"""
Paragraph-level helpers for detector-guided rewriting: blank-line paragraph spans,
mapping of Mesmer sentence spans onto paragraphs, per-paragraph scores, paragraph
substitution, and extraction of protected items (mathematics, code, URLs, citations,
quotations, numbers, names, structure) to check that a rewrite preserves content.

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import re
from collections import Counter

_BLANK_LINE = re.compile(r"\n[ \t\r\f\v]*\n")

# Spans removed before numbers and names are extracted, so their contents are not counted twice
_SPAN_PATTERNS: dict[str, re.Pattern] = {
    "code": re.compile(r"```.*?```|`[^`\n]+`", re.S),
    "math": re.compile(
        r"\$\$.+?\$\$|\$[^$\n]+\$|\\\(.+?\\\)|\\\[.+?\\\]|\\begin\{([A-Za-z]+\*?)\}.*?\\end\{\1\}", re.S
    ),
    "url": re.compile(r"https?://[^\s)\]>]*[^\s)\]>.,;:!?]"),  # trailing punctuation is not part of the URL
    "citation": re.compile(
        r"\\cite[a-zA-Z]*\{[^}]*\}|\[\d+(?:\s*[,-]\s*\d+)*\]|\([A-Z][A-Za-z'-]+(?: et al\.)?,? \d{4}[a-z]?\)"
    ),
    "quote": re.compile(r"\"[^\"\n]+\"|\u201c[^\u201d\n]+\u201d"),
}
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*%?")
_LATEX_COMMAND = re.compile(r"\\[A-Za-z]+")
_SENTENCE_BREAK = re.compile(r"(?<=[.!?:;])\s+|\n+")
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+", re.M)
_HEADING = re.compile(r"^\s*#{1,6}\s+|^\s*\\(?:sub)*section\*?\{", re.M)
# Categories whose changes reject a rewrite; name detection is heuristic and only warns
_SOFT_CATEGORIES = {"name"}


def _names(text: str) -> set[str]:
    """Capitalised words other than a sentence's first word, plus acronyms anywhere."""
    names = set()
    for sentence in _SENTENCE_BREAK.split(text):
        words = _WORD.findall(_LIST_ITEM.sub("", sentence))
        for k, w in enumerate(words):
            if len(w) > 1 and (w.isupper() or (k > 0 and w[0].isupper())):
                names.add(w)
    return names


def paragraph_spans(text: str) -> list[tuple[int, int]]:
    """Character spans of blank-line-separated paragraphs, without surrounding whitespace."""
    spans, pos = [], 0
    for m in [*_BLANK_LINE.finditer(text), None]:
        end = m.start() if m else len(text)
        block = text[pos:end]
        if block.strip():
            spans.append((pos + len(block) - len(block.lstrip()), pos + len(block.rstrip())))
        if m:
            pos = m.end()
    return spans


def _visible(text: str, a: int, b: int) -> int:
    return sum(not ch.isspace() for ch in text[a:b])


def assign_sentences(text: str, paragraphs: list[tuple[int, int]], sentences: list[tuple[int, int]]) -> list[int]:
    """Paragraph index of each sentence span: the paragraph holding most of its visible characters.

    Mesmer can join a short opening fragment (for example a salutation) to the next
    sentence across a blank line, so a sentence span may cover two paragraphs.
    """
    owners = []
    for a, b in sentences:
        overlaps = [_visible(text, max(a, pa), min(b, pb)) if min(b, pb) > max(a, pa) else 0 for pa, pb in paragraphs]
        owners.append(max(range(len(paragraphs)), key=lambda i: (overlaps[i], -i)))
    return owners


def paragraph_scores(text: str, sentences: list[dict]) -> list[dict]:
    """Per-paragraph scores from Mesmer sentences (dicts with start, end, text, label, p).

    involvement is the visible-character-weighted mean of 1 - P(human) over the
    paragraph's sentences (0.0 when it owns none, for example a salutation joined to the
    next sentence; check "sentences"); flagged counts sentences whose label is not "human".
    flagged_share is the visible-character fraction of the paragraph's sentences that are
    flagged; unlike the count, it does not change when sentences are merged or split.
    """
    paragraphs = paragraph_spans(text)
    owners = assign_sentences(text, paragraphs, [(s["start"], s["end"]) for s in sentences])
    out = []
    for i, (a, b) in enumerate(paragraphs):
        mine = [s for s, o in zip(sentences, owners) if o == i]
        weights = [_visible(text, s["start"], s["end"]) for s in mine]
        total = sum(weights)
        involvement = sum(w * (1 - s["p"][0]) for w, s in zip(weights, mine)) / total if total else 0.0
        flagged_share = sum(w for w, s in zip(weights, mine) if s["label"] != "human") / total if total else 0.0
        worst = max(mine, key=lambda s: 1 - s["p"][0])["text"][:80] if mine else ""
        out.append({
            "id": i,
            "start": a,
            "end": b,
            "line": text.count("\n", 0, a) + 1,
            "words": len(text[a:b].split()),
            "sentences": len(mine),
            "involvement": involvement,
            "flagged": sum(s["label"] != "human" for s in mine),
            "flagged_share": flagged_share,
            "worst": worst,
        })
    return out


def substitute_paragraph(text: str, paragraph_id: int, new_text: str) -> str:
    """Replace one paragraph; the replacement may not contain blank lines (paragraph count is preserved)."""
    if _BLANK_LINE.search(new_text) or not new_text.strip():
        raise ValueError("Replacement must be one non-empty paragraph without blank lines")
    a, b = paragraph_spans(text)[paragraph_id]
    return text[:a] + new_text.strip() + text[b:]


def protected_items(text: str) -> dict[str, Counter]:
    """Multisets of items a rewrite must preserve, by category."""
    items: dict[str, Counter] = {}
    rest = text
    for name, pattern in _SPAN_PATTERNS.items():
        found = [m.group(0) for m in pattern.finditer(rest)]
        items[name] = Counter(found)
        rest = pattern.sub(" ", rest)
    items["number"] = Counter(_NUMBER.findall(rest))
    items["latex_command"] = Counter(c for c in _LATEX_COMMAND.findall(rest))
    items["name"] = Counter(_names(rest))  # a set: names may be repeated or reordered
    items["structure"] = Counter({
        "paragraphs": len(paragraph_spans(text)),
        "list_items": len(_LIST_ITEM.findall(text)),
        "headings": len(_HEADING.findall(text)),
    })
    return items


def check_invariants(original: str, candidate: str) -> tuple[list[str], list[str]]:
    """Differences in protected items between two texts.

    Returns (errors, warnings). A rewrite passes when errors is empty; warnings come
    from heuristic categories (names) and need judgement rather than rejection.
    """
    a, b = protected_items(original), protected_items(candidate)
    errors, warnings = [], []
    for category in a:
        out = warnings if category in _SOFT_CATEGORIES else errors
        if category == "structure":
            for key in sorted(set(a[category]) | set(b[category])):
                if a[category][key] != b[category][key]:
                    out.append(f"structure: {key} {a[category][key]} -> {b[category][key]}")
            continue
        missing, added = a[category] - b[category], b[category] - a[category]
        if missing:
            out.append(f"{category}: missing {sorted(missing.elements())}")
        if added:
            out.append(f"{category}: added {sorted(added.elements())}")
    return errors, warnings
