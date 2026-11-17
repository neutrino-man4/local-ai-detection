"""
Compact JSON-ready reports for detector-guided rewriting: a document report with
per-paragraph (and optionally per-sentence) scores, an in-place report for a
candidate rewrite of one paragraph, and an invariant report. Used by the MCP
server; kept free of MCP code so it can be tested directly.

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

from pathlib import Path

from detector.mesmer import MesmerDetector
from detector.segments import (
    assign_sentences,
    check_invariants,
    paragraph_scores,
    paragraph_spans,
    substitute_paragraph,
)

MAX_CHARS: int = 400_000  # about 100k tokens, roughly 100 windows or 8-10 minutes on the CPU
SNIPPET: int = 160


def _pct(x: float) -> float:
    return round(100 * x, 1)


def _involvement(p: dict) -> float | None:
    """Paragraph involvement in percent, or None when the paragraph owns no sentence."""
    return _pct(p["involvement"]) if p["sentences"] else None


def read_document(path: str) -> tuple[Path, str]:
    """Resolve and read a UTF-8 text file, rejecting missing, empty or oversized files."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.is_file():
        raise ValueError(f"File not found: {p}")
    text = p.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"File is empty: {p}")
    if len(text) > MAX_CHARS:
        raise ValueError(f"File has {len(text)} characters; the limit is {MAX_CHARS}")
    return p, text


def document_report(det: MesmerDetector, text: str, detail: str = "paragraphs", max_items: int = 100) -> dict:
    """Document verdict and scores; detail is "summary", "paragraphs" or "sentences".

    ai_involvement and paragraph involvement are 1 - P(human) in percent; a paragraph that
    owns no sentence (its text was joined to a neighbouring sentence) has involvement None. A paragraph's
    "worst" sentence (first characters) is listed only when the paragraph has flagged
    sentences. Lists are cut at max_items and marked as truncated.
    """
    r = det.analyze(text)
    sentences = r["sentences"]
    paras = paragraph_scores(text, sentences)
    out = {
        "verdict": r["verdict"],
        "ai_involvement": _pct(1 - r["probs"]["human"]),
        "probs": r["probs"],
        "words": r["words"],
        "sentences": len(sentences),
        "flagged_sentences": sum(s["label"] != "human" for s in sentences),
        "flagged_fraction": r["flagged_fraction"],
        "paragraphs": len(paras),
        "flagged_paragraphs": sum(p["flagged"] > 0 for p in paras),
    }
    if detail in ("paragraphs", "sentences"):
        rows = []
        for p in paras[:max_items]:
            row = {"id": p["id"], "line": p["line"], "words": p["words"], "sentences": p["sentences"],
                   "involvement": _involvement(p), "flagged": p["flagged"]}
            if p["flagged"]:
                row["worst"] = p["worst"]
            rows.append(row)
        out["paragraph_scores"] = rows
        if len(paras) > max_items:
            out["paragraph_scores_truncated"] = True
    if detail == "sentences":
        owners = assign_sentences(text, paragraph_spans(text), [(s["start"], s["end"]) for s in sentences])
        out["sentence_labels"] = [
            {"paragraph": o, "label": s["label"], "p": s["p"], "text": s["text"][:SNIPPET]}
            for s, o in list(zip(sentences, owners))[:max_items]
        ]
        if len(sentences) > max_items:
            out["sentence_labels_truncated"] = True
    return out


def candidate_report(det: MesmerDetector, text: str, paragraph_id: int, candidate: str) -> dict:
    """Score a rewrite of one paragraph in place, without changing the source text.

    The candidate is substituted into the document and the document is re-scored, so the
    paragraph is judged in its real windows and context (cached windows are reused).
    new_flags_elsewhere counts sentences in other paragraphs that became flagged.
    """
    n = len(paragraph_spans(text))
    if not 0 <= paragraph_id < n:
        raise ValueError(f"paragraph_id must be in 0..{n - 1}")
    original = text[slice(*paragraph_spans(text)[paragraph_id])]
    edited = substitute_paragraph(text, paragraph_id, candidate)

    before = det.analyze(text)
    after = det.analyze(edited)
    pb = paragraph_scores(text, before["sentences"])
    pa = paragraph_scores(edited, after["sentences"])
    owners = assign_sentences(edited, paragraph_spans(edited), [(s["start"], s["end"]) for s in after["sentences"]])
    errors, warnings = check_invariants(original, candidate)
    inv_b, inv_a = _involvement(pb[paragraph_id]), _involvement(pa[paragraph_id])
    return {
        "paragraph_id": paragraph_id,
        "paragraph": {
            "before": {"involvement": inv_b, "flagged": pb[paragraph_id]["flagged"]},
            "after": {"involvement": inv_a, "flagged": pa[paragraph_id]["flagged"]},
            "delta_involvement": round(inv_a - inv_b, 1) if inv_a is not None and inv_b is not None else None,
        },
        "document": {
            "before": {"verdict": before["verdict"], "ai_involvement": _pct(1 - before["probs"]["human"])},
            "after": {"verdict": after["verdict"], "ai_involvement": _pct(1 - after["probs"]["human"]),
                      "probs": after["probs"]},
        },
        "new_flags_elsewhere": sum(max(0, a["flagged"] - b["flagged"]) for i, (a, b) in enumerate(zip(pa, pb))
                                   if i != paragraph_id),
        "candidate_sentences": [
            {"label": s["label"], "p": s["p"], "text": s["text"][:SNIPPET]}
            for s, o in zip(after["sentences"], owners) if o == paragraph_id
        ],
        "invariants": {"passed": not errors, "errors": errors, "warnings": warnings},
    }


def invariants_report(original: str, candidate: str) -> dict:
    """Protected-item differences: errors reject a rewrite, warnings need judgement."""
    errors, warnings = check_invariants(original, candidate)
    return {"passed": not errors, "errors": errors, "warnings": warnings}
