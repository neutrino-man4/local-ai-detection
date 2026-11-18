# Writing style for physics papers (academic mode)

In academic mode this file takes precedence over `humanizer` (§1-§26) and over the R rules in
`loop-overrides.md`. The P, A and X rules still hold: content stays fixed, one paragraph stays
one paragraph, and nothing here licenses a typo, an invented fact, an added aside or a removed
hedge. Where a rule here contradicts humanizer or an R rule, the conflicts section at the end
gives the resolution.

Quoted examples are from published physics papers, including their LaTeX macros. A line
marked "AI-style" is a constructed counter-example. Rule codes W1-W53 and C1-C17 are cited in
the run log like P, R and X codes.

## Contents

1. Word choice (W1-W8)
2. Pronouns and voice (W9-W13)
3. Sentence construction (W14-W21)
4. Paragraph construction (W22-W25)
5. Punctuation (W26-W33)
6. Citations, figures and equations in prose (W34-W38)
7. Numbers, uncertainties and significance (W39-W43)
8. Per-section rhetoric (W44-W50)
9. Spelling and register (W51-W53)
10. Conflicts with humanizer and loop-overrides (C1-C17)
11. Paragraph checklist

## 1. Word choice

**W1. Report results with plain verbs: find, show, see, observe, obtain.** Theory papers attach
them to "we"; collaboration papers use "is found to", "is observed", "are seen".
*Demonstrate* is rare.
> We obtain a 20--30\% improvement in sensitivity when using the multi-dimensional fit method, and about a 35--40\% improvement when combining the data sets recorded in 2016 and 2017 relative to the individual results.
> Looking at the quark chirality, we observe that the bounds on operators with left- and right-handed tops are similar in strength.
> Good agreement between the data and background-only fits is observed for all methods.

AI-style: "Our results demonstrate a remarkable improvement in sensitivity." House version: the
first sentence above, which gives the size and the baseline.

**W2. One calibrated hedge, placed on the claim it qualifies.** Typical forms: *in principle*,
*likely*, *may*, *appears to*, *can be expected*, and scope clauses that name the condition
under which a result holds.
> Given this new piece of the event simulation puzzle through fast neural networks it should in principle be possible to add parton showers, possibly including hadronization, and detector effects to a full machine learning description of LHC events.
> This agreement gives evidence that the tagging techniques have approached a global bound on the maximum possible discrimination power achievable, at least in the context of parton shower simulations.

**W3. Define a term once, then repeat it exactly.** Introduce new terms with `\emph{}`, "which
we call", "known as" or "referred to as", often with the abbreviation in parentheses, and use
the same word afterwards (P7). Contested terms get LaTeX scare quotes.
> A quantile regression (QR) network is then used to decorrelate the anomaly score of the VAE from the dijet mass. This method is referred to as \vae.
> Intuitively, we define quark and gluon jets as the ``pure'' categories that emerge from two different jet samples.

**W4. Words on the §12 list are allowed when they state a dependence; never add them.**
*Crucial*, *key*, *robust*, *enhance*, *highlight*, *interplay* and *powerful* appear in good
physics prose, but each time the sentence says what depends on what. *Leverage, delve,
intricate, nuance, pivotal, landscape, underscore* do not appear.
> Precise predictions are crucial to extract any Lagrangian parameter from LHC rate measurements.
> The bounds on color-octet operators thus rely on the interplay between contributions of order $\Lambda^{-2}$ and $\Lambda^{-4}$, where the inclusion of both terms is particularly important.
> The key to the GAN training is the alternating training of the generator and discriminator networks with their respective loss functions given in Eq.\eqref{eq:GAN1} and Eq.\eqref{eq:GAN2}.

AI-style: "This crucial, robust framework highlights the key interplay of operators." Rule: one
such word per paragraph at most, and only with a stated dependence.

**W5. Prefer *use* to *utilize*.** *Utilize* and *employ* belong to collaboration register.
Keep an existing *utilize* in a collaboration paper; do not introduce it elsewhere.

**W6. Evaluative adjectives sit next to a measured claim.** *Powerful discriminant* is a term of
art for discrimination power. *Excellent performance* is followed by what it refers to. Do not
add evaluative adjectives in a rewrite (P3).
> Using linear classification with energy flow polynomials, we achieve excellent performance on three representative jet tagging problems:  quark/gluon discrimination, boosted $W$ tagging, and boosted top tagging.

**W7. Ordinary wordiness is normal.** *In order to*, *the fact that*, *as a result of* and *it is
important to note* occur in careful physics prose (P6).
> These methods therefore assume a particular hypothesis for the mass of the new resonance in order to construct the samples for training.

**W8. *Novel*, *comprehensive* and *first* appear only in abstracts, contribution sentences and
summaries, once each.** Keep an existing one; never add a second in the same section.
> In this paper we present a comprehensive analysis of the top sector in the framework of SMEFT, based on the data collected mostly during the LHC Run~II.

## 2. Pronouns and voice

**W9. Theory papers say "we" for choices, derivations and results**, including in methods.
Between a quarter and a half of sentences contain we, our or us.
> We extract the statistical uncertainties and a leading set of up to $\sim20$ systematic uncertainties for each experiment and simulate a Gaussian shape of the completely exclusive likelihood for statistics and systematics.
> For both the generator and the discriminator we use a 10-layer MLP with 512 units each, the remaining network parameters are given in Tab.~\ref{tab:details}.

**W10. Collaboration papers are impersonal, with "we" only at decision points.** Abstracts and
summaries are passive and presentational.
> To reduce the QCD multijet background, we require the jet mass to be between 55 and 215\GeV.
> A search is presented for resonances with masses above \BulkGMassMin{}\TeV that decay to \PW{}\PW, \PZ{}\PZ, or \PW{}\PZ boson pairs.
> The VAE is trained using jets from the CR.

**W11. Simulation and event-generation chains are passive, usually past tense, in every type
of paper.** The tense may switch from present to past within one subsection.
> For each type of sample, 200k jets were generated.
> All jets were required to have $p_T\in[500,550]$ GeV and rapidity $|y|<2.5$.

**W12. Tense.** Present for what the paper does, what a figure shows and what holds in general;
present perfect for the opening of conclusions ("We have shown"); simple past for what was done
in the study when recapping it.
> We have shown that it is possible to GAN the full phase space structure of a realistic LHC process, namely top pair production all the way down to the kinematics of the six top decay jets.
> To illustrate the power of the Operational Definition, we tested it in the realistic context of $Z$+jet and dijet processes.

**W13. "One", "us" and the reader.** Generic "one" goes with *can*, *might*, *needs*. "Us" is
the object of *allow*, *require*, *leave*. "We refer the reader to" is normal. Do not introduce
"you" in a research paper.
> To evaluate the matrix element on a quantum computer one first needs to define circuits that perform time evolution of the system, as well as circuits that can create and measure the ground and exited states of the theory.
> In particular, the \textsc{SFitter} technology allows us to easily study correlations between Wilson coefficients and to compare the impact of theoretical and experimental uncertainties.

## 3. Sentence construction

**W14. Most sentences run 15-35 words; short sentences are rare.** Fewer than one sentence in
twenty has under 10 words. Variation comes from the 15-35-word range, with the occasional long
sentence (over 40 words) carrying a list, a condition or a result with its baseline. A rewrite
must not add fragments or punchy one-liners to vary rhythm.

AI-style: "The result is clear. Linear methods suffice." House version: one sentence that states
the result and its condition, for example
> In practice, though, we find that the required set of $\mathcal G$ needed for convergence is rather reasonable in a variety of jet contexts.

**W15. Subject first is the default.** "The" is the most common sentence opener. The next most
common openers frame the sentence: "In Fig.~X we show", "In this paper, we", "For each", "To",
"Since", "As".
> In Fig.~\ref{fig:Global} we show the profile likelihoods for each of the top-related effective operators.
> For each method, the selection efficiency on the benchmark signal models is evaluated.

**W16. Logical connectives open about one sentence in eight (fewer in collaboration papers);
contrast goes mid-sentence.** Common openers: *Finally, Thus, Therefore, In addition,
Furthermore, Similarly, In particular, For example, Here, Note that*. Sentence-initial
*However* is rare; contrast usually sits mid-sentence with *however* or *though*. Do not create
a new pair of adjacent connective openers outside an enumeration (*First ... Next ...
Finally*) (P8).
> For small values of $\beta$, however, one is highly sensitive to nonperturbative effects, which must be modeled or extracted from data.
> In practice, though, we find that the required set of $\mathcal G$ needed for convergence is rather reasonable in a variety of jet contexts.
> It therefore learns how to perform this compression and decompression on QCD background jets, but might fail in performing this task as well on anomalous jets not present in the training sample.

**W17. Stance adverbs are rare and must carry a reason.** *Crucially, Remarkably,
Interestingly, Importantly, Surprisingly* open well under one sentence in a hundred, and never
in collaboration papers. Each is followed in the same sentence by a claim that is in fact
surprising or necessary. Keep an existing one; never add one (C4).
> Crucially, this worked even for observables that do not exhibit quark/gluon mutually irreducibility, as long as the observable used to extract the fractions does.

**W18. Participial and framing openers are normal** when they state a precondition for the
main clause.
> Given the Casimir scaling limit of single-emission observables, a promising approach for improving quark/gluon discrimination is to design observables that are directly sensitive to multiple emissions within the jet, even at lowest order.

**W19. A trailing participle clause states a consequence or mechanism, not a value judgment.**
> Each of the two bosons decays into one large-radius jet, yielding dijet final states.
> Therefore, the highest and lowest mass regions in each set of windows are used only as sidebands, resulting in 12 total SRs in which the training procedure is performed.

AI-style: "..., emphasizing the importance and novelty of the methods developed in the present
work." The tail evaluates rather than informs; cut it.

**W20. Relative clauses with *which* and *where* carry definitions and regimes.** Restrictive
*which* without a comma is normal; do not convert *which* to *that*. *Where* follows displayed
equations and introduces kinematic regimes.
> At lower top efficiencies, where there are well-resolved jets, $N_3$ and $\Nsubnobeta{3,2}$ exhibit similar discrimination power, but at higher efficiencies, where there are not well-resolved jets, the structure of $N_3$ leads to considerably improved performance.

**W21. Parentheses carry glosses, abbreviations, alternative values and cross-references.**
Whole parenthetical sentences occur.
> In principle, to have access to the full dynamics of the Large Hadron Collinder (LHC), one would need to describe the energy range between $\ord(\SI{10}{\MeV})$ (the smallest resolvable transverse momentum between hadrons) and \SI{7}{\TeV} (the beam energy of the LHC).

## 4. Paragraph construction

**W22. Four to six sentences.** Single-sentence prose paragraphs are rare; do not create one by
splitting (P2).

**W23. Open with the object or the step, not with a framing claim.** Paragraphs open with the
thing being studied, a figure ("In Fig.~X we show"), or a transition that names the next task
("We now consider", "We begin by").
> For our global LHC analysis we use the \textsc{SFitter} framework~\cite{Lafaye:2007vs,Lafaye:2009vr}, which focuses on a proper treatment of uncertainties in a conservative frequentist approach.
> We begin by verifying the power-counting argument of \Eq{eq:pc_qvsg}, which suggested that $\ecfvarnobeta{2}{3}$ and $\ecfnobeta{3}$ should be highly correlated with $U_1 = C_1 = \ecfnobeta{2}$.

**W24. Close on the last fact, or on one inference the paragraph has not yet stated.** A closer
starting *This/Thus/Therefore/We conclude* adds a cause, a consequence or a physics reading; it
does not restate. Many paragraphs end on a number.
> The quantum computer reproduces the simulated result to about \SI{5}{\percent} accuracy.
> This illustrates that nonlinear combinations of the $N$-subjettiness observables are crucial for extracting the full physics information.

AI-style: "...reaches 5% accuracy. This highlights the immense potential of quantum computing
for collider physics." Cut the second sentence; end on the number.

**W25. Caveats follow results inside the same paragraph**, attached directly to the result they
limit, often with *though*, *again* or *it should be noted*.
> Again, we caution that the \pythia fractions solely provide a heuristic to demonstrate the performance of the method and should not be taken as fundamental to quark and gluon jets.
> It should be noted that the linear classifier is not trained specifically for the low signal efficiency region and it may be possible that choosing a different hyperplane could boost performance there.

## 5. Punctuation

**W26. `---` is a paired bracket around an appositive, used sparingly** (at most about one per
1,000 words, and many papers use none). Follow the document's spacing (unspaced or spaced).
Never use `---` to join two independent clauses, and never use `--` or a Unicode dash as a
sentence dash.
> We presented a number of case studies of relevance to the jet substructure community---boosted top tagging, boosted $W/Z/H$ tagging, and quark/gluon discrimination---demonstrating the power of power-counting techniques to design discriminants for specific purposes.
> They perform a dimensional reduction of the input data --- often an image --- to create a latent representation.

**W27. `--` joins numeric ranges and two-name compounds:** `20--30\%`, `2016--2018`,
`Randall--Sundrum`, `Cambridge--Aachen`. Inside math, ranges use a hyphen (`$\approx 1-2$~TeV`).

**W28. Semicolons join a statement to its pointer, consequence or deferral**, and are used
sparingly. Recurrent shapes: "...; see \Refs{} for detailed studies", "...; this illustrates
...", "...; we leave such studies to future work".
> One feature worth noting is that the lower bound is accurately extracted by every observable; it is the upper bound that is more difficult to saturate with a generic observable.

**W29. Colons introduce lists, displayed equations and explanations.**
> Nonetheless, jets can be made perfectly well-defined: any hadron-level algorithm for finding jets that is infrared and collinear (IRC) safe provides an operational jet definition that can be compared to perturbative predictions.
> We consider three representative jet tagging problems: quark/gluon discrimination, boosted $W$ tagging, and boosted top tagging.

**W30. Serial comma.** Use it unless the paragraph or document already omits it.

**W31. *e.g.* and *i.e.* follow the document.** Common forms: `e.g.\ ` without a comma inside
parentheses, `\emph{e.g.},` with a comma, or an `\ie` macro. Match whichever the document uses.

**W32. Quotation marks are LaTeX quotes; keep any irregular closings.** Scare quotes mark
contested labels (``quark''), coined verbs and slang (``black box''). Do not normalise existing
quote marks (P1).

**W33. No contractions and no exclamation marks.**

## 6. Citations, figures and equations in prose

**W34. A citation attaches with `~\cite{}` to the word or claim it supports, before the
punctuation.** Multiple keys go in one `\cite{}`. Keep the document's spacing before `\cite`.

**W35. A citation used as a noun is "Ref.~\cite{}" or "Refs.~\cite{}"** (or `\Ref{}`/`\Refs{}`
macros); letters may use a bare `in~\cite{}` or `see~\cite{}`.
> One open question is why the GAN setup of Ref.~\cite{dutch} does not properly work and is replaced by a variational autoencoder with a density information buffer.

**W36. Figures, tables and sections.** Mid-sentence: `Fig.~\ref{}`, `Tab.~\ref{}`,
`Sec.~\ref{}`; collaboration papers spell out `Section~\ref{}`, `Table~\ref{}` and, at the
start of a sentence, `Figure~\ref{}`. Theory papers prefer "In Fig.~X we show"; collaboration
papers prefer "Figure~X shows". A pointer may be appended after a comma: ", see Fig.~X".
> Figure~\ref{fig:nsubj} shows a notable deviation in the shape of the \nsubjDDT distribution between data and simulation.
> Non-trivial correlations as between $C_{tG}$, $C_{\phi Q}^3$, and $C_{Qq}^{3,1}$ vanish once we include the full data set, see Fig.~\ref{fig:Correlations}.

**W37. Equations are part of the sentence.** The lead-in runs straight into the display ("is
given by", "can be written as", "takes the form"); the display ends with `\,.` or `\,,` inside
the math; after a comma the text continues in lower case, usually with *where*. Keep the
document's reference form (`Eq.~\eqref{}`, `\Eq{}`, `\cref{}`).
> where $n_\phi$ denotes the dimensionality of the Hilbert space for a given lattice point, $N$ is the total number of lattice points in each spatial direction, and $d$ represents the number of spatial dimensions.

**W38. Technical asides go in footnotes in theory papers.** Footnotes hold caveats, timing
figures and jokes; do not move footnote content into running text.

## 7. Numbers, uncertainties and significance

**W39. Every quantitative claim names its baseline and its condition.**
> This method yields an improvement in sensitivity of up to 30\% relative to previous search methods.
> The largest improvements are seen for the 6+6 prong \GtoHH signal, in which anomaly detection methods are found to reduce the cross section needed for a $5\sigma$ discovery by a factor of 6.4 (2.9) as compared to the inclusive (3-prong) selection.

AI-style: "The method significantly improves sensitivity." House version: the first sentence
above.

**W40. Precision is stated with *about*, *up to*, *at the order of*, *within*, $\mathcal O()$.**
> As we can see, momentum conservation at the GAN level is satisfied at the order of 2\%.
> The extracted \PV{}+jets cross sections are found to be compatible with the SM expectations within one standard deviation of the post-fit uncertainties.

**W41. Alternative values go in parentheses in the same order as their labels; lists of values
end with *respectively*.**
> The largest excesses of events seen by the \cathode, \cathodeb, \quak, and \vae methods had local significances of 2.2, 2.9, 2.6, and 2.3$\sigma$ at resonance masses of 2.3, 2.3, 4.7, and 4.9\TeV, respectively.

**W42. Statistical significance has a fixed formula; *significantly* as an intensifier needs a
comparison.** Statistical results read "No significant excess ... is observed", with local
significances in $\sigma$ and limits at 95\% CL. *Significant(ly)* outside statistics is
attached to a comparison or a size: *significantly larger feature sets*, *significantly smaller
quantum resources*. In a paragraph that reports $\sigma$ or CL values, use *significant* only
in the statistical sense (C6).
> No significant excess over the background estimation is observed. Upper limits on the production cross section at 95\% confidence level (\CL) are set.
> We have argued that the dynamics of a low energy EFT can be simulated with significantly smaller quantum resources than the dynamics of the corresponding full theory.

**W43. Exclusion and limit sentences follow a template.**
> For the HVT model~B, we exclude at 95\% \CL\ \PWpr and \PZpr spin-1 resonances with masses below \MassExclWPr and \MassExclZPr{}\TeV, respectively.

## 8. Per-section rhetoric

**W44. Introductions open on physics, not on attention.** The first sentence states what the
field does or an established fact; prior work comes with citations; the gap is stated as what
has not been done. "In recent years" is never an opener.
> It is well known that quantum computers can in principle simulate the time evolution of quantum field theories~\cite{Jordan:2011ne}.

**W45. The contribution is one sentence: "In this paper(,) we" (or "In this analysis, we") +
present-tense verb + what.** Positioning against other groups credits them by name.
> In this paper we show that this is indeed possible by using effective field theories (EFTs) which have been designed to reproduce the desired long distance physics.

**W46. The introduction ends with a roadmap** ("The paper is organized as follows."), one
sentence per section. Letters omit it.

**W47. Results paragraphs run figure, observation, interpretation.**
> For operating points with $\varepsilon_s\gtrsim0.5$, all methods except the linear $N$-subjettiness classifier show essentially the same performance.
> This shows the impact of the $t\bar{t}Z$ cross section measurements in the global fit.

**W48. Limitations are stated as plain facts about the method.**
> The main limitation of the GAN approach is that statistical uncertainties in poorly populated tails of distributions in the training data appear as systematic uncertainties in the same phase space regions for the generated high-statistics samples.
> One aspect of jet substructure that has not been studied here is the correlations between discriminants.

**W49. Future work: "We leave ... to future work" and "It would be interesting to ...".**
> In this letter, we work at fixed lattice size and we leave the detailed investigation of these issues to future work.

**W50. Conclusions open with a recap in present perfect or past ("We have presented", "In this
paper, we have introduced", "A search is presented"), restate the main numbers, and end on the
last finding or one concrete outlook.**
> Using only 2 qubits per lattice we obtain results within \SI{10}{\percent} of the analytical result, and by using noise-mitigation techniques, uncertainties due to running on present-day hardware can be reduced to about \SI{5}{\percent}.

## 9. Spelling and register

**W51. Spelling follows the paper.** Never change spelling in a rewrite; new words follow the
paragraph's existing variety (American or British).

**W52. Register is formal but personal in theory papers.** First-person judgment ("we suspect",
"We are particularly interested") appears in theory papers, never in collaboration papers.

**W53. Humour and informal words are confined to footnotes and to authors who already use
them.** Keep the author's own; never add (P3).

## 10. Conflicts with humanizer and loop-overrides

"Style wins" means the W rule applies in academic mode and the other rule does not.

**C1. §8 dashes and R6.** Style wins within limits. Keep existing `---` pairs that bracket a
list or definition. Replace a `---` that joins two clauses, and any dash beyond about one per
1,000 words, as §8 says. Add no dash to a document that has none. `--` in ranges and
two-name compounds is never a dash (W27).

**C2. §11 passive voice.** Style wins, beyond R2. Do not convert passive to active in methods,
event generation, selection, collaboration abstracts or summaries, or "is found to" results.
§11 applies only where a theory paper's own "we" would make an author's choice clearer.

**C3. §12 AI vocabulary and R5.** Style wins for single instances that state a dependence,
including figurative *key* ("a key ingredient"). Remove a flagged word only when two or more
cluster in one paragraph, or when the sentence states no dependence. Never introduce one.

**C4. R3 sentence-initial adverbs and connectives.** Split.
(a) Logical connectives (*However, Therefore, Thus, Finally, In addition, Furthermore,
Additionally, Similarly, For example, In particular*): style wins; keep them, at most one
*Furthermore/Additionally* per paragraph, and no new adjacent pair outside an enumeration
(W16).
(b) Stance adverbs (*Crucially, Importantly, Interestingly, Notably, Remarkably*): R3 holds for
anything the rewrite adds; an existing one stays only if its sentence states why it matters.

**C5. R3 vocabulary list.** R3 holds for introduced words. Technical *genuine* (a genuine W or
Z boson decay) is kept.

**C6. R4 "significant" without statistics.** Style wins in part. *Significantly* is allowed
when it modifies a stated comparison. In a paragraph that reports $\sigma$, CL or excesses, R4
applies. A bare "significant improvement" with no comparison remains an R4 tell.

**C7. R4 inflated contribution, plays-a-role and significance tails.** R4 holds for anything the
rewrite adds. An existing instance stays when the same sentence gives the mechanism, as in
> Observables combining top production and decay play a special role in the SMEFT interpretation, because they probe features of operators not accessible in top production alone~\cite{AguilarSaavedra:2010zi,Aguilar-Saavedra:2017nik,deBeurs:2018pvs,Neumann:2019kvk}.

and otherwise R4 applies.

**C8. R4 summary echo.** Style wins for the first sentence of a conclusions section ("To
summarize, we have presented"); R4 holds for summary echoes at the end of a paragraph or
section.

**C9. R4 gap rhetoric and "In recent years".** A gap stated with citations and a concrete
missing item is house style (W44). R4 applies to gap phrases without citations and to "In
recent years" as an opener.

**C10. §15 shallow -ing phrases.** Keep -ing tails that state a consequence or mechanism, even
with a listed verb ("highlighting that the higher $d$ \Bs carry essential information"); §15
applies to tails that evaluate importance, novelty or power.

**C11. §1 not-X-but-Y and §5 arguing with no one.** Style wins when the objection is a technical
expectation a reader in the field would hold and the next sentence answers it with a result;
§1 and §5 apply otherwise.
> One might worry that the number of \Bs needed to achieve convergence could be intractably large.

**C12. §2 closers and "This shows ...".** Keep a closer that adds an inference not in the
preceding sentence (W24, W47); §2 applies when it restates.

**C13. §25 writing about the document.** Style wins for one roadmap paragraph at the end of the
introduction and for reader pointers to sections or appendices; §25 applies elsewhere.

**C14. §4 staged run-up.** A transition that names the next object ("We now consider", "Let us
now turn our attention to the bosonic operators.") is allowed once per subsection; §4 applies
to empty announcements.

**C15. §9 stacked qualifiers.** Leave existing pairs such as "could potentially" (X6 forbids
removing hedges anyway); add none. Three or more stacked qualifiers remain a §9 tell.

**C16. §10 hyphenated pairs, §16 sales language, §18 avoiding is/has.** Do not edit
hyphenation of technical compounds (§10 is off in academic mode). *Powerful
discriminant/tagger* is a term of art and stays; other §16 adjectives follow W6. §18 applies to
*serves as* and *features* when a plain *is/has* says the same; *represent* in the sense of
mapping one object onto another is kept.

**C17. §19 bold labels.** Bold run-in labels in existing lists of steps or applications stay
(P2 keeps list structure); §19 applies to bold inside running prose.

Not in conflict: R1, R2 (extended by C2), R6 quotes and ranges, P6, P7, §6 (three real items are
allowed), §21 (LaTeX quotes are used throughout).

## 11. Paragraph checklist

Before accepting a rewritten paragraph in academic mode, check:

1. Sentences mostly 15-35 words, none under 10 unless the original had one (W14).
2. Connective openers near one sentence in eight, no new adjacent pair outside an enumeration,
   no added stance adverb (W16, W17, C4).
3. Voice matches the section: passive for setup and collaboration text, "we" for theory
   choices and results (W9-W11).
4. Each quantitative claim keeps its number, baseline and condition (W39); *significant* is
   statistical near $\sigma$ or CL (W42).
5. `---` only as a pair around an appositive and only if the document already uses it (W26).
6. Citation, figure and equation references unchanged in form and position (W34-W37).
7. The paragraph ends on a fact or one new inference, not on a restatement (W24).
8. No added *crucial, key, robust, novel, comprehensive, powerful*; existing ones kept only
   with a stated dependence (W4, C3, C7).
9. Spelling, *e.g.*/*i.e.* form and serial comma match the surrounding text (W30, W31, W51).
