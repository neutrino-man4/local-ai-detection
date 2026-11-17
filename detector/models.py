"""
Registry of supported detector models. Each entry fixes the Hugging Face model id,
the static input length used for export, and how the output logits map to an AI
probability. All artifact and cache paths are derived from the model name.

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ROOT: Path = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ModelSpec:
    """Static description of one detector model.

    Attributes:
        name: Short name used on the command line and in artifact paths.
        hf_id: Hugging Face model id.
        seq_len: Fixed input length of the exported ONNX model, including special tokens.
        head: "softmax2" for two-class logits, "sigmoid1" for a single AI logit.
        ai_index: Index of the AI class in two-class logits (ignored for "sigmoid1").
    """

    name: str
    hf_id: str
    seq_len: int
    head: Literal["softmax2", "sigmoid1"]
    ai_index: int = 0

    @property
    def max_tokens(self) -> int:
        """Content tokens per window; two positions are reserved for the start and end tokens."""
        return self.seq_len - 2

    @property
    def hf_dir(self) -> Path:
        """Hugging Face download cache for this model."""
        return ROOT / "artifacts" / self.name / "hf"

    @property
    def onnx_dir(self) -> Path:
        """Exported ONNX model, tokenizer files and the NPU config."""
        return ROOT / "artifacts" / self.name / "onnx"

    @property
    def onnx_path(self) -> Path:
        return self.onnx_dir / "model_static.onnx"

    @property
    def npu_cache_dir(self) -> Path:
        """Compiled NPU model cache, kept outside the project folder."""
        return Path.home() / ".cache" / "npu_models" / self.name


MODELS: dict[str, ModelSpec] = {
    # id2label in the model config is {0: "Human", 1: "AI"}
    "fakespot": ModelSpec(
        name="fakespot",
        hf_id="fakespot-ai/roberta-base-ai-text-detection-v1",
        seq_len=512,
        head="softmax2",
        ai_index=1,
    ),
    # Single sigmoid output P(AI) per the model card; training length is not documented,
    # 1024 tokens covers the ~4096-character excerpts used in its training data
    "vanguard": ModelSpec(
        name="vanguard",
        hf_id="ShantanuT01/vanguard-ai-text-detector",
        seq_len=1024,
        head="sigmoid1",
    ),
}
