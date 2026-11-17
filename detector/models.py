"""
Registry of supported detector models. Each entry fixes the Hugging Face model id,
the input length, and the backend: "onnx" models are exported to static-shape ONNX
and run on the NPU or CPU, "mesmer" models run on the CPU through the authors'
reference code. All artifact and cache paths are derived from the model name.

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
        seq_len: Window length in tokens, including special tokens (fixed ONNX input length for "onnx").
        head: "softmax2" for two-class logits, "sigmoid1" for a single AI logit,
            "softmax3" for human / ai / ai_edited (handled by the Mesmer reference code).
        ai_index: Index of the AI class in two-class logits (ignored otherwise).
        backend: "onnx" (exported model, NPU or CPU) or "mesmer" (reference code, CPU only).
        label: Display name for the UI.
    """

    name: str
    hf_id: str
    seq_len: int
    head: Literal["softmax2", "sigmoid1", "softmax3"]
    ai_index: int = 0
    backend: Literal["onnx", "mesmer"] = "onnx"
    label: str = ""

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

    @property
    def ready(self) -> bool:
        """Whether the files needed to run the model are present."""
        if self.backend == "mesmer":
            return (self.hf_dir / "model.safetensors").exists() and (self.hf_dir / "mesmer_detector.py").exists()
        return self.onnx_path.exists()


MODELS: dict[str, ModelSpec] = {
    # Weights, config, policy, tokenizer and mesmer_detector.py downloaded into artifacts/mesmer4b/hf
    "mesmer4b": ModelSpec(
        name="mesmer4b",
        hf_id="mesmertech/mesmer-ai-detector-4b",
        seq_len=1024,
        head="softmax3",
        backend="mesmer",
        label="Mesmer 4B",
    ),
}
