# Humanizer Loop: Detector-Guided Rewriting with Claude Code

Plan for a pipeline in which Claude Code iteratively rewrites the parts of a document
that the Mesmer detector flags. The rewriting follows the `humanize-text` skill (or
`academic-humanizer` for papers), and every change is measured through a local
Mesmer MCP server. The loop continues until the document meets a target or stops
improving.

Date: 2026-11-17
Status: phase 1 implemented (`detector/mesmer.py`, `detector/segments.py`, tests). Phases 2-5 not started.

## 1. Goal and non-goals

**Goal.** Make a draft read as natural human writing, measured by Mesmer. Meaning,
facts, citations, numbers and mathematics must stay intact. Every edit is logged and
reviewable.

**Non-goals.**

- Adversarial evasion. Typos, homoglyphs, invisible characters, odd spacing and
  synonym noise are forbidden. They degrade the text, Mesmer normalises many of them
  (homoglyph and emoji handling in its preprocessing), and MELD-eval shows strong
  detectors are robust to such attacks. The only lever is genuinely better prose, as
  defined by the humanizer skills.
- Changing content. The loop edits style, not claims.
- Disclosure. Rewriting does not change any obligation to disclose AI assistance
  (journals, university rules). The pipeline is for improving one's own drafts.

## 2. Facts that shape the design

| Fact | Source | Consequence |
|---|---|---|
| Rewriting is done by Claude itself. A skill is a set of instructions loaded into Claude's context, not an external program. | Skill mechanism | The pipeline is an agentic loop run by Claude Code. Claude orchestrates and the MCP server measures. |
| Mesmer scores whole-sentence windows of at most 1,023 tokens. Each window after the first re-reads up to 256 tokens of preceding sentences as context. Document probabilities are the windows' average, weighted by sentences owned. | `mesmer_detector.py` `analyze()`, lines 607-668 | A local edit changes the window it falls in, and can shift every later window boundary. |
| Sentence labels come from a bidirectional 2-layer transformer over all sentences of a window, plus the window's document state. | `SegHead`, lines 477-496; `_forward_both`, lines 579+ | A sentence's label depends on its neighbours before and after, within the same window. Scoring a paragraph in isolation is not equivalent to scoring it in place. |
| Sentence flagged when 1 - p_human >= 0.8696. Document "ai" if p_ai >= p_ai_edited and p_ai + 0.5 p_ai_edited >= 0.6084. Otherwise "ai_edited" if 1 - p_human >= 0.907. Otherwise "human". | `policy.json` | Targets should use these calibrated rules, not raw probabilities. |
| Results are unreliable below about 50 words. | Model card | Never score or rewrite tiny segments on their own. Paragraphs are the unit. |
| CPU cost: about 5.1 s per full 1,024-token window, 6.6 s for 1,040 tokens with one window per batch. Shorter windows cost proportionally less. | Measured on this machine | Re-scoring the whole document after every candidate is too slow for long texts. Caching per window is needed (section 4.2). |
| Mesmer weights and code are CC BY-NC-SA 4.0. | Model card | Non-commercial use. Any modified copy of `mesmer_detector.py` code inherits the licence, so keep wrappers separate (section 4.4). |

## 3. Architecture

```
            Claude Code session
  +-------------------------------------------+
  |  /humanize-loop skill (orchestration)     |
  |    - loads humanize-text / academic-      |
  |      humanizer guidance                   |
  |    - edits the working copy (Edit tool)   |
  +-----------+-------------------------------+
              | MCP (stdio, local only)
  +-----------v-------------------------------+
  |  mesmer MCP server (conda env "mesmer")   |
  |    score_document   score_candidate       |
  |    check_invariants                       |
  |    window cache (keyed by token ids)      |
  +-----------+-------------------------------+
              |
     detector/mesmer.py (shared with GUI)
     -> authors' mesmer_detector.py (CPU, bf16)
```

**File-based loop.** Claude works on a copy of the document on disk and passes
**paths**, not text, to the tools. Long documents never travel through the context
repeatedly, and every version is kept.

```
<doc>.humanize/
  v000.md            original
  v001.md ...        one file per accepted pass
  log.jsonl          every score, candidate, decision
  report.md          final summary and diff
```

The original file is never overwritten automatically.

## 4. MCP server design

### 4.1 Tools

| Tool | Input | Output (compact JSON) | Cost |
|---|---|---|---|
| `score_document` | `path`, `detail` = `summary` / `paragraphs` / `sentences` | verdict, ai_involvement, probs, flagged_fraction, words; per paragraph: id, line range, words, involvement, flagged sentence count, worst sentence (first 80 characters) | one pass over changed windows (cache) |
| `score_candidate` | `path`, `paragraph_id`, `candidate_text` | the paragraph's involvement and sentence labels **in place**, plus the projected document verdict, without modifying the file | only windows touched by the substitution |
| `check_invariants` | `original_text`, `candidate_text` | errors (reject) and warnings (judge) listing differences in protected items (section 6) | milliseconds, pure Python |

Paragraphs are blank-line-separated blocks of the document. A paragraph's score is
the character-weighted mean of 1 - p_human over its sentences. Paragraph ids are
indices, kept stable by the invariant that rewrites never merge or split paragraphs.

### 4.2 Window cache (the key efficiency measure)

As implemented, the cache works differently from the original plan, which was to
re-implement the window construction:

- The authors' `analyze()` is used unchanged, with one window per forward pass
  (`budget = 1`).
- Only their per-window forward pass (`_forward_both`) is wrapped, and its outputs
  (document logits and sentence logits) are cached. The key is a hash of the window's
  token ids, length and sentence boundaries, which are the forward pass's only
  inputs.
- Cached results are therefore identical to uncached ones by construction (tested),
  and none of the authors' code is copied.

The behaviour after an edit is as follows.
- After a local edit, the windows before it are byte-identical and come from the
  cache. Only the edited window, and any later windows whose boundaries shift, are
  recomputed.
- `score_candidate` substitutes the candidate into the in-memory text and recomputes
  the windows; untouched windows are cache hits. Because the window is rebuilt
  exactly as Mesmer would build it, the candidate is scored in its true context. That
  includes the bidirectional sentence head, so the result equals a full re-score
  (verified by a test, section 9).
- **Expected cost per candidate:** 1-2 windows, about 1-6 s on this CPU, instead of
  scoring the whole document, but only for edits in the last window.
- **Measured** on a 2-window document: cold scoring 11.5 s, unchanged re-score
  0.01 s, edit in the last paragraph 5.2 s (1 window recomputed, 1 cached).
  Editing the first paragraph took 11.3 s: Mesmer packs whole sentences into windows
  from the start, so a token-count change shifts every later window boundary and all
  later windows are recomputed. For long documents, `score_candidate` costs about as
  much as scoring from the edited paragraph to the end. Phase 2 should process
  paragraphs back to front where possible.

### 4.3 Environment and registration

- **Dedicated conda env** `mesmer`: Python 3.12, CPU torch, numpy, tokenizers,
  safetensors, emoji, mcp. Keep it out of the Ryzen AI venv, whose pins the `mcp`
  dependencies could disturb.
- **Registration:**
  `claude mcp add mesmer --scope user -- ~/miniconda3/envs/mesmer/bin/python ~/npu_models/mcp_server/server.py`
- **Timeouts:** long documents need a raised tool timeout (`MCP_TOOL_TIMEOUT`, in
  milliseconds). The variable name is assumed from memory and must be verified
  against the current Claude Code documentation.
- **Logs:** the model loads on the first tool call and stays resident. Log to stderr
  only, because stdout carries the MCP protocol.

### 4.4 Code layout and licence

- `detector/mesmer.py`: `MesmerDetector` moved out of `server/serve.py` (GUI and MCP
  share it), plus the per-window forward-pass cache.
- `detector/segments.py`: paragraph splitting, sentence-to-paragraph mapping,
  invariant extraction.
- `mcp_server/server.py`: FastMCP tool definitions only.
- The wrapper calls the authors' module at runtime (`Detector`, `split_units`,
  `normalize_units`, the forward pass) and does not copy its code into this
  repository. If any of their code has to be modified and copied, that file must
  carry CC BY-NC-SA 4.0 and the attribution.

## 5. The loop (skill `/humanize-loop`)

A project-level skill (`.claude/skills/humanize-loop/SKILL.md`) encodes the procedure,
so it is repeatable and does not depend on re-explaining it each session.

### 5.1 Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `target` | `verdict` | `verdict`: document verdict is "human". `clean`: also no flagged sentences. `involvement<X`: document 1 - p_human below X. |
| `style` | auto | `academic-humanizer` for papers and proposals, `humanize-text` otherwise. |
| `max_passes` | 4 | Full passes over the flagged paragraphs. |
| `per_pass` | 3 | Paragraphs rewritten per pass, worst first. |
| `candidates` | 3 | Rewrites tried per paragraph. |
| `max_attempts` | 2 | Passes in which one paragraph may be retried before it is marked "stubborn". |

### 5.2 Procedure

0. **Setup.**
   - Copy the document to `<doc>.humanize/v000.md`.
   - Call `score_document` with `detail=paragraphs` and log the baseline.
   - If the target is already met, stop and report "no change needed". Text that is
     already human is never touched.
1. **Select.**
   - Rank paragraphs by flagged sentence characters times paragraph involvement.
   - Merge paragraphs under about 60 words with a neighbour for scoring purposes,
     because of Mesmer's unreliability below 50 words. Rewrites still target the
     flagged paragraph only.
   - Take the top `per_pass` that are not stubborn.
2. **Generate.**
   - For each selected paragraph, write `candidates` rewrites following the chosen
     skill. Vary the emphasis per candidate, for example sentence rhythm and
     structure, vocabulary and stock phrases, voice and hedging.
   - Show Claude the flagged sentences and their labels, not the probabilities, so it
     fixes prose patterns instead of chasing numbers.
3. **Gate.**
   - Run `check_invariants` on every candidate and discard failures.
   - Discard candidates that change the paragraph's word count by more than ±25%.
4. **Score.**
   - `score_candidate` for each surviving candidate.
   - Accept the best one if it lowers the paragraph's involvement by at least
     5 points and adds no newly flagged sentence elsewhere in the window.
   - Otherwise keep the original and count an attempt.
5. **Apply.**
   - Write accepted rewrites to `v{n}.md` with the Edit tool.
   - Call `score_document`. This is the authoritative score, mostly cache hits.
   - If the document score got worse than the previous pass, for example because of
     interactions between several edits in one window, revert the pass's edits one
     at a time, worst first, until it no longer does.
6. **Stop** when:
   - the target is met;
   - `max_passes` is reached;
   - a full pass accepts nothing (plateau);
   - all remaining flagged paragraphs are stubborn.
7. **Report** (`report.md`):
   - baseline vs final verdict, involvement and flagged fraction;
   - a per-paragraph table;
   - the unified diff;
   - stubborn paragraphs, left for the user;
   - invariant results;
   - the optional hold-out detector result (section 7).

   Ask the user before copying the final version over the original.

### 5.3 Parallel variant for long documents

Rewriting, not scoring, dominates wall time: a candidate takes Claude several seconds
to write, while scoring with the cache takes about 1-6 s.

- **Sequential loop:** for documents with more than about 8 flagged paragraphs this
  gets slow, so a pass can instead fan out one subagent per selected paragraph.
- **Subagent job:** each one receives the paragraph, about 2 paragraphs of context on
  each side, the flagged sentences and the skill name, and returns its candidates.
- **Main session:** keeps scoring and acceptance, because the MCP server runs one
  model at a time behind a lock anyway.
- **To verify:** whether subagents inherit access to the MCP tools. They do not need
  it in this design.

## 6. Meaning preservation

Deterministic checks in `check_invariants`. A candidate must preserve every protected
item, as a multiset where applicable:

| Protected item | Detection |
|---|---|
| Numbers, units, percentages, dates | regex over digits and number words adjacent to units |
| Citations | `\cite{...}`, `[12]`, `(Author, 2024)`, `et al.` |
| Mathematics | `$...$`, `\(...\)`, `\[...\]`, LaTeX environments, unchanged byte for byte |
| Code and URLs | backtick spans, fenced blocks, `http(s)://` |
| Quotations | text inside quotation marks, unchanged |
| Proper nouns and acronyms | capitalised words other than a sentence's first word, ALL-CAPS words; compared as a set. **Warning only**: moving a name to a sentence start hides it from the heuristic, so a difference needs judgement rather than rejection |
| Structure | paragraph count, list items, headings, LaTeX commands outside prose |

On top of the deterministic gate:

- **Claude self-review:** Claude reviews each accepted diff against the instruction
  "same claims, same hedging strength, no added or removed facts".
- **Human review:** the user approves before the original is replaced.

Semantic similarity scoring with an embedding model is optional. It is not planned,
because it would add another dependency, and the deterministic and review gates catch
the failure modes that matter for technical writing.

## 7. Overfitting to one detector (Goodhart)

Optimising against Mesmer alone can produce text tuned to Mesmer's blind spots that
other detectors still flag.

- **Hold-out check (optional):** after the loop, score the result with a detector not
  used in the loop. For example, re-add Vanguard or Fakespot as CPU ONNX models;
  their exports are deleted but can be regenerated with `scripts/export.py`. Report
  both scores and never feed the hold-out score back into the loop.
- **Bounded edits:** the ±25% length gate and the invariants limit how far the text
  can drift.
- **Skill-defined edits only:** the skills target documented AI-writing tells (stock
  vocabulary, inflated significance, rule-of-three, em dashes, uniform rhythm). Those
  are real quality improvements, not detector artefacts.
- **Expectation:** some paragraphs will stay stubborn. The skill should report them
  rather than escalate rewriting strength without bound.

## 8. Cost estimates (this CPU, estimates)

| Document | Tokens | Windows | Baseline score | Per candidate | Pass (3 paragraphs × 3 candidates) |
|---|---|---|---|---|---|
| 800 words | ~1,100 | 2 | ~7 s | ~1-3 s | ~10-30 s scoring, plus Claude writing |
| 3,000 words | ~4,000 | 4-5 | ~22-28 s | ~2-6 s | ~20-55 s scoring, plus Claude writing |

Claude-side writing time and token use dominate. Each candidate is a paragraph, so a
pass costs roughly 9 paragraph generations plus the tool outputs, which section 4.1
keeps compact. A GPU would cut scoring to well under a second per window, but is not
needed for interactive use.

## 9. Test plan

**Server and wrapper (CPU, automated):**

1. **Parity:** cached-window scoring on a fresh cache equals `Detector.analyze()` for
   a set of documents (probabilities to 1e-6, identical verdicts and labels).
2. **Cache consistency:** after a random paragraph substitution, the cached
   re-score equals a from-scratch `analyze()` of the modified text.
3. **Candidate equivalence:** `score_candidate(path, p, c)` equals the paragraph's
   sentences in `analyze()` of the document with `c` substituted.
4. **Paragraph mapping:** sentence spans map to exactly one paragraph; paragraph texts
   rebuild the document exactly (emoji, CRLF, trailing whitespace, lists).
5. **Invariants:** fixture pairs for every protected class, covering pass, fail, and
   reordering that is allowed.
6. **MCP protocol:** an MCP client test lists the tools, calls each with a fixture,
   and checks that stdout contains only protocol messages.

**Loop (skill, semi-automated):**

7. **No-op on human text:** a known human document exits at step 0 with no edits.
8. **Dry run:** a fixture with 3 flagged paragraphs, `max_passes=1`. Check the log
   structure, versioned files, report and that the original is untouched.
9. **Revert logic:** a constructed case where two edits in the same window raise the
   score together. Check that the step-5 revert happens.

**Effectiveness study (manual, after implementation):**

10. **AI-generated set:** 20 texts of 300-1,500 words from current models. Measure
    verdict flip rate, passes needed, stubborn fraction, invariant failures, and the
    hold-out detector score before and after.
11. **Human set:** 20 texts. Expect no edits; any edit is a defect.
12. **Blind meaning check:** the user rates a sample of original/final pairs for
    preserved meaning.

## 10. Implementation phases

1. **Shared code:** `detector/mesmer.py` (move `MesmerDetector`), lazy ONNX imports in
   `server/serve.py`, and `detector/segments.py`. Tests 1-5.
2. **MCP server:** `mcp_server/server.py`, conda env `mesmer`, registration, timeout
   setting. Test 6. Manual check with `/mcp` in Claude Code.
3. **Skill:** `.claude/skills/humanize-loop/SKILL.md` with the procedure in section 5.
   Tests 7-9.
4. **Optional:** the parallel variant (section 5.3) and the hold-out detector
   (section 7).
5. **Study:** tests 10-12, then tune `per_pass`, `candidates` and the acceptance margin.

## 11. Open questions

- Exact Claude Code tool-timeout variable, and its maximum.
- Whether subagents can call project MCP tools. The design above does not require it.
- Whether to version `.humanize/` working folders or ignore them (proposal: add to
  `.gitignore`).
- Default target for academic text: `verdict` or `clean`. Mesmer's documented false
  positives are concentrated in academic abstracts, news and poetry, so `clean` may
  be unattainable for some genuinely human scientific prose.
