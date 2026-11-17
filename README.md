# local-ai-detection

Local AI-generated-text detection with a browser GUI served on `127.0.0.1` only.
Supports ONNX models on the AMD Ryzen AI NPU (BF16, ONNX Runtime VitisAI execution
provider) or CPU, and Mesmer models on the CPU through the authors' reference code.

Models (`--model`):

| Name | Hugging Face model | Runs on | Output |
|---|---|---|---|
| `mesmer4b` | [`mesmertech/mesmer-ai-detector-4b`](https://huggingface.co/mesmertech/mesmer-ai-detector-4b) (CC BY-NC-SA 4.0) | CPU | human / ai / ai_edited, calibrated verdict, per-sentence labels |

No ONNX models are registered at present; the NPU code path is kept for future ports.

## Layout

```
detector/   shared code: model registry, chunking/weighting, CPU/NPU sessions for ONNX models
scripts/    export.py (model -> static ONNX), compare.py (CPU vs NPU); ONNX models only
server/     serve.py (local web server) and web/index.html (UI)
docs/       design notes
artifacts/  generated: downloads, ONNX models, tokenizers (not tracked)
```

## Setup (Mesmer 4B)

Requires the Ryzen AI 1.9 venv (`ryzenai` shell function) and the `emoji` package.

```
pip install --no-deps emoji
hf download mesmertech/mesmer-ai-detector-4b --local-dir artifacts/mesmer4b/hf \
    --include "*.json" "model.safetensors" "mesmer_detector.py"
```

## Usage

Run from the repository root, inside the Ryzen AI environment.

```
python -m server.serve                        # GUI at http://127.0.0.1:8765
```

Mesmer windows long texts itself (whole sentences, up to 1,023 tokens per window,
256 tokens of context); the server runs one window per batch to avoid padding cost on
the CPU. The GUI ring shows AI involvement (1 - P(human)) with Mesmer's calibrated
verdict, and shades each sentence by its label.

Scores are statistical estimates, not proof of authorship.
