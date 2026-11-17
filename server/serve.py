"""
Local web interface for AI-text detection. Serves a single-page UI and a JSON scoring
endpoint on 127.0.0.1 only. The model session is created once at startup (NPU by
default, CPU with --cpu) and shared by all requests behind a lock.
Run from the repository root: python -m server.serve [--model fakespot] [--cpu]

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import argparse
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
    """Holds the tokenizer and model session and scores texts one at a time."""

    def __init__(self, spec: ModelSpec, use_npu: bool) -> None:
        self.spec = spec
        self.tokenizer = AutoTokenizer.from_pretrained(spec.onnx_dir)
        self.session = make_session(spec, npu=use_npu)
        self.lock = threading.Lock()

    def score(self, text: str) -> dict:
        """Return the document AI percentage and the per-segment text and AI percentage."""
        with self.lock:
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


def make_handler(detector: Detector) -> type[BaseHTTPRequestHandler]:
    """Build a request handler class bound to the given detector."""

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
            else:
                self._send_json(404, {"error": "Not found"})

        def do_POST(self) -> None:
            if self.path != "/api/score":
                self._send_json(404, {"error": "Not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                text = json.loads(self.rfile.read(length)).get("text", "")
            except (ValueError, AttributeError):
                self._send_json(400, {"error": "Request body must be JSON with a 'text' field"})
                return
            if not isinstance(text, str) or not text.strip():
                self._send_json(400, {"error": "Please paste some text first"})
                return
            try:
                self._send_json(200, detector.score(text))
            except Exception as e:  # report model failures to the page instead of dropping the connection
                self._send_json(500, {"error": str(e)})

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(MODELS), default="fakespot")
    parser.add_argument("--cpu", action="store_true", help="Run on the CPU instead of the NPU")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    detector = Detector(MODELS[args.model], use_npu=not args.cpu)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(detector))
    device = "CPU" if args.cpu else "NPU"
    print(f"Serving {args.model} on http://127.0.0.1:{args.port} ({device}); Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
