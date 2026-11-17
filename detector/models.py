"""
Registry of supported detector models. Each entry is a Mesmer model downloaded into
artifacts/<name>/hf (weights, config, policy, tokenizer and the authors'
mesmer_detector.py); all paths are derived from the model name.

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

from dataclasses import dataclass
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ModelSpec:
    """Static description of one detector model.

    Attributes:
        name: Short name used on the command line and in artifact paths.
        hf_id: Hugging Face model id.
        label: Display name for the UI.
    """

    name: str
    hf_id: str
    label: str

    @property
    def hf_dir(self) -> Path:
        """Downloaded model folder."""
        return ROOT / "artifacts" / self.name / "hf"

    @property
    def ready(self) -> bool:
        """Whether the weights and the reference code are present."""
        return (self.hf_dir / "model.safetensors").exists() and (self.hf_dir / "mesmer_detector.py").exists()


MODELS: dict[str, ModelSpec] = {
    "mesmer4b": ModelSpec(name="mesmer4b", hf_id="mesmertech/mesmer-ai-detector-4b", label="Mesmer 4B"),
}
