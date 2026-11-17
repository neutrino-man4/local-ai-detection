"""
Local MCP server (stdio) exposing the Mesmer AI-text detector to Claude Code. Tools
take file paths, so long documents never pass through the conversation, and return
compact JSON. The model loads on the first tool call and stays resident; one lock
serialises model use, since tools run in worker threads.
Register: claude mcp add mesmer --scope user -- <mesmer-mcp python> <repo>/mcp_server/server.py

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import json
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repository root, for the detector package

from mcp.server.mcpserver import MCPServer  # noqa: E402

from detector.documents import (  # noqa: E402
    candidate_report,
    document_report,
    invariants_report,
    read_document,
)
from detector.mesmer import MesmerDetector  # noqa: E402
from detector.models import MODELS  # noqa: E402
from detector.segments import paragraph_spans  # noqa: E402

MODEL_NAME: str = "mesmer4b"

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s mesmer-mcp %(levelname)s %(message)s")
log = logging.getLogger("mesmer-mcp")

mcp = MCPServer(
    name="mesmer",
    instructions=(
        "Local AI-text detector (Mesmer 4B, mesmertech/mesmer-ai-detector-4b) running on the CPU. "
        "Pass paths to UTF-8 text files, not the text itself. Paragraphs are blank-line-separated blocks, "
        "numbered from 0. ai_involvement is 1 - P(human) in percent; the verdict uses the model's calibrated "
        "thresholds (human / ai_edited / ai). Scoring costs about 5 s per 1,000 tokens; re-scoring after an "
        "edit reuses unchanged windows, so edits near the end of a document are cheapest. Scores are "
        "statistical estimates, not proof of authorship. Model licence: CC BY-NC-SA 4.0 (non-commercial)."
    ),
)

_lock = threading.Lock()
_detector: MesmerDetector | None = None


def _get_detector() -> MesmerDetector:
    """Load the model on first use; callers must hold _lock."""
    global _detector
    if _detector is None:
        spec = MODELS[MODEL_NAME]
        if not spec.ready:
            raise RuntimeError(f"Model files missing in {spec.hf_dir}")
        t0 = time.perf_counter()
        _detector = MesmerDetector(spec)
        log.info("loaded %s in %.1f s", spec.hf_id, time.perf_counter() - t0)
    return _detector


def _compact(out: dict) -> str:
    """Single-line JSON: tool output lands in Claude's context, so indentation is wasted tokens."""
    return json.dumps(out, ensure_ascii=False)


def _timed(fn, *args) -> dict:
    """Run a report function under the model lock and add elapsed time and cache counts."""
    with _lock:
        det = _get_detector()
        hits, misses, t0 = det.hits, det.misses, time.perf_counter()
        out = fn(det, *args)
        out["elapsed_s"] = round(time.perf_counter() - t0, 2)
        out["windows"] = {"computed": det.misses - misses, "cached": det.hits - hits}
    return out


@mcp.tool()
def score_document(
    path: str,
    detail: Literal["summary", "paragraphs", "sentences"] = "paragraphs",
    max_items: int = 100,
) -> str:
    """Score a text file with Mesmer.

    Returns the document verdict (human / ai_edited / ai), ai_involvement (1 - P(human), %),
    probabilities, and sentence and paragraph flag counts. detail="paragraphs" adds per-paragraph
    scores (id, line, words, involvement %, flagged count, worst flagged sentence);
    detail="sentences" also adds every sentence's label, probabilities [human, ai, ai_edited] and
    paragraph id. Lists are capped at max_items.
    """
    p, text = read_document(path)
    out = _timed(document_report, text, detail, max_items)
    out["path"] = str(p)
    return _compact(out)


@mcp.tool()
def score_candidate(path: str, paragraph_id: int, candidate_text: str) -> str:
    """Score a proposed rewrite of one paragraph in place, without modifying the file.

    The candidate replaces paragraph paragraph_id (0-based, blank-line-separated) and the whole
    document is re-scored, reusing cached windows. Returns paragraph involvement and flagged
    sentences before and after, the document verdict before and after, new_flags_elsewhere
    (sentences in other paragraphs that became flagged), the candidate's sentence labels, and an
    invariant check of the candidate against the original paragraph. The candidate must be a single
    paragraph without blank lines.
    """
    _, text = read_document(path)
    return _compact(_timed(candidate_report, text, paragraph_id, candidate_text))


@mcp.tool()
def check_invariants(
    candidate_text: str,
    path: str | None = None,
    paragraph_id: int | None = None,
    original_text: str | None = None,
) -> str:
    """Check that a rewrite preserves protected content, without running the model.

    Compare candidate_text with either original_text or paragraph paragraph_id of the file at path.
    errors (numbers, citations, mathematics, code, URLs, quotations, LaTeX commands, paragraph /
    list / heading structure) mean the rewrite must be rejected; warnings (names, detected
    heuristically) need judgement.
    """
    if original_text is None:
        if path is None or paragraph_id is None:
            raise ValueError("Give original_text, or path together with paragraph_id")
        _, text = read_document(path)
        spans = paragraph_spans(text)
        if not 0 <= paragraph_id < len(spans):
            raise ValueError(f"paragraph_id must be in 0..{len(spans) - 1}")
        original_text = text[slice(*spans[paragraph_id])]
    return _compact(invariants_report(original_text, candidate_text))


if __name__ == "__main__":
    mcp.run("stdio")
