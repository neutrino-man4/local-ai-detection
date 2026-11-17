"""
Split texts longer than the model window into overlapping token windows and combine
per-window scores into one length-weighted result. Each token is counted exactly
once: tokens in an overlap are assigned to the window in which they sit further
from the edge, so weights sum to the text length. The same ownership gives
non-overlapping character spans for shading the text.

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import numpy as np
from transformers import PreTrainedTokenizerBase


def _window_bounds(n: int, max_tokens: int, overlap: int) -> tuple[list[int], list[int], list[int]]:
    """Compute window start/end token indices and the midpoint ownership boundaries.

    Window i covers tokens [starts[i], ends[i]) and owns tokens [bounds[i], bounds[i + 1]).
    """
    if not 0 <= overlap < max_tokens:
        raise ValueError("overlap must satisfy 0 <= overlap < max_tokens")
    if n == 0:
        raise ValueError("Text produces no tokens")

    # Window starts; the last window is anchored to the end so no short tail remains
    starts = list(range(0, max(n - max_tokens, 0) + 1, max_tokens - overlap))
    if starts[-1] + max_tokens < n:
        starts.append(n - max_tokens)
    ends = [min(s + max_tokens, n) for s in starts]

    # Split each overlap at its midpoint so every token belongs to exactly one window
    bounds = [0] + [(starts[i + 1] + ends[i]) // 2 for i in range(len(starts) - 1)] + [n]
    return starts, ends, bounds


def chunk_text(
    text: str, tokenizer: PreTrainedTokenizerBase, max_tokens: int, overlap: int = 128
) -> tuple[list[list[int]], np.ndarray]:
    """Split a text into overlapping token windows and compute each window's weight.

    Args:
        text: Input text of any length.
        tokenizer: Tokenizer matching the model.
        max_tokens: Content tokens per window, excluding the two special tokens.
        overlap: Tokens shared by consecutive windows.

    Returns:
        The token ids of each window, and per-window weights equal to the number of
        tokens each window owns. Weights sum to the total token count of the text.
    """
    ids = tokenizer(text, add_special_tokens=False)["input_ids"]
    starts, ends, bounds = _window_bounds(len(ids), max_tokens, overlap)
    return [ids[s:e] for s, e in zip(starts, ends)], np.diff(bounds)


def owned_char_spans(
    text: str, tokenizer: PreTrainedTokenizerBase, max_tokens: int, overlap: int = 128
) -> list[tuple[int, int]]:
    """Map each window's owned tokens to a character span of the original text.

    Spans are contiguous and non-overlapping and together cover the whole text, so
    whitespace between tokens is attached to the window owning the following token.
    The arguments must match those passed to chunk_text.

    Returns:
        One (char_start, char_end) pair per window, in text order.
    """
    offsets = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
    _, _, bounds = _window_bounds(len(offsets), max_tokens, overlap)
    # Each internal boundary is the first character of the first token the next window owns
    cuts = [0] + [offsets[b][0] for b in bounds[1:-1]] + [len(text)]
    return list(zip(cuts[:-1], cuts[1:]))


def aggregate(ai_probs: np.ndarray, weights: np.ndarray) -> float:
    """Combine per-window AI probabilities into one value, weighted by owned token count.

    Args:
        ai_probs: AI probability per window, shape (num_windows,).
        weights: Owned token count per window, as returned by chunk_text.

    Returns:
        Length-weighted mean AI probability.
    """
    w = np.asarray(weights, dtype=np.float64)
    return float((w * ai_probs).sum() / w.sum())
