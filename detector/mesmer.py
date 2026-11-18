"""
CPU wrapper around the authors' Mesmer reference implementation. The reference code
(mesmer_detector.py, CC BY-NC-SA 4.0) is downloaded with the weights and imported at
runtime; it is not copied into this repository. The wrapper caches the model output
of every window, so re-scoring a document after a local edit recomputes only the
windows whose tokens changed, and converts results into text segments for the UI.

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import hashlib
import importlib.util
from collections import OrderedDict
from types import ModuleType

import numpy as np
import torch

from detector.models import ModelSpec

# Weight of P(ai_edited) in the AI score, as in the verdict rule of policy.json
EDITED_WEIGHT: float = 0.5


def ai_score(probs: dict) -> float:
    """P(ai) + EDITED_WEIGHT * P(ai_edited): the quantity Mesmer's verdict rule compares with t_ai."""
    return probs["ai"] + EDITED_WEIGHT * probs["ai_edited"]


def load_reference(spec: ModelSpec) -> ModuleType:
    """Import the authors' mesmer_detector.py from the model folder."""
    src = importlib.util.spec_from_file_location(f"mesmer_detector_{spec.name}", spec.hf_dir / "mesmer_detector.py")
    module = importlib.util.module_from_spec(src)
    src.loader.exec_module(module)
    return module


class MesmerDetector:
    """Mesmer model on the CPU with a per-window output cache.

    The reference analyze() is used unchanged; only its per-window forward pass is
    wrapped. A window's outputs depend only on its token ids, length and sentence
    boundaries, which form the cache key, so cached and uncached results are identical.
    """

    def __init__(self, spec: ModelSpec, cache_size: int = 1024) -> None:
        self.spec = spec
        self.ref = load_reference(spec)
        self.det = self.ref.Detector(spec.hf_dir, device="cpu")
        # One window per forward pass: batching gains nothing on the CPU, padding a short
        # window to the longest in its batch costs a full window, and the cache stores single windows
        self.det.budget = 1
        self.cache: OrderedDict[str, tuple[torch.Tensor, torch.Tensor]] = OrderedDict()
        self.cache_size = cache_size
        self.use_cache = True
        self.hits = self.misses = 0
        self._forward = self.det._forward_both
        self.det._forward_both = self._cached_forward

    @property
    def flag_threshold(self) -> float:
        """Sentence flagging threshold on 1 - P(human), from the model's policy."""
        return float(self.det.policy["t_unit"])

    def _cached_forward(self, x: torch.Tensor, lens: torch.Tensor, units: list) -> tuple[torch.Tensor, torch.Tensor]:
        """Drop-in replacement for Detector._forward_both that memoises single-window passes."""
        if not self.use_cache or x.shape[0] != 1:
            return self._forward(x, lens, units)
        starts, ends = units[0]
        h = hashlib.sha256()
        for part in (x.cpu().numpy(), lens.cpu().numpy(), np.asarray(starts, np.int64), np.asarray(ends, np.int64)):
            h.update(part.tobytes())
            h.update(b"|")
        key = h.hexdigest()
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hits += 1
            doc, sent = self.cache[key]
            return doc.clone(), sent.clone()
        self.misses += 1
        doc, sent = self._forward(x, lens, units)
        self.cache[key] = (doc.detach().clone(), sent.detach().clone())
        if len(self.cache) > self.cache_size:
            self.cache.popitem(last=False)
        return doc, sent

    def analyze(self, text: str) -> dict:
        """Reference result: verdict, document probabilities and per-sentence labels with char spans."""
        return self.det.analyze(text)

    def score(self, text: str) -> dict:
        """Result for the UI: AI score, calibrated verdict, class probabilities and segments.

        The AI score is 100 * (P(ai) + EDITED_WEIGHT * P(ai_edited)), the quantity Mesmer's
        verdict rule compares with t_ai.

        Gaps between sentence spans become unlabelled segments, so the segment texts joined
        in order reproduce the input exactly.
        """
        r = self.analyze(text)
        segments, pos = [], 0
        for s in r["sentences"]:
            if s["start"] > pos:
                segments.append({"text": text[pos:s["start"]]})
            segments.append({
                "text": s["text"],
                "label": s["label"],
                "probs": dict(zip(self.ref.LABELS, s["p"])),
            })
            pos = s["end"]
        if pos < len(text):
            segments.append({"text": text[pos:]})
        return {
            "ai_score": 100 * ai_score(r["probs"]),
            "verdict": r["verdict"],
            "probs": r["probs"],
            "model": self.spec.hf_id,
            "segments": segments,
        }
