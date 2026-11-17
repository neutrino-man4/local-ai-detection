# Mesmer-4B on the Ryzen AI NPU: audit and rewrite plan

Date: 2026-11-17. Scope: planning only. Nothing was implemented, the Mesmer model was not
run in any form, nothing was compiled for the NPU, and no existing file was changed.

> Write-up status: complete (the file was saved section by section during the audit; the
> line "END OF DOCUMENT" at the bottom marks a finished write-up). The scratch scripts listed
> in Appendix A can be re-run to reproduce every synthetic result.

Marking convention used throughout:

- **[V]** verified in this audit; the method is given next to the claim or in Appendix A.
- **[E]** estimate computed from verified numbers; the calculation is given.
- **[A]** assumed or unverified.

Reference code: `~/npu_models/artifacts/mesmer4b/hf/mesmer_detector.py` (690 lines). All
line numbers below refer to this file.

---

## 1. Executive summary

### 1.1 Feasibility verdict

| Question | Answer | Basis |
|---|---|---|
| Can the backbone be expressed as a static ONNX graph of plain tensor ops? | Yes | A complete rewrite of both layer types was prototyped with random weights and matches the authors' classes to 4e-7 relative error [V, study H] |
| Will the NPU compiler accept it? | Unknown | Exp, Sigmoid, Sqrt, Sub, Abs and graphs of this size were never compiled on this machine [V]; every unproven op except Abs has a fallback built from ops that already ran inside an NPU partition (section 4.12) |
| Will bf16 everywhere preserve the detector's outputs? | Probably, not proven | With random weights the all-bf16 rewrite of a Gated DeltaNet mixer deviates 0.84 to 0.90 % from fp32, against 0.56 to 0.59 % for the reference itself [V, study I]. Only a run with the real weights can settle it (milestone M1, CPU only) |
| Will it be faster than the CPU? | **At best marginally, by the available evidence** | Measured CPU reference: 5.7 s for a 988-token window (reported by the coordinating agent during this audit, not measured by the auditor [A]); synthetic estimate by the audit: 4.8 to 5.0 s plus omitted ops [V, study G]. NPU projection from the Vanguard rate: 4.1 to 4.6 s before per-node overhead [E], a ratio of 1.3 to 1.4 at best |
| Is the port worth starting now? | **No. Measure the NPU first** | One cheap NPU micro-benchmark (M0b in section 11) decides whether there is any speed gain to win |

Overall: the port is **technically plausible, high effort, and currently unjustified on
speed**. The recommended path is to run Mesmer through the authors' own CPU code (exact parity, no
rewrite; this integration was started by the coordinating agent while the audit ran) and to
begin NPU work only if an NPU micro-benchmark at Mesmer shapes projects at least a 1.5 times
advantage over the measured CPU time of about 5.9 s per full window.

### 1.2 Main risks, in order

1. **No speed benefit.** The CPU has AVX-512 BF16 and reaches 2.2 to 2.35 TFLOPS on the
   three dominant matrix shapes [V, study E]; the NPU reached about 1.7 TFLOPS effective on
   Vanguard (figure supplied with the task, not re-measured [A]). The real CPU reference runs
   at about 1.3 TFLOPS effective (5.7 s for 988 tokens, reported [A]). The earlier 4.1 times NPU
   advantage compared NPU bf16 with CPU fp32 in ONNX Runtime, not with CPU bf16.
2. **Static length.** CPU time scales with text length (1.2 s at 256 tokens, 2.4 s at 512
   [V, study G]); a 1024-token static graph costs the same for every text. Length buckets
   multiply compile time, disk and NPU-resident weights.
3. **Compiler acceptance and scale.** About 10,400 non-Constant nodes in total for the
   prototype graph [V per layer, E total], 7.5 times the largest graph compiled so far, and
   3.57 billion NPU-side parameters, 10 times the largest so far.
4. **Numerical drift in bf16.** The reference keeps the delta rule, all RMSNorm internals,
   the decay gate and the heads in fp32. On the NPU everything is bf16.
5. **Threshold stability.** `policy.json` thresholds were tuned to at most 0.7 % and 1 %
   false positives on the authors' held-out human texts. Small logit shifts move verdicts
   that sit near a threshold.
6. **Runtime memory and contexts.** Eight NPU sessions and at least 7.1 GB of NPU-side
   weights; neither the driver's hardware-context limit nor the runtime's weight storage
   format was determined [A].

### 1.3 Where this audit disagrees with the existing proposal

| # | Proposal item | Finding | Status |
|---|---|---|---|
| D1 | Item 3: unit-triangular solve by the nilpotent product (I-N)(I+N^2)...(I+N^32) | **Reject.** Exact in real arithmetic but unstable: fp32 errors of 4e-2 to 1e+27 and bf16 NaN once keys within a chunk are correlated. Random keys hide the problem. Use a recursive block inverse (10 batched MatMuls for chunk 64) | [V, studies A, C] |
| D2 | Item 3: cumsum by MatMul, then pairwise differences | **Replace.** The subtraction cancels in bf16. Compute interval sums directly with one constant MatMul; no subtraction, no Where, no -inf | [V, study C] |
| D3 | Item 6: softplus through Log | **Replace.** `Log(1 + Exp(x))` returns exactly 0 in bf16 for x below about -5.5; 84 of 768 heads would lose their decay. Use a cancellation-free series form; Log is then not needed at all | [V, study D] |
| D4 | Evidence list: "op types in Vanguard's ONNX (all accepted)" | **Overstated.** Cos, Sin, Cast, Shape, Expand, Equal, And, Abs, GreaterOrEqual, LessOrEqual, Unsqueeze, Flatten and the embedding Gather were not inside the NPU partition | [V, section 2.3] |
| D5 | Item 7: 4 segments of 8 layers, about 1.8 GB bf16 each | **Change.** The exported graphs are FLOAT, so 8 layers are 3.57 GB, above the 2 GB protobuf limit. Use 8 segments of 4 layers (1.785 GB each) | [V sizes] |
| D6 | Item 9: NPU 2 to 5 s vs CPU 5 to 15 s | **Not supported.** See 1.1 and section 8 | [V CPU, E NPU] |
| D7 | Item 8: hybrid fallback | **Keep only as a correctness fallback.** The CPU kernel costs 47 ms per layer, 1.1 s per window [V, study E]; with 48 hand-offs the hybrid is projected slower than the plain CPU reference | [V, E] |
| D8 | Item 1: optional buckets 256/512/1024 | **Defer.** Each bucket is a full recompile and another set of NPU-resident weights | [E] |
| D9 | Item 2: NPU outputs the final hidden states | **Small change.** Output the states before the final RMSNorm and apply that norm on the CPU in fp32, as the reference does | design |
| D10 | Item 5: precompute constants | **Refine.** `1 + weight` does not survive rounding to bf16 (mean gain error 0.15 %, maximum 0.39 %, on the real weights); write the gain as `y + y * weight` | [V, study J] |
| D11 | Open concern: exp factors "may underflow in bf16" | **Reframe.** bf16 has the same exponent range as fp32; the issue is resolution (8 significant bits), not range | format definition |
| D12 | Integration | Do not port pre- or post-processing. Use the authors' `Detector` unchanged with only `backbone` replaced; set `pad_to = budget = 1024` so every window is a batch of one at the static length | [V, code reading] |

Agreed without change: batch 1 and static length 1024; no attention mask; pooled token
gathered on the CPU; embedding lookup on the CPU; both heads on the CPU; causal convolution
as shifted multiply-add; the int8 weights cannot feed the BF16 compiler; chunk size is a free
parameter in exact arithmetic.

---

## 2. Evidence base

### 2.1 What was examined

| Source | How | Used for |
|---|---|---|
| `mesmer_detector.py` | read in full | inventory, parity target |
| `model.safetensors` | header parsed; small parameter tensors (A_log, dt_bias, in_proj_a/b, norm weights) read by memory map | shapes, gate statistics. No forward pass |
| `config.json`, `policy.json` | read | sizes, thresholds |
| `~/npu_models` sources and `docs/gui-plan.md` | read | integration |
| `~/.cache/npu_models/{fakespot,vanguard}/*/context.json` and the two exported ONNX graphs | metadata only, no session | which ops ran in the NPU partition, compile times |
| Ryzen AI 1.9 install tree (`vaip_config.json`, `voe/passes/vaiml.py`, `flexmlrt/include/flexml_supported_ops.h`) | read | compiler entry points |
| AMD docs: `modelrun.md`, `linux.md`, `ops_support.html`; AMD article on BCE model memory (2026-02-05) | fetched | op table, config options, memory behaviour |
| `transformers` 5.19 `models/qwen3_5/modeling_qwen3_5.py` | read | upstream delta rule, export path, RoPE |
| arXiv 2412.06464 (Gated DeltaNet), 2406.06484 (DeltaNet parallel form) | abstracts fetched | algorithm provenance |
| Model cards for the 4B and 9B detectors | fetched | int8 statement, benchmarks, limits |
| Ten studies (eight synthetic on the CPU, two read-only inspections) | scripts in Appendix A | every numerical claim |

Note on reproducibility: the Fakespot and Vanguard artifacts and NPU caches
(`~/npu_models/artifacts/{fakespot,vanguard}`, `~/.cache/npu_models/{fakespot,vanguard}`)
were scheduled for deletion by the coordinating agent while this audit was running. Section
2.3 was extracted from them before that and cannot be re-derived once they are gone. The
plan does not depend on those files, only on the facts recorded here.

### 2.2 Model facts

| Item | Value | Status |
|---|---|---|
| Tensors | 466 (426 BF16, 40 F32) | [V] header |
| Embedding | 248,320 x 2,560 = 635,699,200 params (1.27 GB bf16) | [V] |
| Gated DeltaNet mixer, per layer | 42,139,840 params (in_proj_qkv 8192x2560, in_proj_z 4096x2560, in_proj_a and in_proj_b 32x2560, out_proj 2560x4096, conv 8192x1x4, A_log 32, dt_bias 32, norm 128) | [V] |
| Attention mixer, per layer | 36,700,672 params (q_proj 8192x2560, k_proj and v_proj 1024x2560, o_proj 2560x4096, q_norm and k_norm 256) | [V] |
| MLP, per layer | 70,778,880 params (gate, up 9216x2560; down 2560x9216) | [V] |
| Backbone without embedding | 3,570,052,096 params = 7.14 GB bf16 = 14.28 GB fp32 | [V] |
| Doc head | 12,800 params F32 | [V] |
| Sentence head | 8,419,845 params F32 | [V] |
| Layer pattern | 32 layers, every fourth is full attention (indices 3, 7, ..., 31) | [V] config |
| No bias in any backbone linear | no `.bias` tensors under `layers.*` | [V] header |

Decay-gate parameters, read from the checkpoint (768 heads = 24 layers x 32) [V, study J]:

| Quantity | min | 5 % | 25 % | median | 75 % | 95 % | max |
|---|---|---|---|---|---|---|---|
| exp(A_log) | 0.0147 | 0.094 | 0.163 | 0.311 | 0.987 | 9.48 | 74.6 |
| dt_bias | -7.47 | -6.19 | -4.63 | -2.87 | -0.76 | 2.49 | 19.1 |
| g at the mean gate logit, per token | -10.3 | -1.17 | -0.228 | -0.0355 | -0.00347 | -0.00069 | -0.00011 |
| same, summed over a 64-token chunk | -657 | -75.2 | -14.6 | -2.27 | -0.222 | -0.044 | -0.0073 |

Here g = -exp(A_log) * softplus(dt_bias) is the value at a zero gate projection; the
projection adds a per-token term whose scale, under an isotropic-input assumption [A], has a
median standard deviation of 1.06. Two consequences drive section 5: many heads sit deep in
the negative tail of softplus, and 23 % of heads accumulate more than 16 in magnitude within
one chunk.

### 2.3 What actually ran on the NPU so far

Method: the node list of the compiled partition in `context.json` holds node names and node
output names; both were matched against the ONNX graph [V].

| | Vanguard | Fakespot |
|---|---|---|
| Partitions | 1 (`vaiml_par_1`, device VAIML) | 1 |
| Nodes in partition | 1386 | 476 |
| Compile time (`vaiml_partition` pass) | 466.1 s | 49.6 s |
| NPU-side parameters | about 344 M | about 86 M |
| Compiled `.rai` size | 423.6 MB (1.23 bytes per parameter) | 103.4 MB (1.21) |
| Ops inside the partition | Mul 255, MatMul 169, Add 169, Slice 168, Transpose 112, Squeeze 84, LayerNormalization 58, Reshape 56, Neg 56, Concat 56, Where 30, Div 30, Erf 29, Split 28, Softmax 28, IsNaN 28, ReduceSum 1, Gemm 1 | Add, MatMul, Reshape, Transpose, Mul, LayerNormalization, Where, Softmax, IsNaN, Div, Erf, Gemm, Tanh 1, Gather 1 |
| Not in the partition | Constant, Cast 179, Gather 31, Shape 30, And, Unsqueeze, ConstantOfShape, Equal, Expand, Cos, Sin, GreaterOrEqual, Flatten, Abs, LessOrEqual, plus constant-foldable Mul/Add/Where/Transpose/Div | Constant, Cast, Gather 5, Equal, ConstantOfShape, Expand, And, Shape, Not, CumSum, GatherElements, GreaterOrEqual, Flatten |
| Partition inputs | two Cast outputs, two attention masks, the embedding Gather output | attention mask and three embedding Gather outputs |

Notes:

- "Not in the partition" means either folded to a constant before partitioning or executed by
  the ONNX Runtime CPU provider. The two cases were not separated.
- The embedding lookup ran on the CPU in both models [V]. The proposal's plan to keep the
  Mesmer embedding on the CPU matches what the toolchain already does.
- The largest activation-by-activation MatMul proven is the attention product
  `[1,16,1024,64] x [1,16,64,1024]` (rank 4) [V].
- `flexmlrt/include/flexml_supported_ops.h` declares a `cpu_op` list ("supported by the CPU
  runtime") with 81 entries including Exp, Log, Sigmoid, Sqrt, CumSum, Conv. So a node inside
  a VAIML partition is not necessarily executed on the NPU array [A]. Whether an op is
  accelerated must be checked by timing, not only by partition membership.
- AMD's operator table (BF16 column) marks as supported: Abs, Add, Cast, Concat, Conv,
  CumSum, Div, Einsum, Equal, Erf, Exp, Expand, Gather, Gemm, Greater, GroupConv, Less, Log,
  MatMul, Max, Min, Mul, Neg, Pad, Pow, Reciprocal, ReduceMean, ReduceSum, Reshape, Sigmoid,
  Sin, Slice, Split, Sqrt, Squeeze, Sub, Tanh, Tile, Transpose, Unsqueeze, Where. It leaves
  blank: Softmax, LayerNormalization, Cos, Relu, Clip, Gelu, GreaterOrEqual, LessOrEqual.
  Softplus, Trilu, Loop and If are absent [V, table parsed from the page]. Softmax and
  LayerNormalization did compile here, so the table is indicative only.

### 2.4 Toolchain facts relevant to the plan

| Fact | Status |
|---|---|
| The BF16 flow takes a FLOAT ONNX graph and converts to bf16 (`enable_f32_to_bf16_conversion=True` in `voe/passes/vaiml.py`); both existing exports hold only FLOAT initializers | [V] |
| `voe/passes/vaiml.py` loads the model with `load_external_data=False` and passes an external-data directory to the front end | [V] code; behaviour with external data [A] |
| AMD's BCE article compiles from a single-file ONNX and then runs an external-data copy against the same cache; peak memory fell from 1936 MB to 735 MB with a bf16 embedding plus external data (Ryzen AI 1.7) | [V] article; not reproduced |
| AMD docs: opset 17 recommended; `preferred_data_storage: unvectorized` for transformers; `optimize_level` 1 to 3 | [V] docs |
| `emoji` is not installed in `~/ryzen-ai-venv`; `tokenizers` 0.23.3, `safetensors` 0.9.0rc1, `datasets` 4.5.0 are; `scipy`, `pytest`, `onnxscript`, `onnxsim` are not | [V] |
| No process was listening on 127.0.0.1:8765 during the audit | [V] `ss -ltn` |
| RAM 53 GB total, 46 GB available; 544 GB disk free | [V] |

---

## 3. Inventory of the reference detection path

Everything below is used by `Detector.analyze()` (the path a GUI needs) or
`Detector.predict()` (the benchmarked path). Verified by reading the file in full [V].

### 3.1 Pre-processing

| Step | Lines | What it does | Dependencies |
|---|---|---|---|
| `normalize_text` | 103-110 | NFC, `emoji.demojize`, delete all Unicode `Cf` characters and a fixed invisible list, map U+2800 to space, fold fullwidth and mathematical letters by NFKC, map Cyrillic/Greek/Armenian look-alikes inside Latin words, drop everything before `</think>`, drop a chat-style first paragraph ("Sure", "Here", "Abstract", "Title", "I'm happy to help", "Certainly"), collapse whitespace, lowercase | `emoji`, `unicodedata` (Python's Unicode version), `re` |
| `_char_table`, `_map_homoglyphs`, `_mostly_latin`, `_remove_ai_header` | 51-100 | helpers for the above | same |
| `split_units` | 122-139 | sentence, line and list-item spans on the **raw** text; fragments under 3 words join the previous unit | `re` |
| `_kept_from`, `normalize_units` | 142-177 | the same normalisation applied per unit; units inside a dropped preamble become `''` | `emoji` |
| Tokenisation | 513-515, 552-553 | `tokenizers.Tokenizer.from_file(tokenizer.json)`, no truncation, no padding, `add_special_tokens=False` | `tokenizers` |
| `predict` input | 558 | ids of the normalised whole text, first 1,023 tokens, plus `eos_id` (248044) | |
| `analyze` windows | 612-637 | each kept unit is encoded on its own (a leading space for every unit after the first) and truncated to 1,023 tokens; a window holds whole units up to 1,023 tokens, ends with `eos_id`, and after the first window re-reads preceding units as context while they fit in `min(256, 255, 1023 - len(first owned unit))` tokens; unit token spans `us`, `ue` and the `owned` flags are recorded | |
| Batching | 181-216 | length-sorted micro-batches under a token budget (default 16,384), right-padded with `pad_id` to a multiple of 16 | |

Two properties matter for the port:

- `analyze` and `predict` tokenise differently (per unit with a leading space against the
  whole normalised string), so they do not see the same ids for the same text. Both must be
  kept as they are.
- With `tokens_per_batch = 1024` and `pad_to = 1024`, `_microbatches` and `_collate` produce
  exactly one window per batch, padded to 1024 [V, lines 185-216: `tokens_per_mb // width`
  is 1]. No change to the windowing code is needed for a batch-1 static backend.

### 3.2 Backbone

| Component | Lines | Precision in the reference (CPU, bf16 weights) |
|---|---|---|
| Embedding lookup | 458 | bf16 table, bf16 output |
| RoPE tables | 453-461 | computed in fp32 from `inv_freq` (32 frequencies, theta 1e7, rotary dim 64 = 0.25 x 256), cast to bf16 |
| `RMSNorm` | 319-327 | fp32 inside (`x.float()`, mean of squares, rsqrt, times `1 + weight`), result cast to bf16 |
| `Linear` | 308-316 | bf16 (int8 path not used) |
| `torch_causal_conv1d` + SiLU | 268-272 | bf16 (weights bf16), depthwise, kernel 4, left padding 3 |
| Gates | 376-377 | `beta = sigmoid(in_proj_b(h))` in bf16; `g = -exp(A_log) * softplus(in_proj_a(h) + dt_bias)` in **fp32** |
| Head repetition | 381-382 | q, k repeated from 16 to 32 heads (`repeat_interleave(2)`) |
| `torch_chunk_gated_delta_rule` | 229-265 | **fp32** throughout (autocast disabled, line 291), chunk 64, output cast to bf16 |
| `GatedRMSNorm` | 330-339 | norm in fp32, cast to bf16, times weight, times `silu(gate)` in fp32, cast to bf16 |
| `Attention` | 396-412 | q carries a gate (q_proj output is split in two); RMSNorm on q and k; partial RoPE on the first 64 of 256 dims; `scaled_dot_product_attention(is_causal, scale=1/16, enable_gqa)` in bf16; output times `sigmoid(gate)`; o_proj |
| `MLP` | 415-421 | `down(silu(gate(x)) * up(x))`, bf16 |
| `Layer` | 424-438 | pre-norm residual blocks, residual stream bf16 |
| Final norm | 452, 464 | `RMSNorm` as above |

The reference is therefore already a bf16 model with fp32 islands: the delta rule, the decay
gate, every norm's internals and the heads. An NPU graph in bf16 turns the first three into
bf16. RoPE with `mrope_interleaved` and sections [11, 11, 10]: for text-only input the three
position axes are identical, which reduces the interleaved scheme to ordinary 1-D RoPE with
32 frequencies; the authors' `_rope` implements exactly that [V by reading the upstream
`recomposition_frequencies`; the parity target is the authors' file in any case].

### 3.3 Heads and post-processing

| Step | Lines | Notes |
|---|---|---|
| Pooling | 565, 595 | hidden state at index `lens - 1`, which is the appended `eos` token |
| `DocHead` | 467-474, 566-567 | LayerNorm(2560) + Linear(2560, 3, no bias), fp32 |
| Unit features | 598-604 | per unit: mean of its token states (`index_add_`), state of its last token, `log1p(token count)`; fp32 |
| `SegHead` | 477-496 | LayerNorm + Linear to 512, learned position (513 entries, clamped), global token from the pooled state, 2-layer `nn.TransformerEncoder` (8 heads, norm-first, key-padding mask), LayerNorm + Linear to 3; fp32 |
| Softmax | 219-221, 645 | fp32 |
| Unit probabilities | 646-654 | only owned units of each window are written; units dropped by normalisation copy the next (else previous) unit |
| Document probabilities | 655-656 | mean of the window probabilities weighted by the number of owned units |
| `verdict` | 570-577 | `ai` if `p_ai >= p_edit` and `p_ai + 0.5 p_edit >= 0.6084`; else `ai_edited` if `1 - p_human >= 0.907`; else `human` |
| Unit labels | 657-661 | `human` if `1 - p_human < 0.8696`, else `ai` or `ai_edited` by the larger of the two |
| Summary | 662-666 | `words`, `flagged_fraction` (non-space characters in flagged units) |

Model-card limits that the GUI should surface: English only; unreliable below about 50 words;
the int8 weights are "within 0.007 on the ternary rows" of the bf16 weights, and the authors'
second benchmark table was produced with int8 [V, model card as fetched]. That last statement is the
only published indication of how much numerical perturbation the authors consider harmless.

---

## 4. Port plan per component

Placement key: **CPU-ref** = the authors' code, unchanged; **NPU** = inside the exported
graph; **CPU-glue** = new, small, on the CPU.

"Proven" means the op ran inside an NPU partition on this machine (section 2.3). "Listed"
means AMD's table marks it for BF16 but it never ran here.

### 4.1 Text normalisation, sentence units, tokenisation, windowing

| | |
|---|---|
| Current | lines 31-216, 552-553, 608-637 |
| Target | **CPU-ref, unchanged.** Import the authors' module from `artifacts/mesmer4b/hf/` |
| Changes | none to the code. Install `emoji` (pure Python) into the venv and record its version; record the `tokenizers` and Python versions |
| Rationale | the thresholds were calibrated on this exact pipeline; any re-implementation is a source of silent drift |
| Risks | `emoji.demojize` output and the `Cf` table depend on the installed `emoji` and Python Unicode versions, which the authors do not pin [A]. Covered by golden tests (section 10.5). Adding a package departs from the "no new packages" rule in `docs/gui-plan.md`; `emoji` has no dependencies [A] |

### 4.2 Embedding lookup

| | |
|---|---|
| Current | `F.embedding(input_ids, embed)`, bf16 |
| Target | **CPU-glue.** `numpy.memmap` of the `embed_tokens.weight` byte range in `model.safetensors` as uint16; gather 1024 rows; widen to fp32 by a 16-bit left shift |
| Ops | none in the graph. The graph input is `h0` FLOAT `[1024, 2560]` |
| Precision | exact: every value is bf16-representable, so the FLOAT to bf16 conversion at the NPU input is lossless |
| Rationale | embedding Gathers stayed on the CPU in both compiled models [V]; a 1.27 GB table inside a graph adds nothing |

### 4.3 RMSNorm (65 instances: two per layer and the final one) and q/k norms

| | |
|---|---|
| Current | fp32 inside: `y * rsqrt(mean(y^2) + 1e-6) * (1 + w)`, then bf16 |
| Target | **NPU** for the 64 in-layer norms; **CPU-glue in fp32 for the final norm** (D9) |
| Graph form | `ms = ReduceSum(x * x) * (1/n)`; `y = x / Sqrt(ms + eps)`; `out = y + y * w` |
| Ops | Mul, ReduceSum, Add, Div (proven); Sqrt (listed) |
| Fallback if Sqrt is rejected | `LayerNormalization(Concat(x, -x))` and keep the first half: the mean is zero and the variance equals the mean square, so it is RMSNorm with the same epsilon, using only proven ops (Concat, Neg, LayerNormalization, Slice) |
| Precision | all intermediate values become bf16. Measured on random data: decomposed form 0.36 % relative error, LayerNormalization form 0.24 %, reference 0.17 % [V, study D] |
| Gain constant | `1 + w` rounded to bf16 has a mean relative error of 0.15 % and a maximum of 0.39 % over the 170,496 real gain entries, and 65 % of channels are off by more than 0.1 % [V, study J]. This is a fixed per-channel bias, not noise. `y + y * w` avoids it because `w` itself is exactly representable |
| Risk | mean of squares of large residual-stream values; no overflow is possible below about 1e19 per element |

### 4.4 Linear layers (all projections and the MLP)

| | |
|---|---|
| Current | `F.linear`, bf16 weights, no bias |
| Target | **NPU.** `MatMul(x, W^T)` with W as a FLOAT initializer holding the widened bf16 values |
| Ops | MatMul with a constant operand (proven) |
| Precision | identical in kind to the reference. Weights survive the FLOAT to bf16 conversion exactly [V by construction; to be asserted by a test]. The accumulation precision inside the NPU kernel is unknown [A] |
| Risk | the six large matrices per layer are 21 to 24 M parameters each, larger than anything compiled so far (Vanguard's largest is about 5.4 M) [V sizes] |

### 4.5 SiLU and Sigmoid (MLP, convolution, gated norm, attention gate, beta)

| | |
|---|---|
| Current | `F.silu`, `torch.sigmoid` |
| Target | **NPU.** `x * Sigmoid(x)` |
| Ops | Sigmoid (listed), Mul (proven) |
| Fallbacks | (a) `0.5 + 0.5 * Tanh(0.5 x)`; Tanh ran in the Fakespot partition. (b) `Softmax` over a stacked `[x, 0]` pair, first component; Softmax is proven |
| Precision | direct and Tanh forms are both at the bf16 rounding floor on [-12, 12]: SiLU mean absolute error 2.0e-3 and 2.8e-3 [V, study D] |

### 4.6 Causal depthwise convolution

| | |
|---|---|
| Current | `F.conv1d(x, w, padding=3, groups=8192)[..., :T]`, cross-correlation, so `y[t] = sum_j w[c, j] * x[t - 3 + j]` |
| Target | **NPU.** `y = x * w[:, 3] + shift1(x) * w[:, 2] + shift2(x) * w[:, 1] + shift3(x) * w[:, 0]`, where `shift_s` prepends s zero rows and drops the last s |
| Ops | Slice, Concat, Mul, Add (all proven) |
| Alternative | one ONNX `Conv` with `group=8192`; Conv and GroupConv are listed, never run here, and a 1-D depthwise convolution in the unvectorized transformer layout is untested |
| Precision | up to seven roundings instead of one; contribution well below the kernel's |
| Verified | tap order and equality with the authors' function inside the full-layer parity (3.7e-7) [V, study H] |

### 4.7 Decay gate

| | |
|---|---|
| Current | `g = -exp(A_log) * softplus(in_proj_a(h) + dt_bias)`, fp32 |
| Target | **NPU**, with the softplus of section 5.4 |
| Ops | MatMul, Add, Mul, Div (proven); Exp, Abs (listed) |
| Why not `Softplus` or `Log(1 + Exp)` | Softplus is absent from AMD's table; the Log form is numerically wrong in bf16 (D3) |
| Constant | `-exp(A_log)` is computed in fp32 at export and rounded to bf16 by the compiler: a fixed relative error of at most 0.39 % in the decay rate of a head |
| Fallback if Abs is rejected | `Max(x, -x)` (Max listed); else `Where(Greater(x, 0), x, -x)`; else compute the gate on the CPU, which means the hybrid layout of section 7.6 |

### 4.8 Gated delta rule

See section 5. Target **NPU**; ops MatMul, Mul, Add, Slice or Split, Concat, Reshape,
Transpose, ReduceSum, Div, Neg (proven), Exp, Sqrt, Sub (listed). `Sub` can be written as
`Add(a, Neg(b))` if rejected.

### 4.9 Gated RMSNorm and output projection

| | |
|---|---|
| Current | per head vector of 128: `weight * rmsnorm(o) * silu(z)` |
| Target | **NPU**, same decomposition as 4.3 without the `1 +` (the weight multiplies directly; real values 0.62 to 1.02 in layer 0 [V]) |
| Ops | as 4.3 and 4.5 |

### 4.10 Full attention

| | |
|---|---|
| Current | lines 396-412 |
| Target | **NPU**, written out by hand instead of exporting `scaled_dot_product_attention` |
| Grouped queries | 16 query heads share 4 key/value heads. Reshape q from `[16, T, 256]` to `[4, 4T, 256]` so that the four query heads of a group are stacked along the row axis; then `scores = q @ k^T` is `[4, 4T, T]`, the causal mask is the `[T, T]` mask repeated four times along rows, and `out = softmax(scores) @ v` is `[4, 4T, 256]`. No replication of k or v, all tensors rank 3. Equal to `enable_gqa=True` to 9e-16 in fp64 [V, study D] |
| Mask | additive constant, 0 on and below the diagonal and -1e9 above; no Where, no IsNaN, no infinity |
| Scale | 256^-0.5 = 1/16, a power of two, so its placement does not change rounding |
| RoPE | `cos`, `sin` computed at export exactly as lines 455-461 and rounded to bf16 there, stored as constants `[1024, 64]`; rotation by Slice, Neg, Concat, Mul, Add |
| Ops | MatMul, Mul, Add, Softmax, Slice, Concat, Neg, Reshape, Transpose, ReduceSum, Div (proven); Sqrt, Sigmoid (listed) |
| Precision | the reference attention is already bf16 on the CPU. Scores of magnitude 16 or more are resolved to 0.06 to 0.125 in both |
| Verified | full attention layer against the authors' class: 1.4e-7 [V, study H] |

### 4.11 Final norm, pooling, heads, aggregation, policy

| | |
|---|---|
| Target | **CPU.** Final RMSNorm in fp32 on the NPU output, result rounded to bf16 as the reference does (`.type_as`), then the authors' `_forward_both`, `DocHead`, `SegHead`, softmax, aggregation and `verdict` unchanged |
| Cost | 1024 x 2560 values; negligible |
| Rationale | this is the last operation before both heads; keeping it in fp32 removes one bf16 island at no cost |

### 4.12 Operator summary for the NPU graph

Counts are from a toy export of the prototype with random weights at the real sequence
length, head counts and head dimensions (reduced hidden width) [V, study H].

| Op | Per GDN layer | Per attention layer | Status | Fallback |
|---|---|---|---|---|
| MatMul | 87 | 9 | proven | |
| Mul | 62 | 24 | proven | |
| Add | 50 | 9 | proven | |
| Gather (constant index) | 94 | 0 | proven only once (Fakespot pooling) | replace by one Split per tensor, or Slice + Squeeze (proven); see 6.3 |
| Sub | 22 | 0 | listed | Add + Neg |
| Unsqueeze | 18 | 0 | not in a partition | Reshape (proven) |
| Reshape | 15 | 7 | proven | |
| Concat | 9 | 4 | proven | |
| Slice | 8 | 10 | proven | |
| Transpose | 8 | 5 | proven | |
| ReduceSum | 6 | 4 | proven | |
| Div | 6 | 4 | proven | |
| Sqrt | 5 | 4 | listed | LayerNormalization on `[x, -x]` |
| Exp | 5 | 0 | listed | for non-positive arguments: `p / q` with `[p, q] = Softmax([x, 0])` |
| Sigmoid | 4 | 2 | listed | Tanh form or 2-way Softmax |
| Reciprocal | 2 | 4 | listed | write as Div |
| Abs | 1 | 0 | listed | Max, or Where + Greater, or hybrid |
| Neg | 1 | 2 | proven | |
| Softmax | 0 | 1 | proven | |
| Identity | 1 | 0 | listed | remove |
| Non-Constant nodes | 404 | 89 | | |
| Maximum tensor rank | 4 | 3 | rank 4 proven | |

Every Exp argument in the design is non-positive by construction (decays and
`exp(-|x|)`), so no Exp can overflow and the Softmax fallback for Exp is valid everywhere it
is used.

---

## 5. The gated delta rule rewrite

### 5.1 The recurrence (ground truth)

Per value head, with state `S` of shape `[128, 128]` (key dim by value dim), unit-norm key
`k_t`, query `q_t` (unit norm times 128^-0.5), value `v_t`, write strength `beta_t` in (0, 1)
and log decay `g_t <= 0`:

```
S'_t = exp(g_t) * S_{t-1}                    decay
u_t  = beta_t * (v_t - S'_t^T k_t)           correction (the delta rule)
S_t  = S'_t + k_t u_t^T                      write
o_t  = S_t^T q_t                             read
```

This is `torch_recurrent_gated_delta_rule` in transformers 5.19 [V, read]. The chunked kernel
in the reference is an exact regrouping of it (DeltaNet, arXiv 2406.06484; gating, arXiv
2412.06464).

### 5.2 Chunked form

Take one chunk of C tokens with incoming state `S_0`. Define the interval decay

```
gamma[t, j] = exp(g_{j+1} + ... + g_t)   for j <= t,   gamma[t, t] = 1
e_cum[t]    = exp(g_1 + ... + g_t)                      (decay since the chunk start)
e_tail[j]   = exp(g_{j+1} + ... + g_C)                  (decay until the chunk end)
e_all       = exp(g_1 + ... + g_C)
```

Unrolling the recurrence inside the chunk gives

```
S_t = e_cum[t] * S_0 + sum_{j <= t} gamma[t, j] * k_j u_j^T
u_t = beta_t * ( v_t - e_cum[t] * S_0^T k_t - sum_{j < t} gamma[t, j] * (k_j . k_t) * u_j )
```

Stack the rows of a chunk into matrices U, V (C by 128), K, Q (C by 128) and let

```
N[t, j]     = beta_t * (k_t . k_j) * gamma[t, j]   for j < t, else 0      (strictly lower)
A[t, j]     = (q_t . k_j) * gamma[t, j]            for j <= t, else 0     (lower with diagonal)
K~[t, :]    = beta_t * e_cum[t] * k_t
Tinv        = (I + N)^-1
```

Then

```
U     = Tinv (beta * V)  -  (Tinv K~) S_0
O     = (e_cum * Q) S_0  +  A U
S_C   = e_all * S_0  +  (e_tail * K)^T U
```

These are lines 243-263 of the reference: `new_v = Tinv (beta V)`, `k_cum = Tinv K~`,
`intra = A`, `query * exp(cum)`, `key * exp(cum_last - cum)`, `chunk_decay = e_all`. The
reference's `solve_triangular(..., unitriangular=True)` ignores the diagonal of its `ut`
matrix, so the system matrix is exactly `I + N` [V].

Everything that does not involve `S_0` depends on one chunk only and is computed for all 16
chunks at once. Only the three lines above are sequential: 16 steps for T = 1024, C = 64.

### 5.3 Decays without subtraction (replaces "cumsum then difference")

The reference forms `gamma[t, j] = exp(cum_t - cum_j)`. In fp32 this is harmless. In bf16
`cum` carries 8 significant bits, so a cumulative sum of magnitude 16 to 32 is resolved to
0.125 and one of magnitude 1024 to 2048 to 8, while the difference that is needed may be of
order 0.01 to 10. From section 2.2, 23 % of heads exceed 16 within one chunk and 3.8 % exceed
88 [V].

Replacement: let `M` be the constant 0/1 matrix of shape `[C*C, C]` with
`M[(t, j), m] = 1` when `j < m <= t`. Then

```
D = g M^T                       shape [.., C*C] -> [.., C, C];  D[t, j] = g_{j+1} + ... + g_t
gamma_strict = exp(D) * strict_lower_ones
e_cum  = exp(g @ triu_ones)     (inclusive prefix sums as one constant MatMul)
e_tail = exp(g @ strict_tril_ones)
e_all  = exp(ReduceSum(g))
```

All sums are of same-sign terms, so nothing cancels. `D` is zero wherever `j >= t`, so the
upper triangle is removed by multiplying with a constant mask; no Where and no infinite
constant are needed. Cost: one MatMul of `[32, 16, 64] x [64, 4096]`, 0.27 GFLOP per layer.

Measured effect in emulated bf16 (per-head relative error of the kernel output, recursive
inverse in both columns) [V, study C]:

| Gate parameters from | Key correlation | cumsum-difference: median / max | interval sums: median / max |
|---|---|---|---|
| layer 1 (fast heads) | 0 | 0.77 % / 2.4 % | 0.43 % / 0.77 % |
| layer 1 | 0.9 | 1.7 % / 6.4 % | 0.52 % / 1.7 % |
| layer 10 | 0.6 | 1.0 % / 1.4 % | 0.85 % / 1.2 % |
| layer 26 | 0.9 | 1.4 % / 2.2 % | 0.61 % / 1.8 % |

### 5.4 Softplus without `1 + tiny`

`softplus(x) = log(1 + exp(x))`. For negative x the result is close to `exp(x)`, and
`1 + exp(x)` rounds to exactly 1 in bf16 once `exp(x) < 2^-8`, that is for x below about
-5.5. The gate then returns g = 0: a head that should decay slowly does not decay at all.
Measured with every op rounded to bf16 [V, study D]:

| x range | `Log(1 + Exp(x))` mean / max relative error | proposed form mean / max |
|---|---|---|
| [-10, -6] | 100 % / 100 % | 0.15 % / 0.46 % |
| [-6, -3] | 32 % / 100 % | 0.27 % / 0.80 % |
| [-3, 0] | 1.2 % / 7.0 % | 0.31 % / 1.3 % |
| [0, 3] | 0.19 % / 1.1 % | 0.17 % / 1.1 % |
| [3, 10] | 0.07 % / 0.42 % | 0.07 % / 0.37 % |

On the real parameters, at the mean gate value: the Log form sets g to exactly 0 for 84 of
768 heads and changes the retention over 1024 tokens, `exp(sum g)`, by more than 0.05 for
137 heads (mean absolute change 0.084, maximum 1.0). The proposed form: 0 heads, maximum
change 0.003 [V, study D]. Fed into an otherwise exact fp32 kernel, the Log form alone
produces a kernel output error of up to 35 % per head with layer-10 parameters
[V, study C].

Proposed form (Exp, Div, Mul, Add, Abs only):

```
a  = |x|
u  = exp(-a)                         in (0, 1]
s  = u / (u + 2)                     in (0, 1/3]
L  = 2 s (1 + s^2/3 + s^4/5 + s^6/7 + s^8/9)       = log(1 + u) up to truncation
softplus(x) = (x + a) / 2 + L
```

It uses `log(1 + u) = 2 atanh(u / (2 + u))`. Every term is positive, so relative accuracy is
kept for arbitrarily negative x. Truncation error with five terms: 1.6e-6 relative over
[-30, 30]; four terms 1.8e-5; three terms 2.1e-4 [V]. `(x + a) / 2` is exact for negative x
only if `a` is the exact absolute value, which is why Abs (or Max) is required and
`sqrt(x^2)` is not acceptable.

### 5.5 The triangular inverse (replaces the nilpotent product)

The proposal's identity `(I + N)^-1 = (I - N)(I + N^2)(I + N^4)...(I + N^(C/2))` is correct
because `N^C = 0`. It is numerically unusable. Expanding the product gives every power
`N^p` with alternating signs. If the keys of a chunk are similar to each other (a shared
component, or slow drift from token to token) then `N` is close to a constant times the
strictly lower matrix of ones, whose p-th power has entries `binomial(t - j - 1, p - 1)`.
For C = 64 these reach about 5e17 before they cancel. The true inverse is of order one, because
the delta rule with unit keys and beta in (0, 1) is a contraction.

Measured, chunk 64. The fp64 column is from study A (8 heads, 256 tokens, dim 32); the other
columns are from study C at the real kernel shapes with layer-1 gate parameters [V]:

| Key model | fp64 | fp32, global relative error | bf16 emulated |
|---|---|---|---|
| independent random keys | 8e-16 | 2.7e-7 | 0.97 % |
| shared component 0.3 | | 2.2e-5 | 411 % |
| shared component 0.6 | | 4.7 % | NaN |
| shared component 0.9 | 3.6e-10 | 5.8e+21 | NaN |
| token-to-token persistence 0.9 | | 53 % | NaN |
| shared 0.9, chunk 128 | 3.5 % | | |

A study with independent random keys confirms the method; any structure in the keys breaks
it. Real key vectors come from a convolution over neighbouring tokens followed by SiLU, so
correlation within a chunk has to be expected [A; measured on real data in milestone M1].

Replacement: recursive block inversion. Let `M_s` (s = 1, 2, 4, ..., C/2) be the constant
mask with `M_s[i, j] = 1` when i and j are in the same block of size 2s but i is in its lower
half-block and j in its upper half-block. The masks tile the strict lower triangle. Define

```
T_1    = I
T_{2s} = T_s - T_s (N * M_s) T_s
```

Claim: `T_s` is the block-diagonal matrix of the inverses of the s-by-s diagonal blocks of
`I + N`; hence `T_C = (I + N)^-1`. Proof by induction: a diagonal block of size 2s of
`I + N` is `[[A, 0], [B, D]]` with `B` the part selected by `M_s`, and its inverse is
`[[A^-1, 0], [-D^-1 B A^-1, D^-1]]`, which is `T_s - T_s (N * M_s) T_s` restricted to that
block because `T_s` there is `diag(A^-1, D^-1)`.

Properties:

- The first level needs no product (`T_2 = I - N * M_1`). For C = 64 there are 5 further
  levels, 10 batched MatMuls of `[32, 16, 64, 64]`, 2.7 GFLOP per layer.
- Only MatMul, Mul by a constant mask, and Sub (or Add + Neg).
- Every intermediate is an inverse of a principal block of the same matrix, so intermediate
  magnitudes are those of the solution. No binomial growth.
- Products of lower-triangular matrices with exact zeros above the diagonal stay exactly
  lower triangular, so causality inside a chunk is preserved bit for bit [V, study H: zero
  change of earlier outputs when later inputs change].

Accuracy: equal to row-by-row forward substitution (the route transformers takes when
exporting, which needs 63 sequential steps) to within rounding, in fp64, fp32 and emulated
bf16, for every key model tested [V, studies A and C]. Example, shared component 0.9, layer-1
gates, bf16: recursive 0.52 % median / 1.74 % max; forward substitution 0.52 % / 1.80 %.

### 5.6 Head repetition

Value head h uses key head h // 2. The Gram matrices `K K^T` and `Q K^T` depend only on the
key head, so they are computed for 16 heads and duplicated, which halves those products.
Duplication is done with rank-4 tensors only: `Concat([x, x], axis=1)` on `[16, nc, C, C]`
gives `[16, 2 nc, C, C]`, and a Reshape to `[32, nc, C, C]` places the two copies of key
head h at value heads 2h and 2h + 1 [V, study H parity].

### 5.7 Complete kernel, in graph order

Shapes for T = 1024, C = 64, nc = 16, batch dimension dropped.

```
q, k       [16, nc, C, 128]   after conv + SiLU, l2-normalised; q also times 128^-0.5
v          [32, nc, C, 128]
beta, g    [32, nc, C]

D          = (g @ M_interval).reshape(32, nc, C, C)
pair       = exp(D) * strict
e_cum      = exp(g @ M_prefix)[..., None]         e_tail = exp(g @ M_suffix)[..., None]
e_all      = exp(sum(g))

Gkk, Gqk   = dup(k @ k^T), dup(q @ k^T)           [32, nc, C, C]
k2, q2     = dup(k), dup(q)                       [32, nc, C, 128]
N          = Gkk * beta[..., None] * pair
A          = Gqk * (pair + I)
rhs        = concat(v * beta[..., None], k2 * (beta * e_cum)[..., None], axis=-1)   [32, nc, C, 256]

Tinv       = I - N * M_1
for s in (2, 4, 8, 16, 32):   Tinv = Tinv - Tinv @ ((N * M_s) @ Tinv)
sol        = Tinv @ rhs        new_v = sol[..., :128]     k_cum = sol[..., 128:]
qd         = q2 * e_cum        kdT   = (k2 * e_tail)^T

S = 0                                              [32, 128, 128]
for c in 0..nc-1:
    v_new  = new_v[:, c] - k_cum[:, c] @ S
    out_c  = qd[:, c] @ S + A[:, c] @ v_new
    S      = S * e_all[:, c] + kdT[:, c] @ v_new
out        = concat(out_c, axis=1)                [32, T, 128]
```

Verified against the authors' `GatedDeltaNet` inside a full layer, random fp32 weights, real
head counts and dimensions, T = 1024: relative error 3.7e-7 [V, study H]. Verified against
the fp64 per-token recurrence: 2e-7 to 9e-7 in fp32, 5e-16 in fp64 [V, studies A and C].

### 5.8 Exactness conditions

| Condition | Why | Status |
|---|---|---|
| T is a multiple of C | the reference pads to a multiple of 64 with zeros (beta = 0, g = 0, k = 0), which is a no-op; a static 1024 graph needs no padding | [V] |
| Chunks start at position 0 | same alignment as the reference | [V] |
| No initial state, no final state | the reference passes `initial_state=None` | [V] line 383 |
| Any C dividing T gives the same result in exact arithmetic | regrouping of the same recurrence; fp64 error at most 1.4e-15 for C = 16, 32, 64, 128 | [V, study A] |
| Padding content cannot influence earlier positions | all masked entries are exact zeros; no operation can produce an infinity (all Exp arguments are non-positive) | [V, study H, fp32] |

### 5.9 Chunk size

| C | Sequential steps | Inverse levels with products | Kernel GFLOP per layer [E] | bf16 error, median / max [V, study C, layer-1 gates, shared 0.9] |
|---|---|---|---|---|
| 16 | 64 | 3 | about 4 | 0.54 % / 1.31 % |
| 32 | 32 | 4 | about 5 | 0.53 % / 1.35 % |
| 64 | 16 | 5 | 8.3 | 0.52 % / 1.74 % |
| 128 | 8 | 6 | about 21 | 0.52 % / 2.24 % |

Accuracy is flat in C. Choose **C = 64**: it equals the reference's chunking, which makes
intermediate tensors directly comparable while debugging, and the kernel is 0.20 TFLOP for
24 layers, 2.6 % of the window total. C = 128 is the option if node count rather than FLOPs
turns out to limit the NPU (it halves the loop nodes).

### 5.10 Precision of the kernel in bf16

Emulation model: every op is evaluated in fp32 and its result rounded to bf16. This is the
optimistic case; if an NPU kernel accumulates in bf16 internally, errors are larger [A].

Per-head relative error of the kernel output against the fp64 recurrence, recommended form,
C = 64, real gate parameters, synthetic q, k, v, beta [V, study C]:

| Gate parameters | Key model | median | 90 % | max |
|---|---|---|---|---|
| floor: exact result rounded once to bf16 | | 0.17 % | 0.17 % | 0.17 % |
| authors' fp32 kernel | any | 2e-7 to 9e-7 | | 1e-6 |
| layer 0 | independent | 0.66 % | 0.75 % | 0.79 % |
| layer 0 | shared 0.9 | 1.65 % | 1.75 % | 1.76 % |
| layer 1 | independent | 0.43 % | 0.69 % | 0.77 % |
| layer 1 | shared 0.9 | 0.52 % | 1.69 % | 1.74 % |
| layer 10 | shared 0.6 | 0.85 % | 1.12 % | 1.16 % |
| layer 26 | shared 0.9 | 0.61 % | 1.65 % | 1.78 % |

No single stage is responsible. Rounding only one stage at a time gives 0.004 % to 0.56 %
(median) for each of: normalisation, beta scaling, decays, Gram matrices, inverse, applying
the inverse, and the three loop lines; the total is their root-sum [V, study F]. The inverse
itself is among the smallest contributors (0.02 % to 0.12 %). There is therefore no cheap
"keep one stage in fp32" variant; the choice is between the whole kernel in bf16 and the
whole kernel on the CPU.

In context: at the level of a whole mixer with random weights, the reference deviates
0.56 to 0.59 % from an fp32 evaluation and the all-bf16 rewrite 0.84 to 0.90 %
[V, study I]. The kernel's extra error is of the same order as the noise the reference
already carries in its bf16 linears. This is encouraging but is a random-weight result.

---

## 6. Precision analysis across the whole model

### 6.1 What bf16 changes and what it does not

- bf16 has the fp32 sign and 8-bit exponent and 8 significant bits. Its range, including the
  point where `exp` underflows, is the same as fp32; its relative resolution is 2^-8
  (0.39 %) worst case, about 0.17 % RMS per rounding [V, floor rows in study C].
- The concern raised with the proposal, that `exp(cum)` factors "may underflow in bf16", is
  therefore a resolution problem, not a range problem. Factors that underflow do so in the
  fp32 reference at the same point, and zero is the correct limit there. Subnormal handling
  on the NPU is unknown [A]; it only affects values below 1e-38.
- No operation in the proposed graph can overflow: every Exp argument is non-positive,
  Sigmoid and Softmax are bounded, and RMSNorm squares overflow only above about 1e19.

### 6.2 Where the reference is fp32 and the NPU graph is not

| Island in the reference | NPU graph | Kind of error introduced | Size |
|---|---|---|---|
| Delta-rule kernel | bf16 | random, accumulates over about ten stages | 0.4 to 1.8 % per head against 0.17 % [V, study C] |
| Decay gate (softplus, exp(A_log)) | bf16 | random if the softplus of 5.4 is used; systematic and large with the Log form | 0.1 to 0.3 % kernel-output error [V, study D]; constant up to 0.39 % |
| RMSNorm internals (80 instances in the graph) | bf16 | random | 0.36 % against 0.17 % [V, study D] |
| RMSNorm gain `1 + w` | constant rounded | systematic per channel unless written as `y + y w` | mean 0.15 %, max 0.39 % [V, study J] |
| Gated RMSNorm internals, `silu(gate)` | bf16 | random | as RMSNorm |
| Final RMSNorm | kept in fp32 on the CPU | none | |
| Heads | kept in fp32 on the CPU | none | |

Unchanged in kind (bf16 in both): all linear layers, the convolution, SiLU in the MLP,
residual additions, RoPE, attention scores and softmax.

### 6.3 Unknowns specific to the NPU

| Unknown | Why it matters | How to settle |
|---|---|---|
| Accumulation precision inside MatMul and ReduceSum kernels | bf16 accumulation over 2,560 or 9,216 terms would be far noisier than the emulation | micro-graph on the NPU against numpy, M0b |
| Rounding mode (nearest-even or truncation) | truncation biases every residual addition in one direction | same |
| Accuracy of Exp, Sigmoid, Sqrt, Softmax, Tanh kernels | table- or polynomial-based kernels can be less accurate than one bf16 rounding, especially Exp for arguments below -20 | sweep each unary op over its real input range, M0b |
| Whether listed ops run on the array or on flexmlrt's CPU runtime | affects speed, not results | timing, M0b |

### 6.4 Tolerance yardsticks

Absolute tolerances for bf16 results cannot be justified a priori. Three measured yardsticks
make them principled; all three are CPU-only and belong to milestone M1.

| Symbol | Definition | Meaning |
|---|---|---|
| R | authors' code, bf16 weights, CPU, torch kernels, `tokens_per_batch=1024` | the parity target |
| R32 | the same code with every weight widened to fp32 (16.8 GB in RAM), so that every op runs in fp32 | the model without bf16 noise |
| R8 | the authors' int8 weights (`int8=True`, a separate 4.2 GB download) | a perturbation the authors published as acceptable ("within 0.007 on the ternary rows") |
| E16 | the export module of section 7.4 run in torch with bf16 tensors, inside the authors' `Detector` | prediction of the NPU result |

Y1 = distribution of |R - R32| and Y2 = distribution of |R8 - R| over logits and
probabilities on a fixed text set. The port is acceptable if |E16 - R|, and later
|NPU - R|, is no larger than Y2 at the 95th percentile and produces no more verdict changes
than R8 does. If the int8 weights are not downloaded, the criterion falls back to twice Y1.

---

## 7. Graph partitioning, shapes, export, compile, fallbacks

### 7.1 Static shape

- Batch 1, T = 1024. Graph input `h` FLOAT `[1024, 2560]` (the batch axis is dropped inside
  the graph so that no tensor exceeds rank 4); output `h` of the same shape.
- No attention mask, no length input. Positions after the real tokens hold the embedding of
  `pad_id`; causality makes them irrelevant for earlier positions [V, study H].
- The pooled state and all unit features are gathered on the CPU from the returned states.

### 7.2 Segments

| | Proposal | This plan |
|---|---|---|
| Layers per segment | 8 | 4 (three Gated DeltaNet + one attention; layers 4s to 4s+3) |
| Segments | 4 | 8 |
| Parameters per segment | 892.5 M | 446,256,192 [V] |
| ONNX size (FLOAT) | 3.57 GB, needs external data | 1.785 GB weights + about 0.02 GB constants, single file [E] |
| Non-Constant nodes per segment | about 2,600 | about 1,300 (prototype; Vanguard's partition has 1,386) [V per layer] |

Reasons for the change:

- The compiler input is a FLOAT graph (section 2.4). Eight layers exceed the 2 GB protobuf
  limit. Compilation from an external-data model is not established: AMD's own example
  compiles the single-file model and only runs the external-data copy [V article, A here].
- A 4-layer segment is 1.3 times Vanguard in parameters and about equal in node count, the
  smallest extrapolation from what is proven that still keeps the session count manageable.
- All eight segments have the same structure. The first successful compile predicts the
  other seven, and a failed compile is found after minutes, not hours.

Segment hand-off is numerically free: the NPU returns bf16 values, widening to FLOAT is
exact, and feeding a bf16-representable FLOAT tensor to the next segment converts back
exactly. Splitting therefore cannot change results [V by construction; test 10.4-S3].

Costs: 8 sessions and 8 NPU hardware contexts, 7 host round trips of 10.5 MB each. The
driver's hardware-context limit was not determined [A].

### 7.3 Length buckets

Not in the first version. A second bucket (512) means 8 more compiles, about 14.5 GB more
ONNX, about 4.4 GB more compiled cache [E], 8 more contexts and a second copy of all
NPU-side weights unless the runtime shares them between contexts [A]. Results across buckets
agree only to rounding, never bit for bit. The question should be reopened after M0: if the
NPU is fast enough at 1024 for buckets to matter, the measured numbers will say which sizes
pay off. If short texts dominate the use case, the CPU reference is the faster backend for
them at any plausible NPU speed (section 8).

### 7.4 Export procedure (design)

1. Read the tensors of one segment from `model.safetensors` (bf16) and widen them to fp32.
2. Build the export module from the prototype design in sections 4 and 5 (the scratch file
   `rewrite_layers.py` is a working sketch of it). Rules for the module:
   - trace-friendly: fixed Python integers for all shapes, Python loops for the 16 chunk
     steps and 5 inverse levels (the tracer unrolls them);
   - constants as buffers computed at construction: interval matrix, prefix and suffix
     matrices, level masks, identity, RoPE tables rounded to bf16, causal mask, `-exp(A_log)`;
   - no indexing by integer on activations (`x[:, c]` exports as Gather): use `torch.split`
     once and reshape, so the graph has one Split per tensor;
   - no `repeat_interleave`, `tril`, `triu`, `cumsum`, `masked_fill`, `softplus`, `rsqrt`,
     `pow`, `scaled_dot_product_attention`, `F.conv1d`, dtype casts or shape queries;
   - tensors of rank 4 or lower.
3. `torch.onnx.export(module, h, path, opset_version=17, do_constant_folding=True,
   dynamo=False)`, as in `scripts/export.py` [V: this exporter produced a valid graph for the
   prototype, study H].
4. Checks before any compile (section 10.6): op inventory against an allow-list, no
   initializer above 2 GB in total, every weight initializer bf16-representable, all shapes
   static, ONNX Runtime CPU result equal to the torch module.
5. Export-time memory about 6 GB per segment [E: 1.8 GB module plus exporter copies].

### 7.5 Compile plan

| Item | Value | Status |
|---|---|---|
| Order | micro-graphs (M0b), then segment 0 alone, then segments 1 to 7 | |
| Config | the existing BF16 config (`target: VAIML`, `preferred_data_storage: unvectorized`), one `cache_key` per segment | [V] existing flow |
| Time per segment | 8 to 25 min | [E]: Vanguard took 466 s at a similar node count with 0.77 times the weights and matrices a quarter of the size; from Fakespot to Vanguard time grew 9.4 times for 2.9 times the nodes and 4 times the weights, so the scaling law is unknown |
| Time, 8 segments | 1 to 3.5 h | [E] |
| Peak RAM during compile | unknown; AMD recommends at least 32 GB for large BF16 models; 46 GB were available | [A] |
| Compiled cache | about 4.4 GB if 1.22 bytes per parameter holds | [E] |
| Preconditions | GUI server stopped; nothing else using the NPU; one compile at a time | |
| Success criterion | one partition per segment, device VAIML, no node of the layer body left outside | test 10.7 |

### 7.6 Hybrid fallback (delta rule on the CPU in fp32)

Use only if M1 shows that the all-bf16 kernel breaks parity.

- Cut each Gated DeltaNet layer at the kernel. NPU piece "pre": input norm, `in_proj_qkv`,
  convolution, SiLU, `in_proj_z`, and the raw gate projections. CPU: sigmoid for beta,
  softplus for g and the authors' kernel in fp32, exactly as the reference. NPU piece
  "post": gated norm, `out_proj`, residual, MLP. A "post" piece merges with the next "pre"
  piece and with any attention layer in between, giving 25 NPU graphs for 24 kernels.
- Per hand-off: 8,192 + 4,096 + 64 values per token out (about 51 MB as FLOAT, 61 MB with the
  residual stream) and 4,096 per token back.
- Cost: the authors' kernel takes 47 ms per layer on random tensors at the real shapes, so
  1.1 s per window for 24 layers on 12 threads [V, study E], plus 48 transfers.
- 25 sessions exceed the 8 of the main plan; the context limit is unknown [A]. Alternative:
  keep 8 ONNX files and let nodes that the NPU compiler rejects fall to the ONNX Runtime CPU
  provider inside one session. This depends on partitioner behaviour that was not tested [A].
- Precision: restores the reference's fp32 islands for the kernel and the gate; RMSNorm
  internals stay bf16.

By the current numbers the hybrid is slower than the CPU reference (section 8). It is a
correctness fallback only.

### 7.7 CPU reference backend

The authors' code on the CPU is both the parity target and a usable backend: 8.4 GB of
weights in RAM, no export, no compile, cost proportional to text length. Per the
coordinating agent it is being integrated as the `mesmer4b` registry entry with
`tokens_per_batch=1024`, so that each window runs alone at its own length (padded to a
multiple of 16, not to the longest window of a batch). That setting also makes this backend
the reference R of section 6.4 without further changes.

---

## 8. Performance analysis

### 8.1 Work per 1024-token window

| Part | TFLOP | Basis |
|---|---|---|
| Linear layers (projections and MLP), 32 layers | 7.31 | 2 x 1024 x parameter count [V counts] |
| Attention products, 8 layers | 0.14 | two products of 16 x 1024 x 1024 x 256 |
| Delta-rule core, 24 layers, C = 64 | 0.20 | section 5.9 |
| Total | 7.65 | [E] |

The proposal's 7.3 TFLOP is the linear part alone.

### 8.2 CPU, measured on synthetic tensors

All with 12 threads, torch 2.10 CPU, random tensors and random weights [V].

| Measurement | Result |
|---|---|
| `F.linear` 2560 to 9216, 1024 rows | bf16 20.6 ms (2.35 TFLOPS); fp32 71.4 ms (0.68) |
| `F.linear` 9216 to 2560 | bf16 22.1 ms (2.19); fp32 54.3 ms (0.89) |
| `F.linear` 2560 to 8192 | bf16 18.7 ms (2.30); fp32 60.5 ms (0.71) |
| Authors' delta kernel, fp32, C = 64, 32 heads, 1024 tokens | 47.3 ms per layer |
| GEMM-only kernel, fp32, C = 64 | 56.3 ms per layer |
| Synthetic full window, T = 1024 (all linears in bf16, fp32 kernel, attention), six consecutive runs | 4.75 to 5.03 s: linears 3.5 to 3.75 s, delta kernel 1.02 to 1.09 s, attention 0.15 to 0.18 s |
| Same, T = 512 | 2.41 s |
| Same, T = 256 | 1.20 to 1.23 s |

The synthetic window omits norms, convolution, gates, heads and tokenisation, and shares
random weights between layers. Expected real reference from this: 5 to 6 s per full window
[E].

Measured on the real model by the coordinating agent during the audit (authors'
`analyze()`, bf16 weights, 12 threads; reported to the auditor, not reproduced [A]):

| Text | Windows | Time | Note |
|---|---|---|---|
| 988 normalised tokens | 1 | 5.7 s | 7.65 TFLOP x 988/1024 in 5.7 s = 1.3 TFLOPS effective; equivalent to 5.9 s for a full 1024-token window |
| 1040 tokens | 2, batched with `tokens_per_batch=16384` | 11.7 s | both windows are padded to the longer one, so the short second window costs as much as a full one |

The measurement agrees with the synthetic estimate. With `tokens_per_batch=1024` the second
window of the 1040-token text holds its own tokens plus at most 255 context tokens, so it
should cost about a third of a full window [E]. The
task brief reported 1.60 TFLOPS for the same kind of micro-benchmark; this audit measured
2.2 to 2.35 on an otherwise idle machine. Sustained behaviour over many windows (thermal
limits) was observed for 30 s only.

### 8.3 NPU, projected

| Step | Value | Status |
|---|---|---|
| Vanguard: about 0.75 to 0.82 TFLOP in 433 ms | 1.7 to 1.9 TFLOPS effective | [A] timing from the brief, [E] FLOPs |
| Mesmer window at that rate | 4.1 to 4.6 s | [E] |
| Per-node overhead | Vanguard averages 0.31 ms per node including its heavy nodes; about 10,400 mostly small nodes could add between a fraction of a second and 3 s | [E], upper bound |
| Segment hand-offs, embedding, final norm, heads | well under 0.1 s | [E] |
| Hybrid variant | NPU 3.9 to 4.4 s for the non-kernel work plus 1.1 s CPU kernel plus 48 transfers: 5.0 s or more | [E] |

### 8.4 Reading

- Full window: NPU 4.1 to 4.6 s plus node overhead [E]; CPU 5.9 s (reported measurement).
  The ratio is 1.3 to 1.4 if node overhead is negligible and falls to about 0.8 if the
  overhead reaches its upper bound. There is no evidence for the proposal's 2 s.
- Multi-window documents favour the CPU further: every window after the first re-reads up
  to 255 context tokens, and the last window is usually short. The CPU pays for the actual
  length of each window; the static graph pays 1024 tokens every time.
- For a text of 256 tokens the CPU needs about 1.2 to 1.5 s and the static NPU graph the
  full 4 s or more.
- The earlier Vanguard result (NPU 433 ms against CPU 1771 ms) used ONNX Runtime in fp32 on
  the CPU, about 0.45 TFLOPS. The same CPU reaches about five times that in bf16 through
  torch. The comparison that matters for Mesmer is against CPU bf16.
- Reasons other than speed that could still justify the NPU: leaving the 12 cores free, and
  lower power draw and fan noise during long documents. These were not measured.

### 8.5 Decision rule

Proceed with the NPU port only if milestone M0b projects a full-window NPU time of at most
3.9 s, two thirds of the 5.9 s CPU figure (a 1.5 times gain), or if the user decides that
freeing the CPU is worth a port at equal speed. On the present projection (4.1 to 4.6 s
before overhead) the gate is not met; M0b exists to replace that projection with a
measurement at Mesmer's matrix sizes.

---

## 9. Integration plan for the repository (design only)

State assumed, as announced by the coordinating agent during the audit: the Fakespot and
Vanguard entries are removed; `detector/models.py` gains a `mesmer4b` entry that runs the
authors' code on the CPU; `server/serve.py` and `server/web/index.html` are being changed to
show three classes, the calibrated verdict and per-sentence labels; `detector/runtime.py`,
`detector/chunking.py`, `scripts/export.py` and `scripts/compare.py` stay. The auditor did
not see those changes; this section describes how an NPU backend would attach to them.

### 9.1 Principle: one seam, at the backbone

Mesmer should not be forced into the `ModelSpec` / `chunk_text` / `score_chunks` path. That
path assumes a Hugging Face sequence classifier, overlapping token windows, one probability
per window and a `[CLS] ... [SEP]` layout. Mesmer has sentence-aligned windows with
re-read context, an `eos` pooled token, two heads, three classes and its own aggregation.

The authors' `Detector` touches the backbone in exactly two places, both of the form
`hs = self.backbone(x)` with `x` an int tensor `[B, T]` and `hs` a float tensor
`[B, T, 2560]` (lines 564 and 592) [V]. Everything else is independent of how `hs` was
produced. The NPU backend is therefore one object:

```
class NpuBackbone:
    def __call__(self, input_ids):          # [1, 1024] int
        h = embedding rows from the memory-mapped table, widened to fp32
        for session in the 8 segment sessions: h = session.run(h)
        h = final RMSNorm in fp32, rounded to bf16 values
        return torch tensor [1, 1024, 2560], fp32 dtype
```

and the detector is configured with `pad_to = 1024` and `budget = 1024`, which makes every
call a single window padded to the static length (section 3.1). `analyze`, `predict`,
`_forward_both`, the heads, `verdict` and all text handling run unchanged.

### 9.2 Loading without the torch backbone

`Detector.__init__` (lines 501-536) loads all 8.4 GB and builds the torch backbone. The NPU
backend needs only the tokenizer, `config.json`, `policy.json`, the `head.*` and `seg.*`
tensors (8.4 M parameters) and the embedding byte range. Design: a small factory in the
repo that creates the object with `Detector.__new__`, sets the same attributes as lines
506-533, reads the head tensors with `safetensors.safe_open`, and installs `NpuBackbone`.
It duplicates about 20 lines of attribute set-up; a stored SHA-256 of `mesmer_detector.py`
is checked at load so that an upstream change of the file cannot silently break the
duplicate.

The authors' file is imported from `artifacts/mesmer4b/hf/` by path. It is not copied into
the repository: the model is CC BY-NC-SA 4.0 and the repository is public; exported ONNX
files and compiled caches are derivatives and stay under the untracked `artifacts/` and
`~/.cache`. Whether repository code that duplicates part of `__init__` is affected by the
share-alike term is a question for the user [A].

### 9.3 Registry and runtime

| Element | Now | Proposed |
|---|---|---|
| `ModelSpec` | `seq_len`, `head`, `ai_index`, single `onnx_path` | keep for generic classifiers. For Mesmer add a `backend` field with values `"reference-cpu"` (authors' torch code, the announced state) and `"npu-segments"`; `seq_len`, `head`, `ai_index` do not apply to it |
| Paths | `artifacts/<name>/onnx/model_static.onnx`, `~/.cache/npu_models/<name>` | `artifacts/mesmer4b/onnx/seg<k>/model_static.onnx` for k = 0..7; cache key `mesmer4b_seg<k>_bf16` under the existing cache directory |
| `runtime.make_session(spec, npu)` | derives path and key from the spec | generalise to take an ONNX path and a cache key; `write_bf16_config` is reused as is |
| Availability check | `spec.onnx_path.exists()` | `reference-cpu`: `model.safetensors` and `mesmer_detector.py` exist. `npu-segments`: all eight ONNX files exist |
| `scripts/export.py` | Hugging Face classifiers | unchanged; a separate `scripts/export_mesmer.py` exports one segment per call (section 7.4) |
| `scripts/compare.py` | CPU against NPU for one text | a Mesmer counterpart that runs the same text through both backends and prints logits, probabilities, verdict and the number of differing sentence labels |
| Tests | none | a `tests/` directory holding section 10; `pytest` is not installed, so either plain scripts with assertions or one more package |

Both backends should be loadable at the same time only for comparison runs; the server
should hold one. Memory with both: 8.4 GB (torch) plus the NPU-side weights.

### 9.4 Server

- The single lock that serialises scoring stays; it also protects the NPU.
- Backend choice per start: the existing `--cpu` flag selects `reference-cpu`. If the NPU
  backend is absent or fails to load, fall back to `reference-cpu` and say so in the
  `/api/models` response.
- The response should say which backend produced it (`"backend": "reference-cpu"` or
  `"npu-segments"`), because the two are numerically different implementations of the same
  model and a verdict near a threshold can differ.
- A full window takes about 6 s and a long document several windows. The request is
  synchronous today. Add a `windows` count to the response and, if long documents matter,
  a progress field polled by the page. The page needs a visible busy state for tens of
  seconds either way.
- One window, one call: keep `tokens_per_batch=1024` for both backends so that their
  windowing and padding behaviour is identical and results are comparable.

### 9.5 API fields for three classes

Whatever the coordinating agent has implemented takes precedence; the points below are the
requirements the audit derives from the reference.

| Field | Source | Note |
|---|---|---|
| `verdict` | `analyze()["verdict"]` | one of `human`, `ai`, `ai_edited`, decided by `policy.json`. The page must not derive a verdict from a percentage; the five score bands of `docs/gui-plan.md` do not apply |
| `probs` | `analyze()["probs"]` | three numbers |
| `flagged_fraction`, `words` | `analyze()` | `words` drives the short-text warning |
| `segments` | `analyze()["sentences"]` | each with `text`, `label`, `p`. The existing contract is that the segment texts joined in order reproduce the input; sentence spans are stripped and leave gaps, so each segment's text must be extended to the start of the next span (the first from 0, the last to the end) |
| scalar for the ring | open | candidates: `100 * (1 - p_human)` ("any AI involvement") or `100 * p_ai`. The decision rule uses `p_ai + 0.5 p_edit` against 0.6084 and `1 - p_human` against 0.907, so no single scalar reproduces the verdict; the verdict text must come from `verdict` |
| `backend`, `model` | server | see 9.4 |

Character offsets are not sent, for the reason already recorded in `docs/gui-plan.md`
(Python and JavaScript index strings differently).

### 9.6 Page

- Ring: show the chosen scalar; colour by verdict (three states), not by score band.
- Probabilities: a three-part bar for human / AI / AI-edited.
- Text shading: per sentence, by label (none for `human`, one hue for `ai`, another for
  `ai_edited`), intensity by `1 - p_human`; hover shows the three probabilities.
- Sentences that normalisation dropped (a chat-style first paragraph, a `<think>` block)
  receive a neighbour's probabilities in the reference (lines 650-654); mark them as "not
  scored separately" if the distinction is wanted, else keep the reference behaviour.
- Warnings from the model card: under about 50 words the result is unreliable; English only.
- Footer: model id, backend, and the existing line that a score is not proof.

### 9.7 Dependencies and environment

| Item | Action |
|---|---|
| `emoji` | install into `~/ryzen-ai-venv`; record the version in the golden-test metadata |
| `mesmer_detector.py` | record SHA-256; refuse to start on mismatch |
| `tokenizers`, Python (`unicodedata`) | record versions with the golden outputs |
| Import isolation | load the authors' file with `importlib` from its path; it is the only code executed from the download directory, and it was read in full for this audit |

---

## 10. Test plan

### 10.1 Conventions

Where tests run:

- **CPU**: needs neither the NPU nor a compile. Everything up to and including the bf16
  emulation.
- **NPU**: needs a compiled graph and exclusive use of the NPU.

Reference configurations R, R32, R8, E16 are defined in section 6.4. "Teacher-forced" means
the input of a layer or segment is the reference's own hidden state at that depth, so errors
do not compound.

Tolerances come from two sources. For fp32 and fp64 comparisons they are fixed numbers, set
at 3 to 10 times the worst value observed in the synthetic studies, and are meant to catch
implementation errors. For bf16 comparisons they are relative to the yardsticks Y1 and Y2
measured on the same texts, because an absolute bound cannot be justified before the real
model has been run. The few absolute numbers in the bf16 criteria (a probability margin of
0.05 in E5 and F2, 2 of 500 texts in F2, 0.2 % in F3) are provisional choices of this audit
and should be revisited once Y1 and Y2 are known.

Text sets:

| Set | Content | Size | Use |
|---|---|---|---|
| T-smoke | 12 texts: human, AI, AI-edited at about 60, 300, 1000, 3000 words | 12 | every run |
| T-edge | pre-processing edge cases (10.5) | about 40 | golden tests |
| T-parity | mixed human and AI texts, about one window each | 300 | gates G1, G3 |
| T-human | human-written texts only | 500 for gates, 3,000 for the final check | false-positive regression |

Candidate public sources named on the model card: MELD-eval, DetectRL (human subset), the
TOEFL non-native essays, Human Detectors, Enron emails, RAID. Dataset identifiers, licences
and availability were not checked [A]. The user's own human-written texts are a valid and
relevant addition.

### 10.2 Unit tests for rewritten ops and the kernel (CPU)

| ID | Test | Tolerance | Basis |
|---|---|---|---|
| U1 | softplus form of 5.4 against fp64 softplus on [-30, 30], evaluated in fp32 | max relative error 1e-5 | observed 1.8e-6 |
| U1b | same with every op rounded to bf16 | max relative error 2.5e-2 on [-10, 10] | observed 1.3e-2 |
| U1c | real `A_log`, `dt_bias`: number of heads with g exactly 0, and error of `exp(1024 g)` | 0 heads; at most 0.01 | observed 0 and 0.003 |
| U2 | interval-sum decays against `exp` of cumulative-sum differences, fp64, gates drawn from the real parameters | 1e-12 absolute | algebraic identity |
| U3 | recursive inverse against `torch.linalg.solve_triangular`, fp64, keys with shared component 0, 0.6, 0.9, 0.99 and with token persistence 0.9 | 1e-12 relative | observed about 1e-15 |
| U3b | same in fp32: residual `max |(I + N) Tinv - I|` | 1e-4 | observed kernel errors below 1e-6 |
| U3c | regression guard: the nilpotent product must fail U3b for shared component 0.9 | documents why it is not used | observed 1e+21 |
| U4 | full kernel of 5.7 against the authors' kernel and against the fp64 recurrence, fp32, real shapes | per-head relative error 5e-6 | observed at most 1e-6 |
| U5 | full kernel with every op rounded to bf16 against the fp64 recurrence, gate parameters of layers 0, 1, 10, 26, key models as in U3 | median 2.5e-2, maximum 4e-2 per head, no non-finite value | observed 1.65e-2 and 1.8e-2 |
| U6 | shifted multiply-add convolution against `torch_causal_conv1d`, fp32 | 1e-6 relative | exact regrouping |
| U7 | RMSNorm decomposition, `y + y w` gain, and the LayerNormalization-on-`[x, -x]` form against the authors' `RMSNorm`, fp32 | 1e-6 relative | |
| U8 | grouped-query fold against `scaled_dot_product_attention(enable_gqa=True)`, fp64 | 1e-12 | observed 9e-16 |
| U9 | RoPE tables in the export module against the reference tables after the bf16 cast | bit-identical | same formula |
| U10 | Sigmoid fallbacks (Tanh form, 2-way Softmax) against `torch.sigmoid`, fp32 | 1e-6 absolute | |
| U11 | memory-mapped embedding rows against the tensor loaded by safetensors, 10,000 random ids | bit-identical | |
| U12 | every weight initializer of an exported segment is bf16-representable | exact | by construction |

### 10.3 Layer parity (CPU)

| ID | Test | Tolerance |
|---|---|---|
| L1 | Gated DeltaNet layer of the export module against the authors' `Layer`, random fp32 weights, real head counts and dimensions, T = 1024 | relative 5e-6 (observed 3.7e-7) |
| L2 | attention layer, same set-up | relative 5e-6 (observed 1.4e-7) |
| L3 | each of the 32 real layers in fp32, teacher-forced with R32 hidden states from T-smoke | relative 1e-5 per layer |
| L4 | each real layer in the bf16 emulation (E16), teacher-forced with R hidden states, against R's next hidden state | recorded per layer; pass if at most twice the same layer's R-against-R32 deviation |
| L5 | L4 statistics also for the kernel output alone (hook on the mixer), reporting key correlation within chunks | diagnostic; replaces the synthetic key models of study C with measured ones |

L3 to L5 require running the real model on the CPU; they are the first tests that do.

### 10.4 Segment parity

| ID | Where | Test | Tolerance |
|---|---|---|---|
| S1 | CPU | exported segment in ONNX Runtime (CPU provider, fp32) against the torch export module in fp32, random input and T-smoke hidden states | max absolute difference 1e-4 of the output RMS (observed 2e-6 for single layers) |
| S2 | CPU | exported segment (ONNX, fp32) against R32, teacher-forced | relative 5e-5 |
| S3 | CPU | chain of 8 segments in ONNX fp32 against R32 end to end; and the same chain with each hand-off rounded to bf16 against E16 with rounding at the same places | logits within 5e-3 for the fp32 chain (to be confirmed on first run); hand-off rounding is idempotent on bf16-representable tensors |
| S4 | NPU | one compiled segment against E16 and against R, teacher-forced | pass if its deviation from R is at most twice E16's deviation from R; record both |
| S5 | NPU | all 8 compiled segments chained against R | section 10.8 |

### 10.5 Pre-processing (CPU)

The code is reused unchanged, so these tests guard the environment, not a port.

| ID | Test |
|---|---|
| P1 | golden outputs of `normalize_text`, `split_units`, `normalize_units`, the token ids, and the window tuples (`ids`, `us`, `ue`, `owned`, unit indices) for T-edge, stored with the `emoji`, `tokenizers`, Python and file-hash versions; any change fails |
| P2 | T-edge contents: empty and whitespace-only text; under 3 words; no sentence punctuation; a `<think>...</think>` block; each of the six chat-style openers with and without a following paragraph; emoji; zero-width and variation-selector characters; fullwidth and mathematical letters; Cyrillic and Greek look-alikes inside Latin words and inside genuine Cyrillic text; lists and blank lines; a single sentence above 1,023 tokens; a window with more than 512 units (position clamp, line 494); text that needs exactly 1,023 and 1,024 tokens; text whose second window re-reads the maximum context |
| P3 | `analyze` output invariants: spans are ordered and non-overlapping; extended segment texts joined reproduce the input; unit probabilities contain no NaN; owned counts sum to the number of kept units |
| P4 | with `pad_to = budget = 1024` every backbone call has shape `[1, 1024]`; with the CPU backend at `tokens_per_batch=1024` every call has batch 1 |
| P5 | `predict` and `analyze` are both exercised; they tokenise differently by design |

### 10.6 Static checks on every exported graph (CPU)

| ID | Check |
|---|---|
| O1 | op inventory equals an allow-list: MatMul, Mul, Add, Sub, Div, Neg, Exp, Sqrt, Sigmoid, Abs, Softmax, ReduceSum, Slice, Split, Concat, Reshape, Transpose, Squeeze, Constant. Any other op fails the export. The list is narrowed after M0b to what the NPU accepted |
| O2 | no Gather, Cast, Shape, Expand, Where, Trilu, CumSum, Loop, If, Softplus, Pow, Unsqueeze, ConstantOfShape |
| O3 | all value shapes static and of rank 4 or lower (shape inference) |
| O4 | file below 2 GB; opset 17; only FLOAT tensors |
| O5 | node count per segment recorded and compared with the previous export |
| O6 | U12 on the initializers |

### 10.7 Compile checks (NPU)

| ID | Check |
|---|---|
| C1 | session creation succeeds; `context.json` shows exactly one partition with device VAIML |
| C2 | the partition's node list covers every non-Constant node of the graph (the cross-reference method of section 2.3) |
| C3 | compile time, peak RSS of the compiling process, and cache size recorded per segment |
| C4 | second session creation hits the cache (seconds, not minutes) |
| C5 | all eight sessions can be open in one process at the same time |

### 10.8 End-to-end parity

Run on T-smoke first, then T-parity. Compared quantities: document logits before
aggregation (per window), document probabilities, verdict, per-sentence probabilities and
labels, `flagged_fraction`.

| ID | Where | Comparison | Criterion |
|---|---|---|---|
| E1 | CPU | Y1 = R against R32; Y2 = R8 against R | recorded; these define the scale |
| E2 | CPU | E16 against R | 95th percentile of the absolute logit difference at most that of Y2 (or twice that of Y1 if R8 is not available); verdict changes no more than R8's; sentence-label changes no more than R8's |
| E3 | NPU | NPU against R | same criteria as E2 |
| E4 | NPU | NPU against E16 | recorded; a large gap means the emulation model of the NPU arithmetic is wrong (accumulation precision, rounding mode, unary-op accuracy) and section 6.3 must be revisited |
| E5 | both | every verdict change is listed with its margin to the nearest threshold; a change at a margin above 0.05 in probability is a failure regardless of the counts | a perturbation of the size measured in study I should not move a probability by that much |

### 10.9 Invariance and property tests

| ID | Where | Property | Criterion |
|---|---|---|---|
| I1 | CPU, NPU | padding content: replace the pad positions by random token ids | states at real positions bit-identical (observed for the fp32 prototype); on the NPU bit-identical or the difference is reported as a finding |
| I2 | CPU | prefix property: the states of the first n tokens do not change when tokens are appended | bit-identical in the export module |
| I3 | CPU | chunk size 32, 64, 128 in the export module, fp32 | relative 1e-5 |
| I4 | CPU | same, bf16 emulation | within the spread of U5 |
| I5 | CPU, NPU if buckets exist | bucket length: the same text at 512 and at 1024 | fp32 relative 1e-5; bf16 within E2's scale |
| I6 | CPU | window boundaries: a text just below and just above 1,023 tokens gives the documented one and two windows; document probabilities equal the owned-unit weighted mean of window probabilities recomputed by hand | exact |
| I7 | CPU | reference batch independence: R with `tokens_per_batch` 1024 against 16384 | recorded; shows how much the reference itself moves with batching and padding |
| I8 | CPU | segment split: 8 segments of 4 against one 32-layer module in torch | bit-identical in fp32 |

### 10.10 Policy and false-positive regression

The thresholds in `policy.json` were set on the authors' held-out human texts, which are not
available. An absolute false-positive rate on any other corpus is therefore not a pass/fail
quantity; the paired difference between the port and the reference on the same texts is.

| ID | Where | Test | Criterion |
|---|---|---|---|
| F1 | CPU | R on T-human: fraction called `ai`, fraction with any flag, fraction of flagged sentences | recorded as the baseline for this corpus |
| F2 | CPU | E16 on T-human (500 texts) | number of texts whose verdict differs from R at most that of R8 (or at most 2 of 500 if R8 is unavailable); no text moves from `human` to `ai` at a margin above 0.05 |
| F3 | NPU | NPU on T-human (500, then 3,000) | same as F2; in addition the count of `ai` verdicts and of any-flag verdicts on human texts may not exceed R's by more than 0.2 % of the set |
| F4 | both | margin histogram: distance of `p_ai + 0.5 p_edit` to 0.6084 and of `1 - p_human` to 0.907 and, per sentence, to 0.8696, for R | shows how many texts sit within the perturbation scale of a threshold; this is the population at risk |
| F5 | both | the same counts on an AI-written subset of T-parity | detection must not drop by more than R8's change |

Cost: at about 6 s per window, 500 one-window texts take about 50 min per configuration and
3,000 take about 5 h [E].

### 10.11 Determinism

| ID | Where | Test | Criterion |
|---|---|---|---|
| D1 | CPU | R twice on T-smoke with the same thread count | bit-identical logits; if not, the run-to-run spread is recorded and added to the yardsticks |
| D2 | NPU | the same window 20 times | bit-identical outputs |
| D3 | NPU | after a process restart and after a cache reload | bit-identical to D2 |
| D4 | NPU | with another process using the NPU, if that is ever allowed | identical or documented |

### 10.12 Performance

| ID | Where | Measurement |
|---|---|---|
| B1 | CPU | R: seconds per window at 128, 256, 512, 768, 1023 tokens; a 10-window document; 20 consecutive full windows to expose thermal limits; peak RSS |
| B2 | NPU | micro-graphs of M0b: seconds for one MLP block at the real shape; seconds for 200 small batched MatMuls; hence effective TFLOPS and per-node overhead |
| B3 | NPU | per segment and for the chain: seconds per window, cold and warm; time to open all sessions; RSS; hand-off time separated from session time |
| B4 | both | the same documents end to end through the server, including tokenisation and heads |
| B5 | NPU | CPU utilisation while the NPU runs, to quantify the "CPU stays free" argument |

---

## 11. Milestones and gates

Ordered by cost; each gate can end the project early.

| # | Milestone | Needs | Effort | Gate |
|---|---|---|---|---|
| M0a | CPU reference integrated and timed. Reported during the audit: 5.7 s for a 988-token window. Remaining: store R's outputs for T-smoke as golden values, run B1 | CPU | done / hours | none: this is the baseline |
| M0b | **NPU micro-benchmark, random weights, no Mesmer weights.** Three tiny graphs: (1) one MLP block at the real shape, 1024 x 2560 to 9216 and back with SiLU and the product (0.145 TFLOP, 283 MB ONNX); (2) a chain of 200 batched MatMuls `[32, 64, 128] x [32, 128, 128]`; (3) Exp, Sigmoid, Sqrt, Abs, Sub, Div, Split, ReduceSum on small tensors swept over their real input ranges, compared with numpy | NPU, minutes of compile | half a day | **G0.** (a) Projected full window = 7.65 TFLOP / measured rate + 10,400 x measured per-node overhead is at most 3.9 s. (b) Every needed op, or its fallback from 4.12, lands in the partition and matches numpy within bf16 rounding. Fail (a): stop, keep the CPU backend. Fail (b) for Exp with no working fallback: stop |
| M1 | Export module in torch (sections 4, 5, 7.4), unit and layer tests U1-U12, L1-L3, I2, I3, I8; then the bf16 emulation E16 inside the authors' `Detector`; yardsticks Y1, Y2; tests L4, L5, E1, E2, F1, F2, F4 | CPU only | several days | **G1.** E2 and F2 pass. Fail: evaluate the hybrid (7.6) with the same tests; if G0(a) cannot hold for the hybrid, stop |
| M2 | Export segment 0, static checks O1-O6, S1, S2; compile it; C1-C4, S4, I1, D2, B3 | NPU | 1 to 2 days | **G2.** One partition, all nodes inside, compile under 1 h, S4 passes, measured segment time x 8 at most 3.9 s |
| M3 | Export and compile segments 1 to 7; C5; chain; S3, S5, E3, E4, E5 on T-smoke and T-parity | NPU, 1 to 3.5 h of compile [E] | 1 to 2 days | **G3.** E3 and E5 pass |
| M4 | False-positive regression F3, F5 on 500 then 3,000 texts; determinism D1-D4 | NPU and CPU, about 10 h of run time | 1 to 2 days | **G4.** F3 passes |
| M5 | `NpuBackbone` behind the backend switch (section 9); server and page wiring; B4, B5; documentation | both | 1 to 2 days | **G5.** End-to-end times confirm the gain measured in M2 |
| M6 | Optional: a 512 bucket, C = 128, node-count reduction, external-data run-time copy to cut memory | NPU | open | only if measurements justify it |

M0b is placed before M1 on purpose. It costs hours, uses no model weights, and decides the
question that the current evidence answers unfavourably. M1 is the expensive part and should
not start unless G0 passes.

Stop conditions in one place: G0(a) fails (no speed gain); an essential op has no accepted
form; G1 fails for both the all-NPU and the hybrid layout; compile of a 4-layer segment
fails or exceeds available memory; G3 or G4 fails and the cause cannot be traced to a
fixable op.

---

## 12. Resource estimates

| Resource | Amount | Status |
|---|---|---|
| Disk, exported ONNX | 8 x about 1.81 GB = 14.5 GB | [E] |
| Disk, compiled caches | about 4.4 GB (1.22 bytes per parameter, as for the two compiled models) | [E] |
| Disk, int8 weights for R8 | 4.2 GB | [V] model card |
| Disk, test corpora and golden outputs | under 1 GB | [E] |
| Disk, total | about 25 GB of 544 GB free; each extra length bucket adds about 19 GB | [E] |
| RAM, CPU reference | 8.4 GB weights plus activations | [V] file size |
| RAM, R32 | 16.8 GB weights | [E] |
| RAM, export of one segment | about 6 GB | [E] |
| RAM, compile of one segment | unknown; AMD: at least 32 GB recommended for large BF16 models; 46 GB available | [A] |
| RAM, NPU run time | at least 7.1 GB (weights as bf16) plus the 1.27 GB embedding map; up to about 21 GB more if each session keeps its FLOAT initializers, which AMD's article suggests the standard flow does | [E], [A] |
| Compile time | 8 to 25 min per segment, 1 to 3.5 h in total | [E] |
| NPU hardware contexts | 8 | limit [A] |
| Test run time | 50 min per 500 one-window texts per configuration; about 5 h per 3,000 | [E] |
| New packages | `emoji` (required by the reference); optionally `pytest` | [V] |

---

## 13. Open questions

1. NPU throughput and per-node overhead at Mesmer's matrix sizes (M0b). Everything else
   depends on it.
2. Which of Exp, Sigmoid, Sqrt, Abs, Sub the BF16 compiler accepts into the partition, and
   whether they run on the array or on the CPU runtime inside the partition.
3. Internal accumulation precision and rounding mode of NPU MatMul, ReduceSum and Add; the
   accuracy of the NPU's Exp for arguments down to about -700.
4. How correlated real key vectors are within a 64-token chunk. It decides how far the
   synthetic kernel errors of study C carry over (test L5).
5. Whether the detector's logits tolerate the extra bf16 noise (gates G1, G3). The only
   published hint is the authors' int8 result.
6. Hardware-context limit of the amdxdna driver for this NPU, and whether 8 contexts with
   7 GB of weights can stay loaded.
7. How the VAIML runtime stores weights (the `.rai` contains a file named `wts32.bin`) and
   whether the ONNX Runtime session keeps a FLOAT copy.
8. Compile behaviour for 20 to 24 M-parameter matrices and about 1,300 nodes per graph:
   time, memory, and whether one partition results.
9. Whether compilation from an external-data ONNX works; it would allow fewer, larger
   segments.
10. Which path the authors used to tune `policy.json` (`predict` on the first 1,023 tokens
    or `analyze`), and on what text lengths.
11. Versions of `emoji`, `tokenizers` and Python the authors used; they affect
    normalisation of unusual characters only.
12. Which scalar the ring should show for a three-class model.
13. Licence handling for derived ONNX and compiled artifacts and for repository code that
    mirrors part of the authors' loader.
14. Whether freeing the CPU or saving power is itself a goal. If it is, the gate in 8.5
    changes.

---

## Appendix A. Study log

The study scripts were kept in a temporary local scratch directory (`mesmer_audit/`)
and are not part of this repository. Python:
`~/ryzen-ai-venv/bin/python -I`, torch 2.10.0+cpu, 12 threads. No study loaded the Mesmer
backbone or ran a forward pass of the model. Studies B and J read files only.

| ID | Script | Purpose | Set-up | Result |
|---|---|---|---|---|
| A | `study_a_exact.py`, `gdr.py` | Is the GEMM-only rewrite algebraically exact, for which chunk sizes and which inverse method? | fp64; 8 heads, 256 tokens, dim 32; independent keys and keys with a shared component of 0.9; decays by cumsum-difference and by interval sums; inverse by nilpotent product, recursive blocks, forward substitution; C = 16, 32, 64, 128; truth = per-token recurrence | Recursive and forward: at most 1.4e-15 everywhere. Nilpotent product with shared keys: 4.5e-14 (C = 32), 3.6e-10 (C = 64), 3.5e-2 (C = 128), in fp64. Authors' kernel in fp32: 3e-7 to 4e-7 |
| B | `partition_ops.py`, `onnx_meta.py` | Which ops ran inside the NPU partitions of the two compiled models? | `context.json` node lists matched to ONNX node names and outputs; no session | Section 2.3 |
| C | `study_c_bf16.py`, `gdr.py` | Output error of kernel variants in bf16 | every op in fp32 then rounded to bf16; 32 heads, 1024 tokens, dim 128; gates from the real `A_log`, `dt_bias` of layers 0, 1, 10, 26 with a Gaussian gate logit; keys independent, shared 0.3 / 0.6 / 0.9, persistence 0.9; truth fp64 recurrence | Sections 5.3, 5.5, 5.9, 5.10. Proposal as written (cumsum-difference + nilpotent product): NaN or above 100 % once keys are correlated. Recommended form: 0.4 to 1.7 % median, at most 1.8 % |
| D | `study_d_elementwise.py` | bf16 accuracy of elementwise rewrites | every op rounded to bf16; softplus two ways; sigmoid two ways; RMSNorm two ways; grouped-query fold in fp64; gate rounded only | Sections 5.4, 4.3, 4.5, 4.10. Gate rounded to bf16 with an fp32 kernel: 0.02 to 0.07 % kernel error; gate through the proposed softplus: 0.1 to 0.3 % |
| E | `study_e_timing.py` | CPU cost of the kernel and of the dominant linears | random tensors at real shapes | Section 8.2 |
| F | `study_f_ablation.py` | Which kernel stage carries the bf16 error? | recommended kernel; one stage rounded at a time | Each stage 0.004 to 0.56 % (median); inverse 0.02 to 0.12 %; all stages 0.45 to 0.90 % |
| G | `study_g_window.py` | CPU cost of a whole window | random bf16 matrices of the real shapes applied in layer order, fp32 kernel, attention; T = 1024, 512, 256 | 4.75 to 5.03 s, 2.41 s, 1.20 to 1.23 s |
| H | `study_h_layer_parity.py`, `rewrite_layers.py` | Does the complete layer rewrite equal the authors' classes; what does it export to? | authors' `Layer`, `GatedDeltaNet`, `Attention` imported from `mesmer_detector.py` with random fp32 weights; hidden 96, real head counts and dims, T = 1024; legacy exporter, opset 17; ONNX Runtime CPU provider | Relative error 3.7e-7 (Gated DeltaNet layer), 1.4e-7 (attention layer); earlier outputs unchanged (0.0) when the last 300 inputs change; 404 and 89 non-Constant nodes; rank at most 4; ONNX Runtime within 2.2e-6 of torch |
| I | `study_i_layer_bf16.py` | Whole-mixer bf16 noise: reference against all-bf16 rewrite | random weights (bf16-representable), inputs with a shared component of 0, 0.7, 1.5; rewrite run with torch bf16 tensors | Gated DeltaNet mixer: reference 0.56 to 0.59 %, rewrite 0.84 to 0.90 %, no non-finite values. Attention: reference 0.30 to 0.47 %, rewrite 0.30 to 0.70 % |
| J | `st_header.py`, `gate_stats.py`, `norm_gain_stats.py` | Checkpoint structure and the statistics of gate and norm parameters | safetensors header; memory-mapped read of `A_log`, `dt_bias`, `in_proj_a`, `in_proj_b`, norm weights | Section 2.2; `1 + w` rounding error mean 0.15 %, max 0.39 % |

Limits of the studies: q, k, v and beta are synthetic; the gate logit is Gaussian with a
scale derived under an isotropic-input assumption; the bf16 emulation assumes each op is
computed in fp32 and rounded once; study I uses random weights. None of this replaces the
run on real weights in milestone M1.

## Appendix B. Sources

- Reference implementation: `~/npu_models/artifacts/mesmer4b/hf/mesmer_detector.py`
- Model cards: https://huggingface.co/mesmertech/mesmer-ai-detector-4b ,
  https://huggingface.co/mesmertech/mesmer-ai-detector-9b
- AMD Ryzen AI documentation: https://ryzenai.docs.amd.com/en/latest/modelrun.md ,
  https://ryzenai.docs.amd.com/en/latest/linux.md ,
  https://ryzenai.docs.amd.com/en/latest/ops_support.html
- AMD article, "Practical Technique for Reducing Memory Usage of BCE Models on Ryzen AI"
  (2026-02-05):
  https://www.amd.com/en/developer/resources/technical-articles/2026/practical-technique-for-reducing-memory-usage-of-bce-models-on-r.html
- Upstream delta rule and export path: `transformers` 5.19,
  `models/qwen3_5/modeling_qwen3_5.py` (`torch_chunk_gated_delta_rule`,
  `torch_recurrent_gated_delta_rule`)
- Yang, Kautz, Hatamizadeh, "Gated Delta Networks", arXiv:2412.06464
- Yang et al., "Parallelizing Linear Transformers with the Delta Rule over Sequence Length",
  arXiv:2406.06484

END OF DOCUMENT
