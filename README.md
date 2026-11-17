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
            segments.py (paragraphs, paragraph scores, rewrite invariant checks)
server/     serve.py (local web server) and web/index.html (UI)
tests/      unit tests (segments) and model tests (mesmer)
docs/       design notes and plans
artifacts/  downloaded models (not tracked)
```

The authors' reference code (`mesmer_detector.py`) is downloaded with the weights and
imported at runtime; it is not part of this repository.

## Setup

Python 3.12 with torch (CPU), numpy, tokenizers, safetensors and emoji, then:

```
hf download mesmertech/mesmer-ai-detector-4b --local-dir artifacts/mesmer4b/hf \
    --include "*.json" "model.safetensors" "mesmer_detector.py"
```

## Usage

Run from the repository root.

```
python -m server.serve                          # GUI at http://127.0.0.1:8765
python -m unittest discover -s tests -t .       # tests (model tests take about a minute)
```

Mesmer windows long texts itself (whole sentences, up to 1,023 tokens per window,
256 tokens of context). The wrapper runs one window per forward pass and caches each
window's output, so re-scoring after an edit recomputes only windows whose tokens
changed. The GUI ring shows AI involvement (1 - P(human)), coloured by Mesmer's
calibrated verdict, and shades each sentence by its label.

Scores are statistical estimates, not proof of authorship.
