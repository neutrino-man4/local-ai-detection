# local-ai-detection

Local AI-generated-text detection, running on the AMD Ryzen AI NPU (BF16, ONNX Runtime
VitisAI execution provider) or on the CPU. Includes a browser GUI served on `127.0.0.1`
only. Texts of any length are split into overlapping windows and combined by
token-weighted mean.

Models (`--model`):

| Name | Hugging Face model | Window |
|---|---|---|
| `fakespot` | [`fakespot-ai/roberta-base-ai-text-detection-v1`](https://huggingface.co/fakespot-ai/roberta-base-ai-text-detection-v1) | 512 tokens |
| `vanguard` | [`ShantanuT01/vanguard-ai-text-detector`](https://huggingface.co/ShantanuT01/vanguard-ai-text-detector) | 1024 tokens |

## Layout

```
detector/   shared code: model registry, chunking/weighting, CPU/NPU sessions
scripts/    export.py (model -> static ONNX), compare.py (CPU vs NPU)
server/     serve.py (local web server) and web/index.html (UI)
docs/       design notes
artifacts/  generated: downloads, ONNX model, tokenizer (not tracked)
```

## Usage

Requires the Ryzen AI 1.9 software (XRT + venv). Run all commands from the repository
root, inside the Ryzen AI environment (`ryzenai` shell function).

```
python -m scripts.export --model fakespot     # once: download and export to ONNX
python -m scripts.compare "some text"         # CPU vs NPU scores
python -m server.serve [--cpu]                # GUI at http://127.0.0.1:8765
```

Scores are statistical estimates, not proof of authorship.
