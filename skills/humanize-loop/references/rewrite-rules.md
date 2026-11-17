# Rewrite rules

Rules for rewriting a flagged paragraph so that it reads as plainly written human prose
without changing what it says. Sections 1-5 are condensed from the humanize-text skill
(itself derived from Wikipedia's "Signs of AI writing", WikiProject AI Cleanup).
Section 6 is new and built on that article's "Signs of human writing" section. Section 7
covers research writing and LaTeX, including the author's house rules.

Codes (C1, L3, ...) are used in the run log to explain each change.

## 1. Principles

1. **Why AI text reads as AI.** Models regress to the mean: specific facts are smoothed
   into generic, positive statements that would fit any subject. The text becomes less
   specific and more exaggerated at the same time. Almost every fix is therefore:
   - put the specific fact back (only if the source has it), or
   - delete the generic claim.

   Swapping one word for a synonym is not a fix.
2. **Preserve content.** Keep every fact, number, unit, equation, symbol, citation key,
   quotation, proper noun, technical term and claim strength. Text inside quotation marks,
   code and mathematics is never edited.
3. **Never invent specifics.** If the source has the concrete fact, use it. If it does
   not, delete the vague claim or mark it `[needs specific]`. A fabricated detail is worse
   than a vague one.
4. **Fix the sentence, not the word.** The tell is usually a construction (a trailing
   participle clause, a significance sentence), not a single word. Restructure or remove
   it.
5. **Context decides.** Technical senses are fine: robust estimator, loss landscape,
   cryptographic key, signal enhancement, input features, pivotal quantity, detector
   alignment. Only figurative, inflationary uses are tells.
6. **Density, not single hits.** One "additionally" proves nothing; clusters do. Remove
   clusters and patterns, not every listed word.
7. **No new uniform patterns.** Replacing every em dash with a semicolon, or every "serves
   as" with "is", creates a new detectable rhythm. Vary the repairs.
8. **Formal is not AI.** Good grammar, academic register and long words are not tells.
   Keep the genre's register: a physics paper still says "we", uses passive voice where
   conventional, and hedges where the evidence is uncertain.
9. **Shorter is usually right**, typically 10-30% after cutting puffery and summaries.
   Do not pad back. But do not strip every ordinary filler either (rule H5).

## 2. Content patterns (fix first: they change what the text claims)

- **C1 Undue significance, legacy, broader trends.** "marks a pivotal moment", "stands as a
  testament", "reflects broader", "setting the stage for", "evolving landscape", "indelible
  mark", "deeply rooted", including hedged forms ("though minor, it contributes to the
  broader..."). **Fix:** delete, or state the concrete consequence the source documents.
- **C2 Canned notability.** "featured in", "independent coverage", "profiled in major
  outlets", "active social media presence". **Fix:** say what a named source reported, or
  delete.
- **C3 Trailing participle analysis.** "..., highlighting its importance",
  "..., reflecting the region's heritage", "..., contributing to the development of".
  **Fix:** cut the clause. If it hides a fact, give the fact its own sentence with a
  subject and a finite verb.
- **C4 Promotional tone.** boasts, vibrant, rich (figurative), profound, nestled, in the
  heart of, groundbreaking, renowned, diverse array, commitment to, seamless, stunning.
  **Fix:** replace evaluation with measurable facts.
- **C5 Vague association.** "is associated with", "in connection with", "connected to".
  **Fix:** state the actual relation (taught at, was CEO of, measured).
- **C6 Vague attribution and inflated consensus.** "experts argue", "observers note",
  "several sources" (with one citation), "such as" before a complete list. **Fix:** name
  the source and match the count, or delete the opinion.
- **C7 Formulaic challenges and outlook.** "Despite its X, Y faces challenges... Despite
  these challenges, Y continues to thrive"; vague future-outlook endings. **Fix:** keep
  concrete challenges as plain facts; cut the frame and the optimistic close.
- **C8 "X and Y" catch-all sections** ("Legacy and Impact", "Challenges and Future
  Directions"). **Fix:** rename to the specific content or merge. Headings are structure,
  so in this loop only flag them in the report, never change them.

## 3. Language patterns

- **L1 AI vocabulary (in clusters).** additionally (sentence-initial), align with, boasts
  (= has), bolstered, crucial, deep dive, delve, emphasizing, enduring, enhance, fostering,
  garner, highlight (verb), interplay, intricate/intricacies, key (adjective), landscape
  (abstract), meticulous(ly), pivotal, robust (figurative), showcase, tapestry, testament,
  underscore (verb), valuable, vibrant. **Fix:** usually the word sits in a C1/C3
  construction, and fixing that removes it. Otherwise use the plain word: crucial ->
  necessary or delete; enhance -> improve or increase by N; showcase -> show; delve ->
  examine or delete.
- **L2 Copula avoidance.** serves as, stands as, functions as, represents, marks; boasts,
  features, offers, maintains in place of "has". **Fix:** is, are, was, has.
- **L3 Negative parallelism.** "not only... but also", "it's not just X, it's Y", "not X
  but Y", "Y rather than X", and a sentence twisted by the next with "however". **Fix:**
  state the positive claim. Keep a contrast only when the contrasted view is real and
  attributed.
- **L4 Rule of three.** Reflexive triplets of adjectives or phrases. **Fix:** keep three
  only when exactly three real items exist; otherwise give the one or two that matter, or
  the full list.
- **L5 Stiff synonyms.** authored -> wrote, utilized -> used, relocated -> moved,
  attempted -> tried, commenced -> began, facilitate -> help or allow, prior to -> before,
  subsequently -> later.
- **L6 Elegant variation.** Cycling synonyms for one referent ("the model... the
  architecture... the framework"). **Fix:** repeat the exact term. In technical writing a
  changed term implies a changed referent.
- **L7 Didactic filler and summaries.** "it is important to note", "it is worth noting",
  "may vary", "In summary", "Overall," restating the paragraph. **Fix:** delete; if the
  caveat carries a fact, state the fact once.
- **L8 Title-as-entity leads.** "X refers to...", "'List of X' is a curated compilation".
  **Fix:** "X is...".

## 4. Structure and formatting (within a paragraph)

- **F2 Inline-header lists** (`- **Label:** text`) inside a paragraph: prose instead,
  unless it is a genuine enumeration. List items are structure; keep their count.
- **F4 Em dashes.** Overused or spaced dashes for punch. **Fix:** commas, colons,
  parentheses or full stops, varied. Keep at most an occasional unspaced dash where it is
  the best mark. Apply this rigorously: Claude overuses em dashes more than other models.
- **F5 Emoji as decoration:** remove.
- **F7 Quotes:** match the document's convention (LaTeX ``...''; plain text straight
  quotes); fix inconsistent mixing.
- **F8 Markdown in the wrong medium** (`**bold**`, backticks, `#` in LaTeX): convert to the
  target markup.
- **F9 Template-shaped paragraphs** (topic sentence, facts, significance sentence, every
  time): let the paragraph end when the information ends.
- **F10 Sentence-initial transitions in series** (Additionally, Moreover, Furthermore,
  Notably, Consequently, Ultimately): remove most; let the logic connect sentences.

## 5. Artifacts (any hit is near-conclusive; always remove)

- **A1 Chatbot address:** "Certainly!", "I hope this helps", "Here is a...", "Let me
  know...", "In this section, we will discuss...".
- **A2 Cutoff and availability disclaimers:** "as of my last update", "while specific
  details are limited", "based on available information", plus any speculation that
  follows them.
- **A3 Placeholders:** `[Your Name]`, `2025-xx-xx`, `INSERT_SOURCE_URL`. Never fill them
  with invented values; leave them and report them.
- **A4 Tool and citation markup leakage:** `:contentReference[oaicite:N]`, `[cite: N]`,
  `turn0search0`, `utm_source=chatgpt.com`, stray Private Use Area characters. Remove;
  where one stood in for a citation, mark `[needs source]`.
- **A5 Refusals and meta-AI phrasing:** "As an AI language model".
- **A6 Procedural self-assurance** in notes, rebuttals or change logs: "improved clarity
  and flow", "while preserving the original meaning". **Fix:** say what concretely
  changed.

## 6. Features of human writing to aim for (own rules)

Based on Wikipedia's "Signs of human writing" (Syntax). Over 25 years of Wikipedia
editing, these constructions were observed to be more common in human-written text,
because models default to a formal, neutral, encyclopedic tone and avoid them. They are
targets for the rewrite, applied only where the genre and the facts allow.

- **H1 Simple is/has phrases.** Prefer "there is a", "it has a", "X is a Y" over
  constructions that avoid them. This is the positive form of L2.
- **H2 Plain verbs.** Use the ordinary word a writer reaches for first: wrote, used, moved,
  tried, died, began, showed, found. This is the positive form of L5.
- **H3 Definite, checkable statements.** Where the source supports it, say it outright: "is
  the only", "was the first", "one of two", "the largest of the three samples".
  Definiteness must come from the facts. Never add a superlative or a ranking the source
  does not state.
- **H4 Qualifiers and intensifiers where meant.** Humans write "very", "perhaps", "tends
  to", "fairly", "probably" when they mean them. Calibrate each hedge to the evidence:
  - Do not remove a genuine hedge.
  - Do not hedge uniformly.
  - Do not add a hedge to a claim the source states firmly.
- **H5 Occasional ordinary wordiness.** Isolated constructions such as "as a result of",
  "in order to", "all of the", "a part of", "the fact that" are normal in human text. Leave
  existing ones alone, and do not optimise every sentence to minimal length. Prose with no
  slack at all and perfect parallelism reads machined.
- **H6 Explainable edits.** A human editor can say why each change was made. Every
  accepted rewrite must be explainable in one line naming the rule codes it applies (for
  example "C3 cut trailing significance clause; L2 'serves as' -> 'is'"). This explanation
  goes into the run log. A change that cannot be explained this way is not made.
- **H7 Content-driven rhythm.** Let sentence length follow the content. Short sentences
  for single facts, longer ones for reasoning, and no fixed paragraph template. Do not
  impose an artificial alternation, which is itself a pattern (rule 7).
- **H8 Consistent terms, specific nouns.** Repeat the established technical term. Prefer
  names, dates, quantities and units over evaluative adjectives.

## 7. Research writing and LaTeX

**Author's house rules (from the humanize-text owner):**

- Avoid: leveraged / leverage, principled, delve, intricate, nuance / nuanced, genuinely,
  crucially, endeavour, and similar.
- Do not open sentences with adverbs or adverbial connectives ("Crucially, ...",
  "Importantly, ...", "Notably, ...", "Interestingly, ...", "Additionally, ...",
  "Furthermore, ..."). Put the subject first or join the sentence to the previous one.
- Test each sentence: would an experienced researcher in the field write it like this?
- No pleasantries, tonal hedging or emotional framing. Hedge only where the evidence is
  uncertain.

**Research-specific tells:**

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

**Technical vocabulary to keep** (flag only figurative use): robust/robustness (to
systematics, estimators, adversarial), landscape (loss, energy, string), key (cryptographic,
key-value), enhance/enhancement (signal, cross-section, Sommerfeld), features (input,
learned), interplay (established usage, e.g. QCD and electroweak effects), pivotal
quantity, underscore (literal character), align/alignment (detector, sequence, model).

**LaTeX sources:**

- Quotes ``like this''.
- `--` for ranges, `---` only where a dash is truly best, unspaced.
- No Markdown.
- Never touch math, `\label`, `\cite` and `\ref` keys, macros, or `%` comments.
- Keep every LaTeX command in the paragraph.
- Respect the journal's English variety (APS journals use American spelling).

## 8. Forbidden

The only lever is genuinely better prose. Never use:

- typos, misspellings or deliberate grammar errors;
- homoglyphs, invisible or unusual Unicode characters, odd spacing;
- random synonym substitution or thesaurus noise;
- fragments, slang or register shifts that do not fit the genre;
- invented facts, numbers, citations, quotations or personal anecdotes;
- removing hedges or adding certainty the evidence does not support.

Mesmer normalises many character tricks anyway, and such edits damage the document.

## 9. Ineffective indicators (do not "fix")

These are unreliable or counter-indicative:

- perfect grammar;
- mixed formal and casual register;
- prose that only feels bland;
- formal or academic vocabulary in general;
- transition words in isolation;
- unsourced content;
- random or correct complex markup.

Judge a rewrite on whether it is specific, accurate and plainly written.

## 10. Final read of a candidate

Every answer must be "no":

- Does any sentence assert importance, significance or a broader trend without a concrete
  fact?
- Does any sentence end in ", [verb]-ing ..." that interprets?
- Is there a cluster of L1 words?
- Is "serves as / stands as / features / boasts / offers" used where "is / has" works?
- Is there a "not just... but", "not X, it's Y" or rhetorical "rather than"?
- Is there a triplet that exists for rhythm rather than content?
- More than about one em dash per 500 words?
- Has any fact, number, citation, quotation, term or hedge changed? Was anything invented?
- Would an experienced writer in this genre have written each sentence this way?
