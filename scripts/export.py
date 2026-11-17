"""
Export a registered detector model to a static-shape ONNX model (batch 1, the model's
fixed sequence length, opset 17) suitable for BF16 compilation on the Ryzen AI NPU.
The tokenizer is saved next to the model so inference needs no network access.
Run from the repository root: python -m scripts.export --model fakespot

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import argparse
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from detector.models import MODELS, ModelSpec


class LogitsOnly(torch.nn.Module):
    """Wrap a sequence classifier so the traced graph returns a plain logits tensor."""

    def __init__(self, model: torch.nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        return self.model(input_ids=input_ids, attention_mask=attention_mask).logits


def export(spec: ModelSpec, out_dir: Path) -> None:
    """Download the model, export it with fixed input shapes, and save the tokenizer."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(spec.hf_id, cache_dir=spec.hf_dir)
    model = AutoModelForSequenceClassification.from_pretrained(spec.hf_id, cache_dir=spec.hf_dir).eval()
    print(f"Labels: {model.config.id2label}")

    # Dummy inputs define the static shape baked into the graph
    input_ids = torch.ones((1, spec.seq_len), dtype=torch.int64)
    attention_mask = torch.ones((1, spec.seq_len), dtype=torch.int64)

    onnx_path = out_dir / spec.onnx_path.name
    # Legacy TorchScript exporter: the dynamo exporter needs onnxscript, which the venv lacks
    torch.onnx.export(
        LogitsOnly(model),
        (input_ids, attention_mask),
        str(onnx_path),
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        opset_version=17,
        do_constant_folding=True,
        dynamo=False,
    )
    tokenizer.save_pretrained(out_dir)
    print(f"Saved {onnx_path} and tokenizer to {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(MODELS), default="fakespot")
    parser.add_argument("--out-dir", type=Path, help="Defaults to artifacts/<model>/onnx")
    args = parser.parse_args()
    spec = MODELS[args.model]
    export(spec, args.out_dir or spec.onnx_dir)
