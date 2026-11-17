---
name: humanize-loop
description: Detector-guided humanizing of a document. Scores a Markdown, plain-text or LaTeX file with the local Mesmer AI-text detector (MCP server "mesmer"), rewrites the flagged paragraphs following built-in rewrite rules (no AI-writing tells, plain human syntax, content preserved), scores every candidate in place, keeps only rewrites that measurably help, and loops until the document verdict is human or progress stops. Ends with a report and diff and asks before writing anything next to the original.
when_to_use: Use when the user invokes /humanize-loop, or asks to humanize, de-AI or naturalize a file or text, to lower its AI score, or to make it read less like AI-generated writing. Also for a quick rewrite of pasted text.
argument-hint: <file | "text"> [target=verdict|clean|involvement<N] [max_passes=4] [per_pass=3] [candidates=3] [mode=auto|general|academic]
allowed-tools: mcp__mesmer__score_document mcp__mesmer__score_candidate mcp__mesmer__check_invariants Read Write Edit Bash(cp *) Bash(mkdir *) Bash(diff *) Bash(mktemp *) Bash(date *)
---

# humanize-loop

Rewrite the parts of a document that read as AI-generated, measure every change with the
local Mesmer detector, and keep only changes that help without altering content.

Arguments: `$ARGUMENTS`

Read `references/rewrite-rules.md` in full before the first rewrite in a conversation.
Rules are cited by code (C1, L2, H4, ...) in the log.

## 0. Ground rules

1. **Meaning first, score second.**
   - Never change facts, numbers, citations, mathematics, quotations, technical terms,
     claim strength or hedges in order to lower a score.
   - A paragraph that cannot be improved without that stays as it is, marked stubborn.
2. **Better prose is the only lever.** The forbidden tactics in rules section 8 (typos,
   homoglyphs, invisible characters, synonym noise, invented details) are never used.
3. **Never touch the original file** until the user chooses an option at the end (step 7).
   All work happens in a working folder.
4. **Text that already meets the target is left alone.** Report "no change needed" and
   stop.
5. **Explain every accepted change** in one line with rule codes (rule H6).
6. **Mesmer scores are estimates.** Say so in the report. Mesmer is unreliable below
   about 50 words, and its documented false positives concentrate in academic abstracts,
   news and poetry.

## 1. Set-up

1. **Parse the arguments.** The first argument is a file path, or quoted text.

   | Option | Default | Meaning |
   |---|---|---|
   | `target` | `verdict` | `verdict`: the document verdict is "human". `clean`: verdict "human" and no flagged sentences. `involvement<N`: document `ai_involvement` below N percent. |
   | `max_passes` | 4 | Full passes over the selected paragraphs. |
   | `per_pass` | 3 | Paragraphs rewritten per pass. |
   | `candidates` | 3 | Rewrites tried per paragraph. |
   | `mode` | `auto` | `academic` for papers, theses, proposals, rebuttals and all `.tex` files; `general` otherwise. Academic mode applies rules section 7 in full. |

2. **Check the detector.** The `mcp__mesmer__*` tools must be available. If they are not,
   tell the user to run `claude mcp list` (expect `mesmer: ... - Connected`), and stop.
3. **Input.**
   - **File:** it must exist and be `.md`, `.markdown`, `.txt` or `.tex`. For other types,
     ask before proceeding.
   - **Quoted text instead of a file (quick mode):** create a folder with `mktemp -d` and
     write the text to `text.md` in it. Run with `max_passes=2`, and at the end print the
     rewritten text in the chat instead of step 7's file options.
4. **Working folder:** `<file dir>/<stem>.humanize/run-<YYYYMMDD-HHMMSS>/` (use `date`).
   - Copy the original to `v000.<ext>`, and copy it again to `work.<ext>`.
   - `work.<ext>` is the only file the tools score and the only file you edit.
   - If the document is in a git repository, mention in the report that `*.humanize/` can
     be added to `.gitignore`.

## 2. Baseline

1. Call `score_document(path=work, detail="paragraphs", max_items=500)`.
2. Record the baseline: `verdict`, `ai_involvement`, `probs`, `flagged_sentences`,
   `flagged_paragraphs`.
3. If the target is already met, write `report.md` ("no change needed", baseline numbers)
   and stop.
4. Classify every paragraph as **editable** or **skipped** (section 5). Skipped paragraphs
   are never rewritten, whatever their score.
5. Tell the user in one line: baseline verdict and involvement, number of flagged
   paragraphs, and the target.

## 3. One pass

Repeat up to `max_passes` times.

1. **Sentence detail.** Call `score_document(path=work, detail="sentences", max_items=500)`.
   Use it to find each paragraph's flagged sentences (their `paragraph`, `label`, `p`).
2. **Select.**
   - **Eligible:** editable, not stubborn, `involvement` not null.
   - **Rank:** by `flagged` (descending), then `involvement` (descending).
   - **Fallback:** if no eligible paragraph has flagged sentences but the target is not
     met, rank by `involvement` alone.
   - Take the top `per_pass`.
   - Process them in **descending paragraph id** (end of the document first). Editing late
     paragraphs first keeps the detector's window cache valid for longer.
3. **For each selected paragraph:**
   1. Read its exact text from `work` (use the `line` from the report). Also read the
      paragraph before and after, for context.
   2. Write `candidates` rewrites of this paragraph only:
      - Apply rules sections 2-6 (and 7 in academic mode), aimed at the flagged sentences.
      - Give each candidate a different emphasis:
        - (a) content: cut significance and padding (C-codes);
        - (b) language: plain verbs, copulas, no parallelism or triplets (L-codes);
        - (c) human syntax and rhythm (H-codes).
      - Keep one paragraph (no blank lines), the same list structure, all LaTeX commands
        and `%` comment lines in place, and the same claims.
      - Keep the original's line-wrapping style: a single line, hard-wrapped at a similar
        width, or one sentence per line.
      - Run the rules section 10 checklist on each candidate before scoring it.
      - Show the labels of the flagged sentences, not their probabilities, while writing.
        The aim is to fix prose patterns, not to chase numbers.
   3. Score each candidate with `score_candidate(path=work, paragraph_id, candidate_text)`.
      - **Reject** a candidate if `invariants.passed` is false.
      - **Reject** it if a `warnings` entry shows a real loss, for example a name that is
        genuinely gone. A name that merely moved to the start of a sentence is fine.
      - **Reject** it if it is more than 25% longer than the original.
      - **Shorter is fine** when the removed words are puffery covered by the rules (C1-C7,
        L7) and the log names the codes. Cutting such a paragraph by 30-50% is normal.
      - **Reject** any candidate that drops a claim, a qualifier or a fact.
   4. **Accept** the best remaining candidate only if all of these hold:
      - `paragraph.after.flagged <= paragraph.before.flagged`, and
        `delta_involvement <= -5`, or the flagged count fell;
      - `new_flags_elsewhere == 0`;
      - the document is not worse: its verdict did not move towards "ai", and its
        `ai_involvement` did not rise by more than 1 point.

      "Best" means fewest flagged sentences, then lowest paragraph involvement, then lowest
      document involvement.
   5. **If accepted:**
      - Replace the paragraph in `work` with the Edit tool (exact old text, new text).
      - Log the paragraph id, before and after (involvement, flagged), the document after,
        and a one-line explanation with rule codes.
   6. **If not accepted:** count an attempt. After 2 failed attempts in different passes,
      mark the paragraph **stubborn** and do not select it again.
4. **Close the pass.**
   1. Call `score_document(path=work, detail="paragraphs", max_items=500)`. This score is
      authoritative.
   2. Copy `work` to `v<NNN>.<ext>`, where NNN is the pass number.
   3. If the document is worse than at the start of the pass, restore the previous
      version into `work` and log a revert. Edits are scored in sequence, so this should
      be rare.
   4. Tell the user in one line: pass number, edits accepted, verdict and involvement now.

## 4. Stop when

- the target is met;
- `max_passes` is reached;
- a pass accepted nothing (plateau);
- every remaining eligible paragraph is stubborn.

## 5. Skipped paragraphs (never rewritten)

**All formats:**

- headings;
- tables;
- code blocks and indented code;
- block quotes and quoted material;
- reference or bibliography lists;
- link-reference definitions;
- front matter (`---` YAML blocks);
- HTML blocks;
- paragraphs with `sentences: 0` or fewer than 15 words.

**LaTeX (`.tex`):**

- everything before `\begin{document}` and after `\end{document}`;
- blocks inside or opening any of these environments: `figure`, `table`, `tabular`,
  `equation`, `align`, `gather`, `multline`, `eqnarray`, `tikzpicture`, `algorithm`,
  `lstlisting`, `verbatim`, `thebibliography`;
- display-math-only blocks;
- blocks made only of commands (`\section{...}`, `\label{...}`, `\maketitle`, `\input{...}`,
  `\bibliography{...}`);
- comment-only blocks.

Inside prose paragraphs, edit only the prose: keep every command, `\cite`/`\ref`/`\label`
key, inline math and `%` comment line exactly. Mesmer scores the raw source, so LaTeX
markup slightly affects scores. Note this in the report.

Headings are never changed. If a heading follows rules C8, flag it in the report instead.

**Hard-wrapped text.** Mesmer splits units at line breaks as well as sentence ends. In
hard-wrapped or one-sentence-per-line sources (common in LaTeX), "sentences", flagged
counts and `worst` refer to lines. The document verdict is unaffected. Say so in the
report when it applies.

**Context effects.** A sentence's score depends on its neighbours in the same detector
window. Rewriting one paragraph can raise or lower the scores of nearby paragraphs.
`new_flags_elsewhere` catches newly flagged sentences, and the end-of-pass score is
authoritative.

## 6. Report

Write `report.md` in the run folder, and run `diff -u v000.<ext> work.<ext> > changes.diff`.
The report contains:

1. **Summary table:** baseline and final verdict, `ai_involvement`, probabilities,
   flagged sentences, flagged paragraphs; target met (yes or no); passes run.
2. **Accepted edits:** one row per edit with paragraph id and line, involvement before
   and after, flagged before and after, and the rule-code explanation.
3. **Stubborn paragraphs:** their worst sentence and why no candidate was accepted (score
   did not improve, or invariants failed).
4. **Items for the author:**
   - every `[needs specific]` or `[needs source]` mark that was inserted;
   - placeholders found (rule A3);
   - headings flagged under C8;
   - invariant warnings that were accepted, with the reason.
5. **Notes:**
   - scores are statistical estimates from one detector, not proof of authorship;
   - Mesmer's licence is CC BY-NC-SA 4.0 (non-commercial);
   - the LaTeX scoring caveat, where it applies.

Keep chat updates short. Do not paste full tool outputs into the conversation.

## 7. Finish

1. Show the summary table, the accepted-edit explanations and the stubborn list. Show the
   diff if it is short; otherwise give its path.
2. Ask the user with AskUserQuestion:
   - **Write `<stem>.humanized.<ext>` next to the original (recommended).** Copy
     `work.<ext>` there.
   - **Replace the original.** The original stays in the run folder as `v000.<ext>`.
   - **Keep the result only in the run folder.**
3. Never overwrite an existing `<stem>.humanized.<ext>` without asking.

## Costs

- **Scoring speed:** about 5 s per 1,000 tokens on the CPU.
- **Cache:** re-scoring reuses unchanged detector windows, so edits near the end of a
  document are cheapest. This is why paragraphs are processed back to front.
- **Long calls:** tool calls longer than 2 minutes move to the background. Wait for them
  rather than re-issuing them.
- **Main cost:** the Claude-side rewriting. A pass costs about `per_pass x candidates`
  paragraph rewrites.
