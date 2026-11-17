# Local Web GUI for the Fakespot AI-Text Detector

Plan for a minimal, local-only browser interface: paste a text of any length, run it on
the Ryzen AI NPU in the background, and show the AI-generated probability as a ring
gauge with a verdict, plus shading of the parts of the text that look most AI-generated.

Date: 2026-11-17

> **Status:** implemented. The files have since moved to the repository layout described
> in `README.md`:
>
> - `detection.py` became `detector/chunking.py` and `detector/runtime.py`.
> - `serve.py` became `server/serve.py`.
> - `addons/` became `artifacts/fakespot/onnx/`.
>
> Paths below refer to the original layout.

## 1. Approach

A Python standard-library HTTP server (`http.server`) plus one self-contained HTML page.

| Option | New packages | Look | Verdict |
|---|---|---|---|
| `http.server` + single HTML page | none | fully custom | **chosen** |
| FastAPI + uvicorn | 2-3 | fully custom | works, adds nothing needed here |
| Gradio / Streamlit | dozens | generic, recognisable | can change pinned versions in the Ryzen AI venv (numpy, huggingface-hub, ...) |

Reasons:

- No new packages, so the pinned Ryzen AI venv stays untouched.
- Fully offline: no CDN scripts and no web fonts.
- Complete control over the look.

## 2. Layout

```
fakespot/
├── export_fakespot.py
├── run_fakespot.py
├── detection.py      extended: character spans for shading (section 3)
├── serve.py          new: local web server
├── web/index.html    new: entire UI (HTML, CSS, JS in one file)
├── addons/
└── models/
```

## 3. Change to `detection.py`

Shading needs to know which characters of the pasted text each window owns. The owned
regions are the same midpoint-split token ranges already used for the length weights.
Each token is assigned to exactly one window, so the shaded segments never overlap and
together cover the whole text.

- Move the window-boundary calculation into a small internal helper, used by both
  functions below.
- Add `owned_char_spans(text, tokenizer, max_tokens=510, overlap=128) -> list[tuple[int, int]]`.
  It tokenizes once with `return_offsets_mapping=True` and converts each window's owned
  token range into a `(char_start, char_end)` span of the original text.
- `chunk_text`, `score_chunks` and `aggregate` keep their current interfaces, so
  `run_fakespot.py` is unaffected.

## 4. Backend: `serve.py` (~90 lines)

1. **Startup:** load the tokenizer from `addons/`, the label map, and the NPU session
   once. The compiled model is reused from `~/.cache/npu_models/fakespot/`, so
   requests run immediately.
2. **Binding:** `127.0.0.1:8765` only, so it cannot be reached from the network.
3. **Endpoints:**
   - `GET /` serves `web/index.html`.
   - `POST /api/score` with body `{"text": "..."}` runs `chunk_text`, then `score_chunks`,
     then `aggregate`, then `owned_char_spans`.
     It returns:

     ```json
     {
       "ai_percent": 83.4,
       "model": "fakespot-ai/roberta-base-ai-text-detection-v1",
       "segments": [{"text": "...", "ai_percent": 91.2}, ...]
     }
     ```

     No timing or token statistics are returned. Segments carry their text rather than
     character offsets, because Python and JavaScript index strings differently (for
     example, emoji count as one character in Python but two in JavaScript). The segment
     texts joined in order reproduce the input exactly.
4. **Concurrency:** a lock around the NPU session, so only one request runs on the NPU
   at a time.
5. **Errors:** empty text gives HTTP 400 with a message. A model failure gives HTTP 500
   with the message, which the page shows.
6. **Fallback:** a `--cpu` flag uses `CPUExecutionProvider` when the NPU is unavailable.

## 5. Frontend: `web/index.html` (~200-250 lines, no external files)

### 5.1 Input

- One centered card with an auto-growing text box and an **Analyze** button.
  Ctrl+Enter also submits.
- While running, the button shows a spinner and the text box is locked.

### 5.2 Score ring

- An SVG ring from 0 to 100 %: a neutral grey track, with an arc whose length equals the
  AI score, starting at 12 o'clock and running clockwise, animated on load.
- The arc colour depends on the score, with a deliberate switch at 50 %:

  | Score | Colour |
  |---|---|
  | 0 % | bright green, `hsl(142, 75%, 42%)` |
  | 0 % to 50 % | saturation falls linearly from 75 % to 20 % (hue 142) |
  | 50 % | switches to faded red, `hsl(0, 20%, 50%)` |
  | 50 % to 100 % | saturation rises linearly from 20 % to 85 % (hue 0) |
  | 100 % | bright red, `hsl(0, 85%, 50%)` |

  Lightness moves linearly between the endpoint values (42 % for green, 50 % for red).
  Exactly 50.0 % uses the faded-red value, so the boundary is unambiguous.
- In the centre of the ring:
  - the percentage, large;
  - the verdict below it, smaller.

### 5.3 Verdict bands

The bands are half-open intervals, so they never overlap. Every score has exactly one
verdict, and 100 % belongs to the last band.

| Score range | Verdict shown in the ring |
|---|---|
| 0 % <= s < 10 % | Human |
| 10 % <= s < 35 % | Human with AI editing |
| 35 % <= s < 70 % | Uncertain: AI with human editing |
| 70 % <= s < 90 % | Mostly AI |
| 90 % <= s <= 100 % | Fully AI |

The displayed percentage is the score rounded down (floor), and the verdict is chosen from
that displayed value. All band edges are whole numbers, so the shown number and the verdict
always agree. For example, 34.9 % displays as "34 %" with "Human with AI editing", never
as "35 %" with the lower band's verdict.

### 5.4 Layout inside the ring

The text must never overlap the ring stroke.

- The text block lives in a centred container whose width is at most about 70 % of the
  ring's inner diameter.
- The verdict wraps onto at most two lines. "Uncertain: AI with human editing" breaks
  after "Uncertain:".
- Font sizes are fixed relative to the ring size, so the layout stays the same on
  narrow screens.

### 5.5 Text shading

- After analysis, the text box is replaced by a read-only view of the same text. Each
  window's owned segment gets a background tint from the same colour scale as the ring,
  at low opacity (about 15-30 %), so the text stays readable.
- Segments of 70 % and above get a slightly stronger tint, so the most AI-like parts stand
  out.
- Hovering a segment shows its own score (for example "Segment: 92 % AI").
- An **Edit** button returns to the editable text box.
- Texts that fit in one window (510 tokens or fewer, roughly 350-400 words) get a single
  segment, so the whole text shares one tint. Shading is only as detailed as the windows,
  which are roughly 350-400 words each.

### 5.6 Footer

- Below the ring, in small grey text: `fakespot-ai/roberta-base-ai-text-detection-v1`.
- No timing, token or window statistics.
- One muted line stating the score is an estimate, not proof.

### 5.7 Style

- System font stack, neutral palette, and automatic light/dark mode via
  `prefers-color-scheme`.
- The ring and tint colours stay the same in both modes. Only the track and the text
  colours change.

## 6. Settled decisions

1. **Which label is AI:** from the model config, `id2label = {0: "Human", 1: "AI"}`,
   so `ai_percent = 100 * probs[1]`.
2. **Verdict bands:** as in section 5.3.
3. **Colour scale:** as in section 5.2.

## 7. Usage (after implementation)

```
ryzenai-gui                # or: ryzenai-gui --cpu
```

Then open `http://127.0.0.1:8765` in a browser.

## 8. Effort

- **New:** `serve.py`, about 90 lines; `web/index.html`, about 200-250 lines.
- **Changed:** `detection.py`, one new function plus a shared helper for the window
  boundaries.
- **Unchanged:** `export_fakespot.py`, `run_fakespot.py`.
