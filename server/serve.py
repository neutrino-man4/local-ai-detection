"""
Local web interface for AI-text detection. Serves a single-page UI and a JSON scoring
endpoint on 127.0.0.1 only. Every ready model can be chosen in the UI; the default
model is loaded at startup and others on first use. ONNX models run on the NPU (CPU
with --cpu); Mesmer models always run on the CPU through the authors' reference code.
One lock serialises all scoring, so only one model runs at a time.
Run from the repository root: python -m server.serve [--model mesmer4b] [--cpu]

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import argparse
import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from transformers import AutoTokenizer

from detector.chunking import aggregate, chunk_text, owned_char_spans
from detector.models import MODELS, ModelSpec
from detector.runtime import make_session, score_chunks

INDEX_HTML: bytes = (Path(__file__).resolve().parent / "web" / "index.html").read_bytes()


class Detector:
    """Holds the tokenizer and model session of one model."""

    def __init__(self, spec: ModelSpec, use_npu: bool) -> None:
        self.spec = spec
        self.tokenizer = AutoTokenizer.from_pretrained(spec.onnx_dir)
        self.session = make_session(spec, npu=use_npu)

    def score(self, text: str) -> dict:
        """Return the document AI percentage and the per-segment text and AI percentage."""
        chunks, weights = chunk_text(text, self.tokenizer, max_tokens=self.spec.max_tokens)
        ai_probs = score_chunks(chunks, self.tokenizer, self.session, self.spec)
        spans = owned_char_spans(text, self.tokenizer, max_tokens=self.spec.max_tokens)
        # Segment text rather than offsets: Python and JavaScript index strings differently
        segments = [{"text": text[s:e], "ai_percent": float(100 * p)} for (s, e), p in zip(spans, ai_probs)]
        return {
            "ai_percent": 100 * aggregate(ai_probs, weights),
            "model": self.spec.hf_id,
            "segments": segments,
        }


class MesmerDetector:
    """Mesmer model run on the CPU through the authors' mesmer_detector.py, downloaded with the weights."""

    def __init__(self, spec: ModelSpec) -> None:
        self.spec = spec
        src = importlib.util.spec_from_file_location("mesmer_detector", spec.hf_dir / "mesmer_detector.py")
        self.module = importlib.util.module_from_spec(src)
        src.loader.exec_module(self.module)
        # One window per micro-batch: batching gains nothing on the CPU, and padding a short
        # window to the longest one in its batch would cost a full window
        self.det = self.module.Detector(spec.hf_dir, device="cpu", tokens_per_batch=spec.seq_len)

    def score(self, text: str) -> dict:
        """Return AI involvement (1 - P(human)), the calibrated verdict, and per-sentence segments.

        Mesmer windows the text itself (whole sentences, up to 1,023 tokens, 256 tokens of
        context). Gaps between its sentence spans become unlabelled segments, so the segment
        texts joined in order reproduce the input exactly.
        """
        r = self.det.analyze(text)
        labels = self.module.LABELS
        segments, pos = [], 0
        for s in r["sentences"]:
            if s["start"] > pos:
                segments.append({"text": text[pos:s["start"]]})
            segments.append({
                "text": s["text"],
                "label": s["label"],
                "probs": dict(zip(labels, s["p"])),
                "ai_percent": 100 * (1 - s["p"][0]),
            })
            pos = s["end"]
        if pos < len(text):
            segments.append({"text": text[pos:]})
        return {
            "ai_percent": 100 * (1 - r["probs"]["human"]),
            "verdict": r["verdict"],
            "probs": r["probs"],
            "model": self.spec.hf_id,
            "segments": segments,
        }


class DetectorPool:
    """Ready models, loaded on first use and kept; one lock guards loading and scoring."""

    def __init__(self, default: str, use_npu: bool) -> None:
        self.available = [name for name, spec in MODELS.items() if spec.ready]
        if default not in self.available:
            raise SystemExit(f"Model '{default}' is not ready; export or download it into {MODELS[default].hf_dir.parent}")
        self.default = default
        self.use_npu = use_npu
        self.detectors: dict[str, Detector | MesmerDetector] = {}
        self.lock = threading.Lock()
        self.score(default, "warm up")  # load the default model before serving

    def score(self, name: str, text: str) -> dict:
        with self.lock:
            if name not in self.detectors:
                spec = MODELS[name]
                self.detectors[name] = MesmerDetector(spec) if spec.backend == "mesmer" else Detector(spec, self.use_npu)
            return self.detectors[name].score(text)


def make_handler(pool: DetectorPool) -> type[BaseHTTPRequestHandler]:
    """Build a request handler class bound to the given detector pool."""

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status: int, payload: dict) -> None:
            self._send(status, json.dumps(payload).encode(), "application/json")

        def do_GET(self) -> None:
            if self.path == "/":
                self._send(200, INDEX_HTML, "text/html; charset=utf-8")
            elif self.path == "/api/models":
                models = [{"name": n, "label": MODELS[n].label or n, "hf_id": MODELS[n].hf_id} for n in pool.available]
                self._send_json(200, {"default": pool.default, "models": models})
            else:
                self._send_json(404, {"error": "Not found"})

        def do_POST(self) -> None:
            if self.path != "/api/score":
                self._send_json(404, {"error": "Not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                text, model = body.get("text", ""), body.get("model", pool.default)
            except (ValueError, AttributeError):
                self._send_json(400, {"error": "Request body must be JSON with a 'text' field"})
                return
            if not isinstance(text, str) or not text.strip():
                self._send_json(400, {"error": "Please paste some text first"})
                return
            if model not in pool.available:
                self._send_json(400, {"error": f"Unknown or unexported model: {model}"})
                return
            try:
                self._send_json(200, pool.score(model, text))
            except Exception as e:  # report model failures to the page instead of dropping the connection
                self._send_json(500, {"error": str(e)})

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(MODELS), default="mesmer4b", help="Model selected at startup")
    parser.add_argument("--cpu", action="store_true", help="Run ONNX models on the CPU instead of the NPU")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    pool = DetectorPool(args.model, use_npu=not args.cpu)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(pool))
    device = "CPU" if args.cpu or MODELS[args.model].backend == "mesmer" else "NPU"
    print(f"Serving {args.model} on http://127.0.0.1:{args.port} ({device}); Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
