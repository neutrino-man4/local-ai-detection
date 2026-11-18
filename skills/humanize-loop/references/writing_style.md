# Writing style for physics papers (academic mode)

This file describes how the authors of nine arXiv physics papers actually write. In academic
mode it takes precedence over `humanizer` (§1-§26) and over `loop-overrides.md` (P, A, R, X
codes). Where a rule here contradicts one of those, the "Conflicts" section at the end states
the contradiction, the evidence and the resolution. No P, A or X code is overridden: content
stays fixed, one paragraph stays one paragraph, and no rule here licenses a typo, an invented
fact, an added aside or a removed hedge. The conflicts are with R codes and humanizer patterns.

Every quotation is copied verbatim from the LaTeX source of the paper named in brackets,
including its macros (`\PW`, `\Bs`, `\Eq{}`). A line marked "AI-style (constructed)" is not
from any paper; it shows the pattern to avoid. Rule codes W1-W54 can be cited in the run log
in the same way as P, R and X codes.

## Contents

1. Corpus and method
2. Measured statistics
3. Word choice (W1-W8)
4. Pronouns and voice (W9-W13)
5. Sentence construction (W14-W21)
6. Paragraph construction (W22-W25)
7. Punctuation (W26-W33)
8. Citations, figures and equations in prose (W34-W38)
9. Numbers, uncertainties and significance (W39-W43)
10. Per-section rhetoric (W44-W50)
11. Spelling and register (W51-W54)
12. Conflicts with humanizer and loop-overrides (C1-C17)
13. Paragraph checklist

## 1. Corpus and method

| arXiv ID | Paper (short) | Type | Read closely |
|---|---|---|---|
| 1910.03606 | Brivio et al., global SMEFT fit in the top sector (JHEP) | theory/pheno | Introduction, Global analysis setup, Global top analysis, Conclusions, abstract |
| 1907.03764 | Butter, Plehn, Winterhalder, How to GAN LHC events (SciPost) | ML pheno | in full |
| 1609.07483 | Moult, Necib, Thaler, New angles on energy correlation functions (JHEP) | theory | abstract, Introduction, top-tagging parton-shower results, Quark/gluon section, Conclusions |
| 1809.01140 | Komiske, Metodiev, Thaler, Operational definition of quark and gluon jets (JHEP) | theory/ML | abstract, Introduction, Event generation, Extracting reducibility factors, Conclusions |
| 1712.07124 | Komiske, Metodiev, Thaler, Energy flow polynomials (JHEP) | theory/ML | abstract, Introduction, Event generation, W tagging results, Conclusions |
| 2412.03747 | CMS, model-agnostic dijet anomaly search (2024) | experiment | abstract, Introduction, Anomaly detection methods, Search results, Summary |
| 2102.05044 | Bauer, Freytsis, Nachman, collider physics on quantum computers via EFT (PRL) | theory/QC | main text in full; two supplemental sections |
| 1906.05977 | CMS, multidimensional diboson resonance search (2019) | experiment | abstract, Introduction, Reconstruction and selection, Statistical interpretation, Summary |
| 2102.02770 | Feickert, Nachman, Living review of ML for particle physics (note) | community note | in full |

All nine were read from LaTeX source through the arxiv-latex-mcp server; none needed the PDF.
Three groups are over-represented: the Thaler group (1609, 1712, 1809), the Plehn group (1907,
1910) and CMS (1906, 2412). 2102.02770 is a 1,100-word community note, lighter in register than
the rest; claims that rest on it alone are marked. A few quotations come from passages located
by searching the saved source outside the sections read closely; these are marked "(search)".

**How the statistics were counted.** Script: `scratchpad/style_stats.py`. For each paper it
takes the abstract plus the main text up to the acknowledgements, appendix or bibliography. It
drops comment lines, figure and table environments, footnotes, `\cite{}`, `\label{}` and front
matter; replaces inline math with one token and display math with one token that keeps the
equation's final comma or period; prints reference macros as "Fig. 1", "Eq. 1"; and replaces
any other macro by one token. Sentences are split at `.?!` followed by a capital, with
abbreviations (Fig., Eq., Ref., e.g., i.e., et al., vs.) protected; sentences under 3 words are
discarded. Paragraphs are blank-line blocks. "Connective opener" means the sentence starts with
one of about 80 listed connectives or adverbials (However, Thus, Finally, In addition, Here,
Note that, For example, ...). "Passive" is a heuristic: a form of *be* followed by an -ed word or
a common irregular participle; it overcounts adjectival uses and is comparable only between
papers. Hedges are *may, might, could, likely, suggest, appear, seem, possibly, potential(ly),
approximately, roughly, presumably, perhaps*. At most two macro-definition fragments per paper
survive cleaning; their effect on the averages is below 1%. The statistics cover the whole main
text, which is more than was read closely.

## 2. Measured statistics

Means are unweighted over the nine papers. Pooled over all 2,979 sentences, sentence length has
10th, 25th, 50th, 75th and 90th percentiles of 13, 17, 23, 29 and 36 words.

| Metric | 1910 | 1907 | 1609 | 1809 | 1712 | 2412 | 2102.05 | 1906 | 2102.02 | Mean |
|---|---|---|---|---|---|---|---|---|---|---|
| Words analysed | 10892 | 4491 | 14112 | 8249 | 12199 | 9007 | 3353 | 7044 | 1142 | 7832 |
| Sentences | 531 | 200 | 620 | 312 | 480 | 385 | 128 | 271 | 52 | 331 |
| Sentence length, mean (words) | 20.5 | 22.5 | 22.8 | 26.4 | 25.4 | 23.4 | 26.2 | 26.0 | 22.0 | 23.9 |
| Sentence length, SD | 8.7 | 7.7 | 8.2 | 10.2 | 10.0 | 8.7 | 10.2 | 10.4 | 10.5 | 9.4 |
| Sentences under 10 words (%) | 4.1 | 3.0 | 4.5 | 2.2 | 3.1 | 3.6 | 3.9 | 2.6 | 5.8 | 3.6 |
| Sentences over 40 words (%) | 2.3 | 2.0 | 2.7 | 8.3 | 7.3 | 2.9 | 9.4 | 9.2 | 7.7 | 5.8 |
| Paragraph length, mean (sentences) | 5.0 | 5.1 | 4.2 | 4.2 | 4.1 | 5.1 | 5.6 | 5.2 | 5.2 | 4.9 |
| Connective opener (% of sentences) | 10.7 | 17.0 | 14.4 | 17.9 | 17.7 | 6.0 | 14.1 | 6.6 | 15.4 | 13.3 |
| One connective word + comma (%) | 4.5 | 9.0 | 8.7 | 14.4 | 9.0 | 3.1 | 5.5 | 3.7 | 9.6 | 7.5 |
| "-ly" adverb + comma opener (%) | 2.4 | 5.0 | 3.1 | 5.4 | 4.8 | 1.0 | 1.6 | 1.8 | 1.9 | 3.0 |
| "we" per 1,000 words | 15.1 | 19.8 | 16.4 | 12.0 | 10.9 | 0.7 | 7.2 | 3.3 | 11.4 | 10.7 |
| Sentences with we/our/us (%) | 34 | 50 | 37 | 35 | 28 | 2 | 20 | 10 | 25 | 27 |
| Sentences with passive (%, heuristic) | 19 | 20 | 36 | 39 | 29 | 62 | 44 | 60 | 40 | 39 |
| Semicolons per 1,000 words | 0.55 | 0.00 | 1.49 | 0.36 | 1.15 | 0.11 | 0.30 | 0.28 | 0.00 | 0.47 |
| Colons per 1,000 words | 0.73 | 0.45 | 2.62 | 4.61 | 6.56 | 0.67 | 0.00 | 1.70 | 0.00 | 1.93 |
| Opening parentheses per 1,000 words | 4.0 | 1.3 | 4.3 | 6.4 | 6.2 | 6.9 | 6.9 | 8.5 | 14.0 | 6.5 |
| `---` dashes per 1,000 words | 0.00 | 0.45 | 1.13 | 0.36 | 0.66 | 0.22 | 0.00 | 0.00 | 3.50 | 0.70 |
| Hedge words per 1,000 words | 2.0 | 2.5 | 4.0 | 4.5 | 4.8 | 4.2 | 1.2 | 0.7 | 11.4 | 3.9 |
| Contractions | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

The script reported one `---` for 1906.05977; it is a macro definition, not prose, and is
corrected to 0 above. Section headings are excluded. Of 646 paragraphs, 33 (5%) are a single
prose sentence; another 25 one-sentence blocks are list items. Counts of selected sentence
openers over all nine papers (number of papers in parentheses): Here 28 (5), Finally 27 (7),
Note that 20 (6), Furthermore 17 (7), Therefore 17 (5), Thus 17 (5), In addition 17 (6),
However 15 (7), In particular 14 (5), Similarly 13 (5), For example 10 (6), Additionally 9
(5), Indeed 8 (4), For instance 7 (4), Remarkably 7 (4), Crucially 3 (2), Interestingly 3
(2), Obviously 3 (2), Importantly 2 (2), Notably 0.

## 3. Word choice

**W1. Report results with plain verbs: find, show, see, observe, obtain.** Theory papers attach
them to "we"; collaboration papers use "is found to", "is observed", "are seen". "Demonstrate"
is rare outside 1809.01140 (1.4 per 1,000 words there, under 0.5 elsewhere).
> [1906.05977] We obtain a 20--30\% improvement in sensitivity when using the multi-dimensional fit method, and about a 35--40\% improvement when combining the data sets recorded in 2016 and 2017 relative to the individual results.
> [1910.03606] Looking at the quark chirality, we observe that the bounds on operators with left- and right-handed tops are similar in strength.
> [2412.03747] Good agreement between the data and background-only fits is observed for all methods.
> [1609.07483] Comparing $p_{TJ}=200$ GeV and $p_{TJ}=500$ GeV, we conclude that the behavior of $N_3$ is reasonably robust as a function of $p_{TJ}$ (see \Fig{fig:N3_stability} for higher $p_{TJ}$ values).

AI-style (constructed): "Our results demonstrate a remarkable improvement in sensitivity."
House version: the 1906.05977 sentence above, which gives the size and the baseline.

**W2. One calibrated hedge, placed on the claim it qualifies.** Typical forms: *in principle*,
*likely*, *may*, *appears to*, *can be expected*, and scope clauses that name the condition
under which a result holds. Hedges average 3.9 per 1,000 words; CMS 1906.05977 has 0.7.
> [1907.03764] Given this new piece of the event simulation puzzle through fast neural networks it should in principle be possible to add parton showers, possibly including hadronization, and detector effects to a full machine learning description of LHC events.
> [1712.07124] This agreement gives evidence that the tagging techniques have approached a global bound on the maximum possible discrimination power achievable, at least in the context of parton shower simulations.
> [2412.03747] This is likely because for these signals one of the two jets originates from a single parton, or lacks sufficient jet substructure to be distinguished from a single parton, which makes signal discrimination more challenging.

**W3. Define a term once, then repeat it exactly.** New terms are introduced with `\emph{}`,
"which we call", "known as" or "referred to as", often with the abbreviation in parentheses,
and the same word is used afterwards (agrees with P7). Contested terms get LaTeX scare quotes.
> [1712.07124] Since they trace their lineage to the hadronic energy flow analysis of \Ref{Tkachov:1995kk}, we call these observables the \emph{energy flow polynomials} (\Bs) and we refer to the set of \Bs as the \emph{energy flow basis}.
> [2412.03747] A quantile regression (QR) network is then used to decorrelate the anomaly score of the VAE from the dijet mass. This method is referred to as \vae.
> [1809.01140] Intuitively, we define quark and gluon jets as the ``pure'' categories that emerge from two different jet samples.

**W4. Words on the §12 list are allowed when they state a dependence; never add them.** The
corpus uses *crucial* 14 times (5 papers), *key* as an adjective 16 times (6 papers), *robust*
21 times (3 papers), *enhance/enhancement* 29 times (5 papers, mostly technical), *highlight*
13 times (4 papers), *interplay* 6 times (2 papers), *powerful* 32 times (3 papers, 23 in
1609.07483). In each, the sentence says what depends on what. *Leverage, delve, intricate,
nuance, pivotal, landscape, underscore* never occur; *showcase* occurs twice (1809.01140).
> [1910.03606] Precise predictions are crucial to extract any Lagrangian parameter from LHC rate measurements.
> [1910.03606] The bounds on color-octet operators thus rely on the interplay between contributions of order $\Lambda^{-2}$ and $\Lambda^{-4}$, where the inclusion of both terms is particularly important.
> [1609.07483] Finally, we want to test whether this improvement in quark/gluon discrimination power is robust to grooming.
> [1907.03764] The key to the GAN training is the alternating training of the generator and discriminator networks with their respective loss functions given in Eq.\eqref{eq:GAN1} and Eq.\eqref{eq:GAN2}.

AI-style (constructed): "This crucial, robust framework highlights the key interplay of
operators." Rule: one flagged word per paragraph at most, and only with a stated dependence.

**W5. Prefer *use* to *utilize*; *employ* is collaboration register.** *Utilize* occurs 9 times,
8 of them in the two CMS papers and none in 1910, 1907, 1609, 1809 or 2102.05044. Keep an
existing *utilize* in a CMS-style paper; do not introduce it elsewhere.
> [1906.05977] The \HT{}-triggers utilize a standard jet collection of anti-\kt jets with a distance parameter $R = 0.4$, while the triggers based on the trimmed jet mass operate on AK8 jets.
> [1712.07124] To derive \Eq{eq:genccorr}, we use the Stone-Weierstrass theorem~\cite{stone1948generalized} to expand an arbitrary IRC-safe observable in polynomials of particle energies, and then directly impose IRC safety and particle relabeling invariance.

**W6. Evaluative adjectives sit next to a measured claim.** *Powerful discriminant* is a term
of art for discrimination power; *excellent performance* in 1712.07124 is followed by the three
tagging problems it refers to. Do not add evaluative adjectives in a rewrite (P3).
> [1712.07124] Using linear classification with energy flow polynomials, we achieve excellent performance on three representative jet tagging problems:  quark/gluon discrimination, boosted $W$ tagging, and boosted top tagging.
> [1609.07483] We conclude that soft-dropped $N_3$ is a powerful boosted top tagger that exhibits many experimentally desirable features.

**W7. Ordinary wordiness is normal.** *In order to* appears in every CMS section read and in
2102.02770; *the fact that*, *as a result of*, *it is important to note* also occur (agrees
with P6).
> [2412.03747] These methods therefore assume a particular hypothesis for the mass of the new resonance in order to construct the samples for training.
> [1809.01140] It is important to note, though, that the \pythia fractions are not fully well-defined hadron-level concepts and are shown solely to provide a conceptual and semi-quantitative guideline for the performance of the method.

**W8. *Novel*, *comprehensive*, *first* appear only in abstracts, contribution sentences and
summaries, once each.** *Novel* occurs 6 times (CMS and Thaler group), *comprehensive* 6 times
(three each in 1910.03606 and 2102.02770). Keep an existing one; never add a second in the
same section.
> [1906.05977] A search in an all-jet final state for new massive resonances decaying to \PW{}\PW, \PW{}\PZ, or \PZ{}\PZ boson pairs using a novel analysis method is presented.
> [1910.03606] In this paper we present a comprehensive analysis of the top sector in the framework of SMEFT, based on the data collected mostly during the LHC Run~II.

## 4. Pronouns and voice

**W9. Theory papers say "we" for choices, derivations and results.** 11-20 occurrences per
1,000 words; a quarter to a half of sentences contain we/our/us. "We" appears in methods too.
> [1910.03606] We extract the statistical uncertainties and a leading set of up to $\sim20$ systematic uncertainties for each experiment and simulate a Gaussian shape of the completely exclusive likelihood for statistics and systematics.
> [1907.03764] For both the generator and the discriminator we use a 10-layer MLP with 512 units each, the remaining network parameters are given in Tab.~\ref{tab:details}.

**W10. Collaboration papers are impersonal, with "we" only at decision points.** CMS: 0.7 and
3.3 "we" per 1,000 words, 2-10% of sentences. Abstract and Summary are passive-presentational.
> [1906.05977] To reduce the QCD multijet background, we require the jet mass to be between 55 and 215\GeV.
> [1906.05977] A search is presented for resonances with masses above \BulkGMassMin{}\TeV that decay to \PW{}\PW, \PZ{}\PZ, or \PW{}\PZ boson pairs.
> [2412.03747] The VAE is trained using jets from the CR.

**W11. Simulation and event-generation chains are passive, usually past tense, in every
paper type.** The tense often switches from present to past within the same subsection.
> [1609.07483] Events were generated with \madgraph{2.3.3} \cite{Alwall:2014hca} at the $13$ TeV LHC and showered with \pythia{8.219} \cite{Sjostrand:2006za,Sjostrand:2007gs} with underlying event and hadronization implemented with the default settings.
> [1712.07124] For each type of sample, 200k jets were generated.
> [1809.01140] All jets were required to have $p_T\in[500,550]$ GeV and rapidity $|y|<2.5$.

**W12. Tense.** Present for what the paper does, what a figure shows and what holds in
general; present perfect for the opening of conclusions ("We have shown"); simple past for
what was done in the study when recapping it.
> [1907.03764] We have shown that it is possible to GAN the full phase space structure of a realistic LHC process, namely top pair production all the way down to the kinematics of the six top decay jets.
> [1809.01140] To illustrate the power of the Operational Definition, we tested it in the realistic context of $Z$+jet and dijet processes.

**W13. "One", "us" and the reader.** Generic "one" occurs in 6 papers (up to 3 per 1,000 words
in 2102.05044), usually with *can*, *might*, *needs*. "Us" appears as the object of *allow*,
*require*, *leave*. "We refer the reader to" and "To guide the reader" occur; "you" only in the
community note 2102.02770. Do not introduce "you" in a research paper.
> [2102.05044] To evaluate the matrix element on a quantum computer one first needs to define circuits that perform time evolution of the system, as well as circuits that can create and measure the ground and exited states of the theory.
> [1910.03606] In particular, the \textsc{SFitter} technology allows us to easily study correlations between Wilson coefficients and to compare the impact of theoretical and experimental uncertainties.
> [1609.07483] For detailed discussions of these issues, we refer the reader to \Refs{Gallicchio:2011xc,Gallicchio:2011xq,Gallicchio:2012ez,Larkoski:2013eya,Larkoski:2014pca,Badger:2016bpw}, as well as to studies in data \cite{CMS:2013wea,CMS:2013kfa,Aad:2014gea,ATLAS-CONF-2016-034}.

## 5. Sentence construction

**W14. Length: median 23 words, middle half 17-29, and almost no short sentences.** About 4%
of sentences have fewer than 10 words; the coefficient of variation is 0.34-0.48. Variation
comes from 15-35-word sentences, with long ones (over 40 words, 6%) carrying lists,
conditions or a result plus its baseline. A rewrite must not add fragments or punchy
one-liners to "vary rhythm".
> [1712.07124] Naively, \Eq{eq:introefp} has complexity $\mathcal O(M^N)$ due to the $N$ nested sums over $M$ particles.

AI-style (constructed): "The result is clear. Linear methods suffice." House version:
> [1712.07124] Crucially, linear methods were sufficient to achieve good performance with the \Bs.

**W15. Subject first is the default.** "The" is the most frequent opener in every paper (13-18%
of sentences in the theory papers, 33% and 40% in the CMS papers). The next
most common openers frame the sentence: "In Fig.~X we show", "In this paper, we", "For the",
"For each", "To", "Since", "As".
> [1910.03606] In Fig.~\ref{fig:Global} we show the profile likelihoods for each of the top-related effective operators.
> [2412.03747] For each method, the selection efficiency on the benchmark signal models is evaluated.

**W16. Logical connectives open about one sentence in eight; contrast goes mid-sentence.**
About 13% of sentences open with a connective (6-7% in the CMS papers, 11-18% elsewhere).
The common ones are *Finally, Thus, Therefore, In addition, Furthermore, Similarly, In
particular, For example, Here, Note that*. Sentence-initial *However* is rare (15 in 2,979
sentences); contrast is more often carried by a mid-sentence *however* or *though*. Adjacent
sentences both open with a connective 53 times in about 2,330 adjacent pairs, 17 of them in
enumerations (*First ... Next ... Finally*, *On the one hand ... On the other hand*); that is
roughly what independent placement at 13% would give, so the corpus neither seeks nor avoids
it. A rewrite should not create a new adjacent pair outside an enumeration (P8).
> [1609.07483] For small values of $\beta$, however, one is highly sensitive to nonperturbative effects, which must be modeled or extracted from data.
> [1712.07124] In practice, though, we find that the required set of $\mathcal G$ needed for convergence is rather reasonable in a variety of jet contexts.
> [1906.05977] Furthermore, using the \nsubjDDT variable reduces the dependency of \mJ\ on \mjj, leading to smoothly falling distributions in the jet mass as shown in Fig.~\ref{fig:roc} (\cmsRight).
> [2412.03747] It therefore learns how to perform this compression and decompression on QCD background jets, but might fail in performing this task as well on anomalous jets not present in the training sample.

**W17. Stance adverbs are rare and must carry a reason.** *Crucially, Remarkably,
Interestingly, Importantly, Obviously, Surprisingly* open 19 of 2,979 sentences (0.6%), all in
the Thaler and Plehn groups; CMS and 2102.05044 have none. Each is followed by a claim that is
in fact surprising or necessary, stated in the same sentence. Keep an existing one; never add
one (see C4).
> [1809.01140] Crucially, this worked even for observables that do not exhibit quark/gluon mutually irreducibility, as long as the observable used to extract the fractions does.
> [1712.07124] Remarkably, linear classification with \Bs performs comparably to multivariate machine learning techniques, such as jet images with convolutional neural networks (CNNs)~\cite{Cogan:2014oua,deOliveira:2015xxd,Barnard:2016qma,Komiske:2016rsd,Kasieczka:2017nvn} or dense neural networks (DNNs) with a complete set of $N$-subjettiness observables~\cite{Datta:2017rhs}.

**W18. Participial and framing openers are normal.** About 4% of sentences start with an
-ing word or *Given/Taken*; most state a precondition for the main clause.
> [1609.07483] Having understood the power counting of $\Nobsnobeta{3}$ on groomed jets, we now study its behavior in parton shower generators, comparing $\Nobsnobeta{3}$ with both $\Nsubnobeta{3,2}$ and the simplified version of $\Dobsnobeta{3}$ defined in \Eq{eq:D3_simp_def}.
> [1609.07483] Given the Casimir scaling limit of single-emission observables, a promising approach for improving quark/gluon discrimination is to design observables that are directly sensitive to multiple emissions within the jet, even at lowest order.

**W19. A trailing participle clause states a consequence or mechanism, not a value judgment.**
> [1906.05977] Each of the two bosons decays into one large-radius jet, yielding dijet final states.
> [2412.03747] Therefore, the highest and lowest mass regions in each set of windows are used only as sidebands, resulting in 12 total SRs in which the training procedure is performed.

AI-style (counter-example found in the corpus, 2412.03747): "...an additional anomaly-detection-based
analysis from the ATLAS Collaboration has appeared~\cite{ATLAS_anomaly2}, emphasizing the
importance and novelty of the methods developed in the present work." The tail evaluates rather
than informs; this form occurs once in the sections read.

**W20. Relative clauses with *which* and *where* carry definitions and regimes.** *Which* is
used both with and without a comma (restrictive *which* is common); do not convert *which* to
*that*. *Where* follows displayed equations and introduces kinematic regimes.
> [1712.07124] We introduce the energy flow polynomials: a complete set of jet substructure observables which form a discrete linear basis for all infrared- and collinear-safe observables.
> [1609.07483] At lower top efficiencies, where there are well-resolved jets, $N_3$ and $\Nsubnobeta{3,2}$ exhibit similar discrimination power, but at higher efficiencies, where there are not well-resolved jets, the structure of $N_3$ leads to considerably improved performance.

**W21. Parentheses carry glosses, abbreviations, alternative values and cross-references.**
6.5 per 1,000 words on average (1.3 in 1907.03764, 14 in 2102.02770). Whole parenthetical
sentences occur.
> [2102.05044] In principle, to have access to the full dynamics of the Large Hadron Collinder (LHC), one would need to describe the energy range between $\ord(\SI{10}{\MeV})$ (the smallest resolvable transverse momentum between hadrons) and \SI{7}{\TeV} (the beam energy of the LHC).
> [2102.05044] (For work on simulating EFTs not related to collider physics, see~\cite{Dumitrescu:2018njn,Lu:2018pjk,Cervia:2019res,Roggero:2019myu,Cervia:2020fkk,Stetina:2020abi}).

## 6. Paragraph construction

**W22. Four to six sentences.** Mean 4.9 sentences (4.1-5.6 by paper). Single-sentence prose
paragraphs are 5% of paragraphs; do not create one by splitting (P2 forbids it anyway).

**W23. Open with the object or the step, not with a framing claim.** Paragraphs open with the
thing being studied ("For our global LHC analysis we use..."), a figure ("In Fig.~X we show"),
or a transition that names the next task ("We now consider", "We begin by").
> [1910.03606] For our global LHC analysis we use the \textsc{SFitter} framework~\cite{Lafaye:2007vs,Lafaye:2009vr}, which focuses on a proper treatment of uncertainties in a conservative frequentist approach.
> [1609.07483] We begin by verifying the power-counting argument of \Eq{eq:pc_qvsg}, which suggested that $\ecfvarnobeta{2}{3}$ and $\ecfnobeta{3}$ should be highly correlated with $U_1 = C_1 = \ecfnobeta{2}$.

**W24. Close on the last fact, or on one inference the paragraph has not yet stated.** About
13% of paragraph-final sentences start with *This/These/Thus/Therefore/Overall/We conclude*
(10% of all sentences do). In the samples checked, such closers add an inference (a cause, a
consequence, a physics reading) rather than restating. Many paragraphs end on a number.
> [1809.01140] The \pythia-labeled quark fraction was 86.3\% for the $Z$+jet sample and 49.8\% for the dijet sample.
> [2102.05044] The quantum computer reproduces the simulated result to about \SI{5}{\percent} accuracy.
> [1712.07124] This illustrates that nonlinear combinations of the $N$-subjettiness observables are crucial for extracting the full physics information.

AI-style (constructed): "...reaches 5% accuracy. This highlights the immense potential of
quantum computing for collider physics." Cut the second sentence; end on the number.

**W25. Caveats follow results inside the same paragraph.** The authors attach the caveat
directly to the result it limits, often with *though*, *again* or *it should be noted*.
> [1809.01140] Again, we caution that the \pythia fractions solely provide a heuristic to demonstrate the performance of the method and should not be taken as fundamental to quark and gluon jets.
> [1712.07124] It should be noted that the linear classifier is not trained specifically for the low signal efficiency region and it may be possible that choosing a different hyperplane could boost performance there.

## 7. Punctuation

**W26. `---` is a paired bracket around an appositive, at about 0.7 per 1,000 words.** Three
papers (1910.03606, 2102.05044, 1906.05977) use none. Of 35 `---` marks counted, 32 come in
pairs enclosing a list or a definition; the rest append a remark. Spacing follows the paper:
unspaced in the Thaler group and CMS 2412.03747, spaced in 1907.03764 and 2102.02770. No paper
uses `--` or a Unicode dash as a sentence dash. Never use `---` to join two independent clauses.
> [1609.07483] We presented a number of case studies of relevance to the jet substructure community---boosted top tagging, boosted $W/Z/H$ tagging, and quark/gluon discrimination---demonstrating the power of power-counting techniques to design discriminants for specific purposes.
> [2412.03747] A collection of complementary anomaly detection methods---based on unsupervised, weakly supervised, and semisupervised algorithms---are used in order to maximize the sensitivity to unknown new physics signatures.
> [1907.03764] They perform a dimensional reduction of the input data --- often an image --- to create a latent representation.
> [2102.02770] The fact that a paper is listed in the review does not endorse or validate its content --- that is for the community (and for peer-review) to decide.

**W27. `--` joins numeric ranges and two-name compounds.** Ranges: `20--30\%`, `1.8--6\TeV`,
`2016--2018`. Names: `Randall--Sundrum`, `Cambridge--Aachen`, `Suzuki--Trotter`,
`top--anti-top`. Ranges inside math use a hyphen (`0.35 - 2 \tev`, `$\approx 1-2$~TeV`, 1910.03606).
> [1906.05977] We consider the bulk scenario of the Randall--Sundrum (RS) model with warped extra dimensions~\cite{Randall:1999ee,Randall:1999vf,Agashe:2007zd, Fitzpatrick:2007qr, Antipin:2007pi}, where the spin-2 bulk graviton has an enhanced branching fraction to massive particles, and the heavy vector triplet (HVT) framework~\cite{Pappadopulo:2014qza}, which serves as a template that reproduces a large class of explicit models predicting \mbox{spin-1} resonances.

**W28. Semicolons join a statement to its pointer, consequence or deferral.** 0.47 per 1,000
words; two papers have none. Recurrent shapes: "...; see \Refs{} for detailed studies",
"...; this illustrates ...", "...; we leave such studies to future work", and items of a long
list after a colon.
> [1609.07483] This in turn leads to rather large uncertainties in the predicted quark/gluon efficiencies; see \Refs{Larkoski:2014pca,Badger:2016bpw} for detailed studies.
> [1809.01140] One feature worth noting is that the lower bound is accurately extracted by every observable; it is the upper bound that is more difficult to saturate with a generic observable.

**W29. Colons introduce lists, displayed equations and explanations.** 2 per 1,000 words on
average, 5-6.5 in 1809.01140 and 1712.07124, 0 in 2102.05044 and 2102.02770.
> [1809.01140] Nonetheless, jets can be made perfectly well-defined: any hadron-level algorithm for finding jets that is infrared and collinear (IRC) safe provides an operational jet definition that can be compared to perturbative predictions.
> [1712.07124] We consider three representative jet tagging problems: quark/gluon discrimination, boosted $W$ tagging, and boosted top tagging.

**W30. Serial comma.** Checked by hand among regex candidates: 1609, 1809, 1712, 1907, 2412,
1906 and 2102.02770 use it in every list found (1907.03764 has one exception); 1910.03606 mixes
(about 6 with, 6 without); 2102.05044 has one list, without. Use it unless the paragraph or
document already omits it.
> [1906.05977] This method uses local shape information of charged pileup, event pileup properties, and tracking information in order to rescale the four-momentum of each neutral and charged PF candidate with a weight that describes the likelihood that each particle originates from a pileup interaction.

**W31. *e.g.* and *i.e.* follow the document.** The Thaler group writes `e.g.\ ` and `i.e.\ `
with no comma, inside parentheses or after a comma (11 instances of each). 1910.03606 writes
`\emph{i.e.},` and `\emph{e.g.},` with a comma but also `\ie` without. CMS uses the `\ie`
macro. 2102.02770 writes `(e.g. Generative...` with a plain space.
> [1809.01140] Hadronization and multiple parton interactions (i.e.\ underlying event) were included and a parton-level $p_T$ cut of $\SI{400}{GeV}$ was applied.
> [1910.03606] This is especially important in phase space regions where SMEFT contributions can be large, \emph{e.g.}, in tails of kinematic distributions.

**W32. Quotation marks are LaTeX quotes; keep any irregular closings.** Scare quotes mark
contested labels (``quark''), coined verbs (``demix'') and slang (``black box''). CMS source
mixes ``groomed" with a straight closing quote; 2412.03747 has `prior' and 'generic \quak'.
Do not normalise these (P1).

**W33. No contractions, no exclamation marks.** Zero of each in all nine main texts.

## 8. Citations, figures and equations in prose

**W34. A citation attaches with `~\cite{}` to the word or claim it supports, before the
punctuation.** Multiple keys go in one `\cite{}`. 1609.07483 uses a plain space before `\cite`
(91 times); keep whichever spacing the document uses.
> [2412.03747] One of the most generic searches for new physics at particle colliders is therefore a search for heavy resonances decaying into two jets~\cite{ua1dijet,ua2dijet,cdfdijet,d0dijet,atlas1dijet,atlas2dijet,cms1dijet,cms2dijet}.

**W35. A citation used as a noun is "Ref.~\cite{}" or "Refs.~\cite{}" in JHEP, SciPost and CMS
papers, and a bare `in~\cite{}` / `see~\cite{}` in the PRL letter.** The Thaler group uses
`\Ref{}` and `\Refs{}` macros (83 uses).
> [1907.03764] One open question is why the GAN setup of Ref.~\cite{dutch} does not properly work and is replaced by a variational autoencoder with a density information buffer.
> [2102.05044] For $\bar{\omega} = 1$, as is the case for a single lattice site with $\omega = 1$, corresponding to a single harmonic oscillator, \cref{phiMax} reproduces the empirical numerical values obtained in~\cite{Klco:2018zqz}.

**W36. Figures, tables and sections.** Mid-sentence: `Fig.~\ref{}`, `Tab.~\ref{}`,
`Sec.~\ref{}` in JHEP/SciPost papers; CMS spells out `Section~\ref{}` and `Table~\ref{}`.
Sentence-initially, CMS 1906.05977 spells out `Figure~\ref{}` while 2412.03747 and the Thaler
group (`\Fig{}`, `\Sec{}`) keep the abbreviation. Theory papers prefer "In Fig.~X we show";
CMS prefers "Figure~X shows". A pointer may be appended after a comma: ", see Fig.~X".
> [1906.05977] Figure~\ref{fig:nsubj} shows a notable deviation in the shape of the \nsubjDDT distribution between data and simulation.
> [1910.03606] Non-trivial correlations as between $C_{tG}$, $C_{\phi Q}^3$, and $C_{Qq}^{3,1}$ vanish once we include the full data set, see Fig.~\ref{fig:Correlations}.

**W37. Equations are part of the sentence.** The lead-in runs straight into the display
("is given by", "can be written as", "takes the form:"); the display ends with `\,.` or `\,,`
inside the math; the text after a comma continues in lower case with *where*. References are
`Eq.~\eqref{}` (1910), `Eq.\eqref{}` (1907), `\Eq{}` (Thaler group), `\cref{}` (2102.05044).
> [2102.05044] The physical volume of the lattice is determined by the distance between adjacent lattice points $\var{x}$ in each direction and is given by
> [2102.05044] where $n_\phi$ denotes the dimensionality of the Hilbert space for a given lattice point, $N$ is the total number of lattice points in each spatial direction, and $d$ represents the number of spatial dimensions.

**W38. Technical asides go in footnotes in theory papers.** 1609.07483 has 25 main-text
footnotes and 1712.07124 has 10; the CMS papers and 2102.05044 have none. Footnotes hold
caveats, timing figures and jokes; do not move footnote content into running text.
> [1609.07483] For a jet with $n_J$ particles, the computational cost of $\Uobsnobeta{i}$ scales like $n_J^{i+1}$.

## 9. Numbers, uncertainties and significance

**W39. Every quantitative claim names its baseline and its condition.**
> [1906.05977] This method yields an improvement in sensitivity of up to 30\% relative to previous search methods.
> [2412.03747] The largest improvements are seen for the 6+6 prong \GtoHH signal, in which anomaly detection methods are found to reduce the cross section needed for a $5\sigma$ discovery by a factor of 6.4 (2.9) as compared to the inclusive (3-prong) selection.

AI-style (constructed): "The method significantly improves sensitivity." House version: the
1906.05977 sentence above.

**W40. Precision is stated with *about*, *up to*, *at the order of*, *within*, $\mathcal O()$.**
> [1907.03764] As we can see, momentum conservation at the GAN level is satisfied at the order of 2\%.
> [1809.01140] The count observables and trained models agree within several statistical uncertainties of one another and the \pythia fractions, in many cases achieving $\mathcal O(1\%)$ fidelity.
> [1906.05977] The extracted \PV{}+jets cross sections are found to be compatible with the SM expectations within one standard deviation of the post-fit uncertainties.

**W41. Alternative values go in parentheses in the same order as their labels; lists of values
end with *respectively*.**
> [2412.03747] The largest excesses of events seen by the \cathode, \cathodeb, \quak, and \vae methods had local significances of 2.2, 2.9, 2.6, and 2.3$\sigma$ at resonance masses of 2.3, 2.3, 4.7, and 4.9\TeV, respectively.

**W42. Statistical significance has a fixed formula; *significantly* as an intensifier needs a
comparison.** In statistical results the experiments write "No significant excess ... is
observed", give local significances in $\sigma$ and limits at 95\% CL. All nine papers also use
*significant(ly)* non-statistically (about 40 times), always attached to a comparison or a
size: *significantly larger feature sets*, *significantly smaller quantum resources*. The
theory papers never use the statistical sense. In a paragraph that reports $\sigma$ or CL
values, use *significant* only in the statistical sense (see C6).
> [1906.05977] No significant excess over the background estimation is observed. Upper limits on the production cross section at 95\% confidence level (\CL) are set.
> [2102.05044] We have argued that the dynamics of a low energy EFT can be simulated with significantly smaller quantum resources than the dynamics of the corresponding full theory.

**W43. Exclusion and limit sentences follow a template.**
> [1906.05977] For the HVT model~B, we exclude at 95\% \CL\ \PWpr and \PZpr spin-1 resonances with masses below \MassExclWPr and \MassExclZPr{}\TeV, respectively.

## 10. Per-section rhetoric

**W44. Introductions open on physics, not on attention.** First sentences state what the
field does or an established fact; prior work comes with citation lists; the gap is stated as
what has not been done. "In recent years" appears mid-paragraph twice (1609.07483, 2102.02770),
never as an opener.
> [1712.07124] Jet substructure is the analysis of radiation patterns and particle distributions within the collimated sprays of particles (jets) emerging from high-energy collisions~\cite{Seymour:1991cb,Seymour:1993mx,Butterworth:2002tt,Butterworth:2007ke,Butterworth:2008iy}.
> [2102.05044] It is well known that quantum computers can in principle simulate the time evolution of quantum field theories~\cite{Jordan:2011ne}.
> [1809.01140] Despite decades of using the notions of ``quark'' and ``gluon'' jets \cite{Nilles:1980ys,Jones:1988ay,Fodor:1989ir,Jones:1990rz,Lonnblad:1990qp,Pumplin:1991kc,Gallicchio:2011xq,Gallicchio:2012ez, Bhattacherjee:2015psa,FerreiradeLima:2016gcz,Bhattacherjee:2016bpy,Komiske:2016rsd,Davighi:2017hok,Cheng:2017rdo,Sakaki:2018opq}, a precise and practical hadron-level definition of jet flavor has not been formulated.

**W45. The contribution is one sentence: "In this paper(,) we" + present-tense verb + what.**
Eight of nine papers use it; the CMS papers write "In this analysis, we present" (2412.03747)
and "In this analysis, we test" (1906.05977). Positioning against
other groups credits them by name.
> [2102.05044] In this paper we show that this is indeed possible by using effective field theories (EFTs) which have been designed to reproduce the desired long distance physics.
> [1910.03606] The specific error treatment, a detailed analysis of several physics aspects not considered before, as well as a slightly different data set complement other state-of-the-art analyses, such as that of the \textsc{SMEFiT} collaboration~\cite{Hartland:2019bjb}.

**W46. The introduction ends with a roadmap.** Seven papers have one ("The paper is organized
as follows.", "The remainder of this paper is organized as follows.", "We now give a brief
summary of the rest of this paper."), one sentence per section; the PRL letter has none.
> [2412.03747] The paper is organized as follows.

**W47. Results paragraphs run figure, observation, interpretation.**
> [1712.07124] For operating points with $\varepsilon_s\gtrsim0.5$, all methods except the linear $N$-subjettiness classifier show essentially the same performance.
> [1910.03606] This shows the impact of the $t\bar{t}Z$ cross section measurements in the global fit.

**W48. Limitations are stated as plain facts about the method.**
> [1907.03764] The main limitation of the GAN approach is that statistical uncertainties in poorly populated tails of distributions in the training data appear as systematic uncertainties in the same phase space regions for the generated high-statistics samples.
> [1609.07483] One aspect of jet substructure that has not been studied here is the correlations between discriminants.
> [2412.03747] The anomaly detection methods were shown to enhance the sensitivity by larger factors, and on a much wider class of models, than traditional cutoff-based substructure selections, but fell short of the sensitivity of a dedicated model-specific search.

**W49. Future work: "We leave ... to future work" and "It would be interesting to ...".**
"We leave" occurs 15 times in 5 papers; "It would be interesting" 8 times, 7 of them in
1609.07483.
> [2102.05044] In this letter, we work at fixed lattice size and we leave the detailed investigation of these issues to future work.
> [1609.07483] It would be interesting to see whether these parton shower predictions remain true in LHC data.

**W50. Conclusions open by recapping in present perfect or past, restate the main numbers,
and end on the last finding or one concrete outlook.** Opening forms: "We have presented"
(1910), "We have shown" (1907), "In this paper, we provided" (1809), "In this paper, we have
introduced" (1712), "To summarize, we have presented" (2412), "A search is presented" (1906),
"In conclusion," (2102.05044), "This paper has described" (2102.02770). Endings: a finding
(1910), numbers (1906, 2102.05044), a hedged outlook (1609, 1809, 1712), a significance claim
(2412), a hope (2102.02770).
> [1910.03606] For all operators we find that the theory uncertainties linking measurements to Wilson coefficients in the Lagrangian are becoming the limiting factor in interpreting LHC results.
> [2102.05044] Using only 2 qubits per lattice we obtain results within \SI{10}{\percent} of the analytical result, and by using noise-mitigation techniques, uncertainties due to running on present-day hardware can be reduced to about \SI{5}{\percent}.

## 11. Spelling and register

**W51. Spelling follows the paper.** Eight papers use American spelling (behavior, color,
flavor, center, modeling or modeled). CMS 1906.05977 uses -ize with British -our, -ll- and
-re (behaviour, modelling 7, modelled 8, labelling 4, centre 2, focusses). 1907.03764 and
1910.03606 are American with *labelled* and *modelled/modelling*. Never change spelling in a
rewrite; new words follow the paragraph's existing variety.

**W52. Register is formal but personal in theory papers.** First-person opinion appears in
theory papers ("we suspect", "We are particularly interested", "it is gratifying") and
never in CMS papers.
> [1609.07483] We find this much flatter behavior of the discrimination power with respect to $\beta$ to be one of the most interesting features of these observables, suggestive that multiple soft emissions are just as important as hard collinear emissions for discriminating quarks from gluons.

**W53. Humour and informal words are confined to footnotes and a few established voices.**
Examples: the "to GAN" footnote (1907), the acronym footnote (1712), ``\pythia{}-\herwig{}
sandwich'' (1609), "nicely" and "come in handy" (1907). Keep the author's own; never add (P3).
> [1907.03764] From `to GAN', in close analogy to the verbs taylor, google, and sommerfeld.

**W54. Errors in the corpus are not style.** The sources contain typos ("Collinder",
"quantitive", "a underlying", "bigger batch sizes leads"). X1 stands: never imitate them, and
P1 stands: do not fix them in a humanize pass unless asked.

## 12. Conflicts with humanizer and loop-overrides

Each entry: the rule contradicted, the evidence, the resolution. "Papers win" means the W
rule applies in academic mode and the other rule does not.

**C1. §8 dashes (and R6 "`---` used as a dash follows §8").** §8 removes all em dashes unless a
sample uses them. Evidence: 6 of 9 papers use `---`, mean 0.7 per 1,000 words, mostly paired
around an appositive list (W26). Resolution: papers win, within limits. Keep existing `---`
pairs that bracket a list or definition. Replace a `---` that joins two clauses, and any
dash beyond about 1 per 1,000 words in the document, as §8 says. Add no dash to a paper whose
source has none. `--` in ranges and two-name compounds is never a dash (W27).

**C2. §11 passive voice.** §11 prefers active voice. Evidence: passive sentences are 19-62% of
the total (heuristic), highest in CMS; simulation chains are passive in every paper (W11); CMS
abstracts and summaries are passive by convention (W10). R2 already overrides §11 for methods.
Resolution: papers win, beyond R2. Do not convert passive to active in methods, event
generation, selection, collaboration abstracts or summaries, or "is found to" results. §11
applies only where a theory paper's own "we" would make an authors' choice clearer.

**C3. §12 AI vocabulary, and R5's narrow list.** §12 treats *crucial, key, robust, enhance,
highlight, interplay, additionally* as tells wherever they appear; R5 keeps *key* only for
cryptographic use. Evidence: W4 counts; *key* as an adjective is used figuratively in 6 papers
("a key ingredient", "a key concern"). Resolution: papers win for single instances that state
a dependence. Remove a flagged word only when two or more cluster in one paragraph, or when
the sentence states no dependence. Never introduce one.

**C4. R3 sentence-initial adverbs and connectives.** R3 bans openers such as "Crucially,",
"Importantly,", "Notably,", "Interestingly,", "Additionally,", "Furthermore,". Evidence: 13% of
sentences open with a connective; *Furthermore* 17 times in 7 papers, *Additionally* 9 in 5,
*Crucially* 3 in 2, *Interestingly* 3 in 2, *Importantly* 2 in 2, *Notably* 0 (W16, W17).
Resolution: split. (a) Logical connectives (*However, Therefore, Thus, Finally, In addition,
Furthermore, Additionally, Similarly, For example, In particular*): papers win; keep them, at
most one per paragraph for *Furthermore/Additionally*, and no new adjacent pair outside an
enumeration (W16).
(b) Stance adverbs (*Crucially, Importantly, Interestingly, Notably, Remarkably*): R3 holds
for anything the rewrite adds; an existing one is kept if the sentence states why it matters,
otherwise R3 applies. R3's preference for subject-first sentences agrees with W15.

**C5. R3 vocabulary list.** R3 avoids *endeavour, genuinely* and similar. Evidence: "endeavor"
once and "genuine" in a technical sense (a true W or Z decay) twice.
> [1910.03606] (search) Charge asymmetries play an important role in this endeavor, since they probe chiral structures that are not accessible in cross sections or other charge-symmetric observables~\cite{Rosello:2015sck}.
> [1906.05977] (search) The resonant background is defined as all SM processes containing at least one jet originating from a genuine \PW\ or \PZ\ boson decay.
Resolution: R3 holds for introduced words; technical *genuine* is kept.

**C6. R4 "Significant without statistics".** R4 reserves *significant* for statistical
significance. Evidence: all nine papers use *significant(ly)* non-statistically (W42), including
both CMS searches. Resolution: papers win partly. *Significantly* is allowed when it modifies
a stated comparison (larger than X, smaller than Y). In a paragraph that reports $\sigma$, CL
or excesses, R4 applies. A bare "significant improvement" with no comparison stays an R4 tell.

**C7. R4 inflated contribution, plays-a-role and significance tails.** Evidence:
*comprehensive* three times in 1910.03606 (abstract, introduction, conclusions), "novel" (6 uses), "play a ... role" 8 times in 4 papers,
"pave(s) the way" in 1910.03606 and 1809.01140, "shed light" in 1910.03606 and 1609.07483, and a
CMS summary ending on "will play a crucial role in maximizing the discovery potential of LHC
data". Resolution: R4 holds for anything the rewrite adds. An existing instance is kept when
the same sentence gives the mechanism, as in
> [1910.03606] Observables combining top production and decay play a special role in the SMEFT interpretation, because they probe features of operators not accessible in top production alone~\cite{AguilarSaavedra:2010zi,Aguilar-Saavedra:2017nik,deBeurs:2018pvs,Neumann:2019kvk}.
and otherwise R4 applies.

**C8. R4 summary echo.** R4 says end when the content ends and cut "In summary, ...". Evidence:
conclusions in all nine papers open with a recap (W50), and 2412.03747 opens with "To
summarize, we have presented". Resolution: papers win for the first sentence of a conclusions
section; R4 holds for summary echoes at the end of a paragraph or section.

**C9. R4 gap rhetoric and "In recent years".** Evidence: "remain uncovered" (2412.03747),
"has not been formulated" (1809.01140), "in recent years" twice mid-paragraph. Resolution: a
gap stated with citations and a concrete missing item is house style (W44); R4 applies to
gap phrases without citations and to "In recent years" as an opener.

**C10. §15 shallow -ing phrases.** §15 lists *highlighting, emphasizing, ensuring, reflecting*.
Evidence: trailing participles are frequent and usually carry a consequence (W19), including
"highlighting that the higher $d$ \Bs carry essential information for linear classification"
(1712.07124). Resolution: keep -ing tails that state a consequence or mechanism, even with a
listed verb; §15 applies to tails that evaluate (importance, novelty, power).

**C11. §1 not-X-but-Y and §5 arguing with no one.** Evidence: the authors raise an expectation
a reader in the field might hold, then answer it with evidence.
> [1712.07124] One might worry that the number of \Bs needed to achieve convergence could be intractably large.
> [1809.01140] No longer is the output of a neural network viewed as an arbitrary quantity used only for discrimination, but rather as a robust approximation to the likelihood ratio, which turns out also to be optimal for extracting categories from the data.
Resolution: papers win when the objection is a technical expectation answered by a result in
the next sentence (consistent with §5's own exception). §1 and §5 apply otherwise.

**C12. §2 closers and §13 "This shows ...".** §2 flags a sentence after a result that names
what it showed. Evidence: 13% of paragraph-final sentences are *This/Thus/Therefore* inferences
(W24, W47). Resolution: keep a closer that adds an inference not in the preceding sentence;
§2 applies when it restates.

**C13. §25 writing about the document.** §25 flags descriptions of the document's
organisation. Evidence: roadmap paragraphs in 7 of 9 papers (W46); "Because this section is
rather technical, it can be omitted on a first reading" (1712.07124). Resolution: papers win
for one roadmap paragraph at the end of the introduction and for reader pointers to sections
or appendices; §25 applies elsewhere.

**C14. §4 staged run-up.** §4 flags "now let's look at"-type openers. Evidence: "Let us now
turn our attention to the bosonic operators." (1910.03606; "Let us" occurs twice, both in this
paper), "We now consider", "We begin by", "To begin with,". Resolution: a transition that names
the next object is allowed once per subsection; §4 applies to empty announcements.

**C15. §9 stacked qualifiers.** §9 lists "could potentially". Evidence: "$\ecfvarnobeta{v}{n}$-based
slicing could potentially be valuable in regimes where axes are inappropriate or cumbersome"
(1609.07483, outlook). X6 forbids removing hedges anyway. Resolution: leave existing pairs;
add none; three or more stacked qualifiers remain a §9 tell.

**C16. §10 hyphenated pairs, §16 sales language, §18 avoiding is/has.** Evidence: predicative
"well-defined" and "experimentally-accessible quantities" (1809.01140); *powerful* 32 times,
"rich analytic structure" (1712.07124), "impressive performance" (1907.03764); "which serves as
a template" (1906.05977), "features a detailed error treatment" (1910.03606 abstract).
Resolution: do not edit hyphenation of technical compounds (§10 off in academic mode).
*Powerful discriminant/tagger* is a term of art and stays; other §16 adjectives follow W6. §18
applies to *serves as* and *features* when a plain *is/has* says the same; *represent* mapping
one object onto another is kept.

**C17. §19 bold labels.** Evidence: bold run-in labels in an itemised overview
(`\item \textbf{Boosted Top Tagging} (\Sec{sec:tops}):`, 1609.07483) and in a numbered
procedure (`\item {\bf Histograms}:`, 1809.01140). Resolution: bold labels in existing lists of
steps or applications stay (P2 already keeps list structure); §19 applies to bold inside
running prose.

Not in conflict: R1, R2 (extended by C2), R6 quotes and ranges, P6, P7, §6 (three real items
are common and allowed), §21 (LaTeX quotes are used throughout).

## 13. Paragraph checklist

Before accepting a rewritten paragraph in academic mode, check:

1. Sentences mostly 15-35 words, none under 10 unless the original had one (W14).
2. Connective openers near the document's rate (about one sentence in eight), no new
   adjacent pair outside an enumeration, no added stance adverb (W16, W17, C4).
3. Voice matches the section: passive for setup and collaboration text, "we" for theory
   choices and results (W9-W11).
4. Each quantitative claim keeps its number, baseline and condition (W39); *significant* is
   statistical near $\sigma$ or CL (W42).
5. `---` only as a pair around an appositive and only if the document already uses it (W26).
6. Citation, figure and equation references unchanged in form and position (W34-W37).
7. The paragraph ends on a fact or one new inference, not on a restatement (W24).
8. No added *crucial, key, robust, novel, comprehensive, powerful*; existing ones kept only
   with a stated dependence (W4, C3, C7).
9. Spelling, `e.g.`/`i.e.` form and serial comma match the surrounding text (W30, W31, W51).
