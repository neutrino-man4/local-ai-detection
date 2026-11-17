# local-ai-detection

Local AI-generated-text detection with Mesmer on the CPU, a browser GUI served on
`127.0.0.1` only, and helpers for detector-guided rewriting.

Models (`--model`):

| Name | Hugging Face model | Output |
|---|---|---|
| `mesmer4b` | [`mesmertech/mesmer-ai-detector-4b`](https://huggingface.co/mesmertech/mesmer-ai-detector-4b) (CC BY-NC-SA 4.0) | human / ai / ai_edited, calibrated verdict, per-sentence labels |

## Layout

```
detector/   models.py (registry), mesmer.py (CPU wrapper with per-window cache),
            segments.py (paragraphs, paragraph scores, rewrite invariant checks),
            documents.py (JSON reports used by the MCP tools)
mcp_server/ server.py (MCP stdio server for Claude Code), cli.py (same tools on the command line)
server/     serve.py (local web server) and web/index.html (UI)
tests/      unit tests (segments) and model tests (mesmer)
docs/       design notes and plans
artifacts/  downloaded models (not tracked)
```

The authors' reference code (`mesmer_detector.py`) is downloaded with the weights and
imported at runtime; it is not part of this repository.

## Setup

Python 3.12 with torch (CPU), numpy, tokenizers, safetensors, emoji, huggingface_hub
and mcp, for example in a conda env:

```
conda create -n mesmer-mcp python=3.12 && conda activate mesmer-mcp
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install numpy tokenizers safetensors emoji huggingface_hub mcp
hf download mesmertech/mesmer-ai-detector-4b --local-dir artifacts/mesmer4b/hf \
    --include "*.json" "model.safetensors" "mesmer_detector.py"
```

## Usage

Run from the repository root.

```
python -m server.serve                          # GUI at http://127.0.0.1:8765
python -m mcp_server.cli score draft.md         # tool output from the command line
python -m unittest discover -s tests -t .       # tests (model tests take about a minute)
```

## MCP server for Claude Code

`mcp_server/server.py` exposes three tools over stdio. They take file paths and return
compact JSON:

| Tool | Purpose |
|---|---|
| `score_document` | verdict, AI involvement, probabilities; per-paragraph (and optionally per-sentence) scores |
| `score_candidate` | score a rewrite of one paragraph in place, without modifying the file, including an invariant check |
| `check_invariants` | check that a rewrite preserves numbers, citations, maths, code, URLs, quotations and structure |

Register it once (user scope):

```
claude mcp add mesmer --scope user -- ~/miniconda3/envs/mesmer-mcp/bin/python ~/npu_models/mcp_server/server.py
claude mcp list      # mesmer: ... - Connected
```

Mesmer windows long texts itself (whole sentences, up to 1,023 tokens per window,
256 tokens of context). The wrapper runs one window per forward pass and caches each
window's output, so re-scoring after an edit recomputes only windows whose tokens
changed. The GUI ring shows AI involvement (1 - P(human)), coloured by Mesmer's
calibrated verdict, and shades each sentence by its label.

Scores are statistical estimates, not proof of authorship.
