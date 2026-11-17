"""
Score texts with a registered detector model on the CPU and on the Ryzen AI NPU, and
compare the AI probability and latency per text. Long texts are split into overlapping
windows and combined by length-weighted mean.
Run from the repository root: python -m scripts.compare --model <onnx model> "text" ...

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import argparse
import time

from transformers import AutoTokenizer

from detector.chunking import aggregate, chunk_text
from detector.models import MODELS
from detector.runtime import make_session, score_chunks

DEFAULT_TEXTS: list[str] = [
    "I went to the market this morning and the bread was still warm, so I bought two loaves.",
    "In conclusion, leveraging synergistic frameworks enables stakeholders to unlock transformative value across diverse domains.",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("texts", nargs="*", help="Texts to classify (defaults to two samples)")
    parser.add_argument("--model", required=True, choices=sorted(n for n, s in MODELS.items() if s.backend == "onnx"))
    args = parser.parse_args()
    spec = MODELS[args.model]
    texts = args.texts or DEFAULT_TEXTS

    tokenizer = AutoTokenizer.from_pretrained(spec.onnx_dir)
    t0 = time.perf_counter()
    npu_sess = make_session(spec, npu=True)
    print(f"NPU session ready in {time.perf_counter() - t0:.1f} s (includes compilation on first run)")
    cpu_sess = make_session(spec, npu=False)

    for text in texts:
        chunks, weights = chunk_text(text, tokenizer, max_tokens=spec.max_tokens)
        print(f"\nText: {text[:80]}... ({weights.sum()} tokens, {len(chunks)} windows)")
        for name, sess in (("CPU", cpu_sess), ("NPU", npu_sess)):
            t0 = time.perf_counter()
            ai = aggregate(score_chunks(chunks, tokenizer, sess, spec), weights)
            print(f"  {name}: AI={100 * ai:.2f}%  ({(time.perf_counter() - t0) * 1e3:.1f} ms)")


if __name__ == "__main__":
    main()
