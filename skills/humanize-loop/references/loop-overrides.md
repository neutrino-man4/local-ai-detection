# Loop overrides

The rewriting itself follows the `humanizer` skill (blader/humanizer): its patterns §1-§26,
its "How to work" steps 1-4, and its "When not to act" section. This file lists what the
loop adds or changes. **Where this file and humanizer disagree, this file wins.** In
academic mode, `writing_style.md` takes precedence over humanizer and over section 3 (R) of
this file; the P, A and X rules are never overridden.

Codes (P1, R2, X1, ...) and humanizer pattern numbers (§1, §13, ...) are used in the run
log to explain each change.

## 1. Content and scope (P)

- **P1 Content is fixed.** Never change facts, numbers, units, equations, symbols,
  citation keys, quotations, proper nouns, technical terms, claim strength or hedges.
  Humanizer step 2 allows adding "a specific detail you know to be true". In the loop,
  add a detail only if it appears elsewhere in the same document. Otherwise delete the
  vague claim or mark it `[needs specific]`. A fabricated detail is worse than a vague one.
- **P2 One paragraph in, one paragraph out.** Humanizer allows merging, splitting and
  restructuring paragraphs. In the loop, a candidate replaces exactly one paragraph: no
  blank lines, the same number of list items, every LaTeX command and `%` comment line in
  place, and the original line-wrapping style.
- **P3 No added voice.** Do not add reactions, opinions, asides or humour (humanizer
  "Voice" section). Keep the ones the author wrote.
- **P4 Out of scope in the loop.** Headings are never edited: report §13 stock section
  titles, §20 decorative headings and §24 repeated headings instead of fixing them. §26
  (wrong reader) applies to replies, not to documents; ignore it.
- **P5 Explainable edits.** Every accepted rewrite must be explainable in one line naming
  the patterns and codes it applies, for example "§15 cut trailing -ing clause; §18
  'serves as' -> 'is'". A change that cannot be explained this way is not made.
- **P6 Occasional ordinary wordiness.** Isolated "as a result of", "in order to", "the
  fact that" are normal in human text. Leave existing ones alone and do not cut every
  sentence to minimal length. Prose with no slack reads machined.
- **P7 Consistent terms.** Do not cycle synonyms for one referent ("the model... the
  architecture... the framework"). Repeat the established term; in technical writing a
  changed term implies a changed referent.
- **P8 No new uniform patterns.** Replacing every dash with a comma, or every "serves as"
  with "is", creates a new detectable rhythm. Vary the repairs.

## 2. Artifacts humanizer does not cover (A)

- **A3 Placeholders:** `[Your Name]`, `2025-xx-xx`, `INSERT_SOURCE_URL`. Never fill them
  with invented values; leave them and list them in the report.
- **A4 Tool and citation markup leakage:** `:contentReference[oaicite:N]`, `[cite: N]`,
  `turn0search0`, `utm_source=chatgpt.com`, stray Private Use Area characters. Remove;
  where one stood in for a citation, mark `[needs source]`.

## 3. Research writing and LaTeX (R)

Applied in academic mode, and to every `.tex` file. Where an R rule conflicts with
`writing_style.md`, the writing style wins (see its conflicts section).

- **R1 Formal is not AI.** Good grammar, academic register and long words are not tells.
  A physics paper still says "we" and hedges where the evidence is uncertain.
- **R2 Passive voice (overrides §11).** Keep passive voice where the field uses it, for
  example in methods sections. Apply §11 only when the actor is unclear and matters.
- **R3 Author's house rules.**
  - Avoid: leveraged / leverage, principled, delve, intricate, nuance / nuanced,
    genuinely, crucially, endeavour, and similar.
  - Do not open sentences with adverbs or adverbial connectives ("Crucially, ...",
    "Importantly, ...", "Notably, ...", "Interestingly, ...", "Additionally, ...",
    "Furthermore, ..."). Put the subject first or join the sentence to the previous one.
  - Test each sentence: would an experienced researcher in the field write it like this?
  - No pleasantries, tonal hedging or emotional framing.
- **R4 Research-specific tells.**

  | Tell | Typical form | Fix |
  |---|---|---|
  | Attention opener | "In recent years, X has garnered significant attention" | Open with the problem or gap concretely |
  | Gap rhetoric | "remains largely unexplored", "a critical gap" | State what has and has not been done, with citations |
  | Inflated contribution | "a novel, comprehensive, principled framework" | Say in one clause what the method does differently |
  | Significance tail | "..., paving the way for", "..., shedding light on" | Delete, or name the concrete follow-up |
  | Vague improvement | "significantly improves performance" | Give the number and the baseline (only from the source) |
  | "Significant" without statistics | "a significant excess" with no stated significance | Reserve for statistical significance with a value; else "large", "clear", or the number |
  | Plays-a-role | "plays a crucial role in" | "determines", "sets", "dominates", or the dependence |
  | Realm/landscape | "in the realm of", "the evolving landscape of" | Name the field or drop it |
  | Harness/unlock | "harness the power of", "unlock the potential of" | "use" |
  | Summary echo | "In summary, our results demonstrate..." | End when the content ends |

- **R5 Technical vocabulary to keep** (humanizer §12 applies only to figurative use):
  robust/robustness (to systematics, estimators, adversarial), landscape (loss, energy,
  string), key (cryptographic, key-value), enhance/enhancement (signal, cross-section,
  Sommerfeld), features (input, learned), interplay (established usage, e.g. QCD and
  electroweak effects), pivotal quantity, underscore (literal character),
  align/alignment (detector, sequence, model), gate/gating (logic, quantum, trigger).
- **R6 LaTeX sources.**
  - Quotes as ` ``like this'' ` (overrides §21: match the document's convention).
  - `--` in numeric ranges (`1--5`, `pp.~3--7`) is correct typography; §8 does not apply
    to it. `---` used as a dash follows §8.
  - No Markdown; bold emphasis is `\textbf`, and §19 applies to it.
  - Never touch math, `\label`, `\cite` and `\ref` keys, macros, or `%` comments.
  - Respect the journal's English variety (APS journals use American spelling).

## 4. Forbidden (X)

The only lever is better prose. Never use:

- **X1** typos, misspellings or deliberate grammar errors;
- **X2** homoglyphs, invisible or unusual Unicode characters, odd spacing;
- **X3** random synonym substitution or thesaurus noise;
- **X4** fragments, slang or register shifts that do not fit the genre;
- **X5** invented facts, numbers, citations, quotations or personal anecdotes;
- **X6** removing hedges or adding certainty the evidence does not support.

Mesmer normalises many character tricks anyway, and such edits damage the document.

## 5. Candidate checklist

Run after humanizer step 3 ("Check the draft"). Every answer must be "no":

- Has any fact, number, citation, quotation, term or hedge changed? Was anything invented?
- Is the candidate more than one paragraph, or has a list item, LaTeX command or `%`
  comment line gone?
- Does it introduce a repair repeated so uniformly that it forms a new pattern (P8)?
- Does any change lack a one-line explanation with pattern numbers or codes (P5)?
- In academic mode: would an experienced researcher in the field object to any sentence?
