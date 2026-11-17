"""
Tests for the Mesmer MCP server: tool functions called directly (invariants without
the model; document and candidate reports with the model) and an end-to-end stdio
session against a spawned server process, as Claude Code runs it.
Run from the repository root: python -m unittest discover -s tests -t .

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import gc
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from detector.models import MODELS
from detector.segments import paragraph_scores, paragraph_spans, substitute_paragraph
from mcp_server import server
from tests.test_mesmer import SHORT, _long_document

SPEC = MODELS["mesmer4b"]
SERVER_SCRIPT = Path(server.__file__).resolve()


def _write(directory: str, name: str, text: str) -> str:
    path = Path(directory) / name
    path.write_text(text, encoding="utf-8")
    return str(path)


class InvariantTool(unittest.TestCase):
    """check_invariants needs no model."""

    def test_original_text(self) -> None:
        out = json.loads(server.check_invariants("We saw 13% gains.", original_text="We saw 12% gains."))
        self.assertFalse(out["passed"])
        self.assertIn("number: missing ['12%']", out["errors"])

    def test_paragraph_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "doc.md", "First paragraph about NASA.\n\nSecond one, with 3 items.\n")
            ok = json.loads(server.check_invariants("Second one has 3 items.", path=path, paragraph_id=1))
            self.assertEqual(ok, {"passed": True, "errors": [], "warnings": []})
            with self.assertRaises(ValueError):
                server.check_invariants("x", path=path, paragraph_id=5)
            with self.assertRaises(ValueError):
                server.check_invariants("x", path=path)
            with self.assertRaises(ValueError):
                server.check_invariants("x", path=str(Path(d) / "missing.md"), paragraph_id=0)


@unittest.skipUnless(SPEC.ready, "Mesmer-4B is not downloaded")
class ModelTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.long = _long_document()
        cls.long_path = _write(cls.tmp.name, "long.md", cls.long)
        cls.short_path = _write(cls.tmp.name, "short.md", SHORT)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()
        server._detector = None  # free the model (about 8 GB) before other test modules load theirs
        gc.collect()

    def test_document_report_is_consistent(self) -> None:
        out = json.loads(server.score_document(self.long_path, detail="sentences", max_items=1000))
        self.assertIn(out["verdict"], ("human", "ai", "ai_edited"))
        self.assertEqual(out["paragraphs"], len(paragraph_spans(self.long)))
        self.assertEqual(len(out["paragraph_scores"]), out["paragraphs"])
        self.assertEqual(len(out["sentence_labels"]), out["sentences"])
        self.assertEqual(sum(p["flagged"] for p in out["paragraph_scores"]), out["flagged_sentences"])
        self.assertEqual(sum(p["flagged"] > 0 for p in out["paragraph_scores"]), out["flagged_paragraphs"])
        for p in out["paragraph_scores"]:
            self.assertEqual("worst" in p, p["flagged"] > 0)
            self.assertEqual(p["involvement"] is None, p["sentences"] == 0)
        self.assertEqual(sum(p["sentences"] for p in out["paragraph_scores"]), out["sentences"])
        self.assertAlmostEqual(out["ai_involvement"], round(100 * (1 - out["probs"]["human"]), 1))

    def test_paragraph_without_sentences(self) -> None:
        # Mesmer joins "Dear team," to the next sentence, so paragraph 0 owns no sentence
        out = json.loads(server.score_document(self.short_path))
        first = out["paragraph_scores"][0]
        self.assertEqual((first["sentences"], first["involvement"], first["flagged"]), (0, None, 0))

    def test_summary_and_truncation(self) -> None:
        summary = json.loads(server.score_document(self.long_path, detail="summary"))
        self.assertNotIn("paragraph_scores", summary)
        cut = json.loads(server.score_document(self.long_path, detail="sentences", max_items=3))
        self.assertEqual(len(cut["paragraph_scores"]), 3)
        self.assertEqual(len(cut["sentence_labels"]), 3)
        self.assertTrue(cut["paragraph_scores_truncated"] and cut["sentence_labels_truncated"])

    def test_candidate_matches_direct_scoring(self) -> None:
        pid = len(paragraph_spans(self.long)) - 1
        candidate = "In the end the coffee machine was replaced, and everyone was in a better mood by Friday."
        before_file = Path(self.long_path).read_text(encoding="utf-8")
        out = json.loads(server.score_candidate(self.long_path, pid, candidate))
        self.assertEqual(Path(self.long_path).read_text(encoding="utf-8"), before_file, "the file must not change")

        det = server._detector
        edited = substitute_paragraph(self.long, pid, candidate)
        direct = det.analyze(edited)
        self.assertEqual(out["document"]["after"]["verdict"], direct["verdict"])
        self.assertEqual(out["document"]["after"]["probs"], direct["probs"])
        para = paragraph_scores(edited, direct["sentences"])[pid]
        self.assertEqual(out["paragraph"]["after"]["involvement"], round(100 * para["involvement"], 1))
        self.assertEqual(out["paragraph"]["after"]["flagged"], para["flagged"])
        self.assertTrue(out["candidate_sentences"])
        self.assertIn("passed", out["invariants"])
        self.assertGreaterEqual(out["windows"]["cached"], 1, "windows before the last paragraph should be reused")

    def test_candidate_errors(self) -> None:
        with self.assertRaises(ValueError):
            server.score_candidate(self.short_path, 99, "Text.")
        with self.assertRaises(ValueError):
            server.score_candidate(self.short_path, 0, "Two\n\nparagraphs.")


@unittest.skipUnless(SPEC.ready, "Mesmer-4B is not downloaded")
class StdioProtocol(unittest.TestCase):
    """Spawn the server as Claude Code does and talk to it over stdio."""

    def test_session(self) -> None:
        import anyio
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "short.md", SHORT)

            async def session() -> tuple[set, dict, dict]:
                params = StdioServerParameters(command=sys.executable, args=[str(SERVER_SCRIPT)])
                with open(os.devnull, "w") as errlog:
                    async with stdio_client(params, errlog=errlog) as (read, write):
                        async with ClientSession(read, write) as s:
                            init = await s.initialize()
                            self.assertEqual(init.server_info.name, "mesmer")
                            names = {t.name for t in (await s.list_tools()).tools}
                            inv = await s.call_tool("check_invariants", {"candidate_text": "b", "original_text": "a"})
                            doc = await s.call_tool("score_document", {"path": path, "detail": "summary"})
                            self.assertFalse(inv.is_error or doc.is_error)
                            return names, json.loads(inv.content[0].text), json.loads(doc.content[0].text)

            names, inv, doc = anyio.run(session)
        self.assertEqual(names, {"score_document", "score_candidate", "check_invariants"})
        self.assertTrue(inv["passed"])
        self.assertIn(doc["verdict"], ("human", "ai", "ai_edited"))
        self.assertGreaterEqual(doc["windows"]["computed"], 1)


if __name__ == "__main__":
    unittest.main()
