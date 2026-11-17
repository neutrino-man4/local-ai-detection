"""
Local web interface for AI-text detection with Mesmer models on the CPU. Serves a
single-page UI and a JSON scoring endpoint on 127.0.0.1 only. The default model is
loaded at startup and others on first use; one lock serialises all scoring.
Run from the repository root: python -m server.serve [--model mesmer4b] [--port 8765]

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from detector.mesmer import MesmerDetector
from detector.models import MODELS

INDEX_HTML: bytes = (Path(__file__).resolve().parent / "web" / "index.html").read_bytes()


class DetectorPool:
    """Ready models, loaded on first use and kept; one lock guards loading and scoring."""

    def __init__(self, default: str) -> None:
        self.available = [name for name, spec in MODELS.items() if spec.ready]
        if default not in self.available:
            raise SystemExit(f"Model '{default}' is not downloaded into {MODELS[default].hf_dir}")
        self.default = default
        self.detectors: dict[str, MesmerDetector] = {}
        self.lock = threading.Lock()
        self.score(default, "Warm up the model before serving requests.")

    def score(self, name: str, text: str) -> dict:
        with self.lock:
            if name not in self.detectors:
                self.detectors[name] = MesmerDetector(MODELS[name])
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
                models = [{"name": n, "label": MODELS[n].label, "hf_id": MODELS[n].hf_id} for n in pool.available]
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
                self._send_json(400, {"error": f"Unknown or missing model: {model}"})
                return
            try:
                self._send_json(200, pool.score(model, text))
            except Exception as e:  # report model failures to the page instead of dropping the connection
                self._send_json(500, {"error": str(e)})

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(MODELS), default="mesmer4b", help="Model selected at startup")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    pool = DetectorPool(args.model)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(pool))
    print(f"Serving {args.model} on http://127.0.0.1:{args.port} (CPU); Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
