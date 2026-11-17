"""
Unit tests for detector.segments: paragraph spans, sentence-to-paragraph mapping,
paragraph scores, paragraph substitution and invariant checks. No model needed.
Run from the repository root: python -m unittest discover -s tests -t .

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import unittest

from detector.segments import (
    assign_sentences,
    check_invariants,
    paragraph_scores,
    paragraph_spans,
    substitute_paragraph,
)


class ParagraphSpans(unittest.TestCase):
    def test_blank_lines_crlf_and_whitespace(self) -> None:
        text = "  First para line one.\nline two.\r\n\r\n\n- item a\n- item b \n \nLast \U0001F600 para.  \n"
        got = [text[a:b] for a, b in paragraph_spans(text)]
        self.assertEqual(got, ["First para line one.\nline two.", "- item a\n- item b", "Last \U0001F600 para."])

    def test_empty_and_single(self) -> None:
        self.assertEqual(paragraph_spans(""), [])
        self.assertEqual(paragraph_spans(" \n\n "), [])
        self.assertEqual(paragraph_spans("One."), [(0, 4)])


class SentenceMapping(unittest.TestCase):
    def test_sentence_crossing_blank_line_goes_to_larger_part(self) -> None:
        # Mesmer joins a short opening fragment to the next sentence across a blank line
        text = "Dear team,\n\nThanks for the update today. I read it."
        paras = paragraph_spans(text)
        sentences = [(0, text.index("today.") + 6), (text.index("I read"), len(text))]
        self.assertEqual(assign_sentences(text, paras, sentences), [1, 1])

    def test_each_sentence_in_its_paragraph(self) -> None:
        text = "Alpha one. Alpha two.\n\nBeta one."
        paras = paragraph_spans(text)
        sentences = [(0, 10), (11, 21), (23, 32)]
        self.assertEqual(assign_sentences(text, paras, sentences), [0, 0, 1])


class ParagraphScores(unittest.TestCase):
    def test_weighted_involvement_and_flags(self) -> None:
        text = "Aaaa. Bbbbbbbbbb.\n\nCcc."
        sentences = [
            {"start": 0, "end": 5, "text": "Aaaa.", "label": "human", "p": [0.9, 0.1, 0.0]},
            {"start": 6, "end": 17, "text": "Bbbbbbbbbb.", "label": "ai", "p": [0.0, 1.0, 0.0]},
            {"start": 19, "end": 23, "text": "Ccc.", "label": "human", "p": [1.0, 0.0, 0.0]},
        ]
        scores = paragraph_scores(text, sentences)
        self.assertEqual([s["id"] for s in scores], [0, 1])
        # visible characters: 5 and 11, so involvement = (5 * 0.1 + 11 * 1.0) / 16
        self.assertAlmostEqual(scores[0]["involvement"], (5 * 0.1 + 11 * 1.0) / 16)
        self.assertEqual(scores[0]["flagged"], 1)
        self.assertEqual([s["sentences"] for s in scores], [2, 1])
        self.assertEqual(scores[0]["worst"], "Bbbbbbbbbb.")
        self.assertEqual((scores[1]["involvement"], scores[1]["flagged"], scores[1]["line"]), (0.0, 0, 3))


class Substitution(unittest.TestCase):
    def test_replaces_only_target(self) -> None:
        text = "One.\n\n  Two old.  \n\nThree."
        out = substitute_paragraph(text, 1, "Two new.")
        self.assertEqual(out, "One.\n\n  Two new.  \n\nThree.")
        self.assertEqual(len(paragraph_spans(out)), 3)

    def test_rejects_blank_lines_and_empty(self) -> None:
        with self.assertRaises(ValueError):
            substitute_paragraph("A.\n\nB.", 0, "X.\n\nY.")
        with self.assertRaises(ValueError):
            substitute_paragraph("A.\n\nB.", 0, "   ")


class Invariants(unittest.TestCase):
    BASE = ("We measured 12.5% gains on 3 GPUs (Smith, 2024) and in [4], see https://example.org/x. "
            "The energy is $E = mc^2$ and `run.py` prints \"done\". NASA and Geneva agreed \\cite{abc}.")

    def assert_errors(self, candidate: str, category: str) -> None:
        errors, _ = check_invariants(self.BASE, candidate)
        self.assertTrue(any(e.startswith(category) for e in errors), errors)

    def test_style_rewrite_passes(self) -> None:
        candidate = ("Gains reached 12.5% on 3 GPUs (Smith, 2024), also in [4]; details at https://example.org/x. "
                     "With $E = mc^2$, the script `run.py` prints \"done\". Then NASA and Geneva agreed \\cite{abc}.")
        self.assertEqual(check_invariants(self.BASE, candidate), ([], []))

    def test_url_excludes_sentence_punctuation(self) -> None:
        # The full stop after a URL ends the sentence, so the next word is not taken as a name
        _, warnings = check_invariants("See https://example.org/x. The end.", "See https://example.org/x. That is all.")
        self.assertEqual(warnings, [])

    def test_changed_number(self) -> None:
        self.assert_errors(self.BASE.replace("12.5%", "13%"), "number")

    def test_removed_citation(self) -> None:
        self.assert_errors(self.BASE.replace(" (Smith, 2024)", ""), "citation")
        self.assert_errors(self.BASE.replace("\\cite{abc}", ""), "citation")

    def test_changed_math_code_url_quote(self) -> None:
        self.assert_errors(self.BASE.replace("$E = mc^2$", "$E=mc^2$"), "math")
        self.assert_errors(self.BASE.replace("`run.py`", "run.py"), "code")
        self.assert_errors(self.BASE.replace("https://example.org/x", "https://example.org/y"), "url")
        self.assert_errors(self.BASE.replace("\"done\"", "\"finished\""), "quote")

    def test_structure(self) -> None:
        errors, _ = check_invariants("- a one\n- b two\n\nPara.", "- a one, b two\n\nPara.")
        self.assertIn("structure: list_items 2 -> 1", errors)
        errors, _ = check_invariants("A.\n\nB.", "A. B.")
        self.assertIn("structure: paragraphs 2 -> 1", errors)

    def test_names_only_warn(self) -> None:
        errors, warnings = check_invariants(self.BASE, self.BASE.replace("NASA and Geneva", "the agency and the city"))
        self.assertEqual(errors, [])
        self.assertTrue(any(w.startswith("name: missing") for w in warnings), warnings)
        # Moving a name to a sentence start hides it from the heuristic: a warning, never an error
        errors, warnings = check_invariants(self.BASE, self.BASE.replace("NASA and Geneva", "Geneva and NASA"))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, ["name: missing ['Geneva']"])


if __name__ == "__main__":
    unittest.main()
