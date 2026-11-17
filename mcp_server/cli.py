"""
Command-line access to the Mesmer MCP tools without Claude Code: calls the same tool
functions in-process and prints their JSON output, for manual checks and debugging.
Run from the repository root with the mesmer-mcp environment, for example:
  python -m mcp_server.cli score draft.md --detail paragraphs
  python -m mcp_server.cli candidate draft.md 3 "Rewritten paragraph text."
  python -m mcp_server.cli invariants "New text." --path draft.md --paragraph 3

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import argparse
import json

from mcp_server import server


def main() -> None:
    parser = argparse.ArgumentParser(description="Call the Mesmer MCP tools from the command line.")
    sub = parser.add_subparsers(dest="command", required=True)

    score = sub.add_parser("score", help="score_document")
    score.add_argument("path")
    score.add_argument("--detail", choices=["summary", "paragraphs", "sentences"], default="paragraphs")
    score.add_argument("--max-items", type=int, default=100)

    cand = sub.add_parser("candidate", help="score_candidate")
    cand.add_argument("path")
    cand.add_argument("paragraph_id", type=int)
    cand.add_argument("candidate_text")

    inv = sub.add_parser("invariants", help="check_invariants")
    inv.add_argument("candidate_text")
    inv.add_argument("--original")
    inv.add_argument("--path")
    inv.add_argument("--paragraph", type=int)

    args = parser.parse_args()
    if args.command == "score":
        out = server.score_document(args.path, args.detail, args.max_items)
    elif args.command == "candidate":
        out = server.score_candidate(args.path, args.paragraph_id, args.candidate_text)
    else:
        out = server.check_invariants(args.candidate_text, args.path, args.paragraph, args.original)
    print(json.dumps(json.loads(out), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
