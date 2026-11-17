"""
Integration tests for detector.mesmer with the real Mesmer-4B weights on the CPU:
cached scoring equals the uncached reference path, a local edit reuses the cached
windows before it, and UI segments and paragraph scores cover the text exactly.
Skipped when the model is not downloaded. Takes a few minutes on the CPU.
Run from the repository root: python -m unittest discover -s tests -t .

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import unittest

from detector.models import MODELS
from detector.segments import paragraph_scores, paragraph_spans, substitute_paragraph

SPEC = MODELS["mesmer4b"]

SHORT = ("Dear team,\n\nThanks for the update \U0001F600. I read the draft last night.\n\n"
         "- First, the budget section needs numbers.\n- Second, the timeline is optimistic.\n\n"
         "Furthermore, it is essential to recognize that effective communication fosters collaboration.   \n")

_TOPICS = ["the budget", "the hiring plan", "the lab move", "the software release", "the field trip",
           "the grant report", "the safety review", "the new detector", "the summer school"]


def _long_document(paragraphs: int = 18) -> str:
    """A varied multi-window document (18 paragraphs, 2 windows)."""
    out = []
    for i in range(paragraphs):
        t = _TOPICS[i % len(_TOPICS)]
        out.append(
            f"On day {i + 1} we discussed {t} again. Maria said the numbers for {t} looked off by about {i + 3} percent, "
            f"and Tom wanted to wait until the next meeting. In the end we agreed to check {t} with the group in "
            f"room {100 + i} and to send a short note to everyone by Friday. Nobody was thrilled, but it was fair. "
            f"The coffee machine broke again, which did not help anyone's mood during the discussion of {t}."
        )
    return "\n\n".join(out)


@unittest.skipUnless(SPEC.ready, "Mesmer-4B is not downloaded")
class MesmerCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from detector.mesmer import MesmerDetector

        cls.det = MesmerDetector(SPEC)
        cls.long = _long_document()

    def _reference(self, text: str) -> dict:
        """Result through the unwrapped forward pass."""
        self.det.use_cache = False
        try:
            return self.det.analyze(text)
        finally:
            self.det.use_cache = True

    def test_cached_equals_reference(self) -> None:
        for text in (SHORT, self.long):
            ref = self._reference(text)
            self.det.cache.clear()
            misses0, hits0 = self.det.misses, self.det.hits
            cold = self.det.analyze(text)
            windows = self.det.misses - misses0
            warm = self.det.analyze(text)
            self.assertEqual(cold, ref)
            self.assertEqual(warm, ref)
            self.assertGreaterEqual(windows, 1)
            self.assertEqual(self.det.hits - hits0, windows)  # the warm run is served entirely from the cache
        self.assertGreaterEqual(windows, 2, "the long document should span several windows")

    def test_edit_reuses_earlier_windows(self) -> None:
        self.det.analyze(self.long)  # make sure every window of the original is cached
        last = len(paragraph_spans(self.long)) - 1
        edited = substitute_paragraph(self.long, last, "In the end the coffee machine was replaced, and the mood improved a lot.")
        hits0, misses0 = self.det.hits, self.det.misses
        cached = self.det.analyze(edited)
        self.assertGreaterEqual(self.det.hits - hits0, 1, "windows before the edit should come from the cache")
        self.assertGreaterEqual(self.det.misses - misses0, 1, "the edited window must be recomputed")
        self.assertEqual(cached, self._reference(edited))

    def test_segments_and_paragraphs_cover_text(self) -> None:
        for text in (SHORT, self.long):
            result = self.det.score(text)
            self.assertEqual("".join(s["text"] for s in result["segments"]), text)
            self.assertIn(result["verdict"], ("human", "ai", "ai_edited"))
            sentences = self.det.analyze(text)["sentences"]
            scores = paragraph_scores(text, sentences)
            self.assertEqual(len(scores), len(paragraph_spans(text)))
            self.assertEqual(sum(s["flagged"] for s in scores), sum(s["label"] != "human" for s in sentences))


if __name__ == "__main__":
    unittest.main()
