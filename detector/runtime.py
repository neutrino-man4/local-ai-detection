"""
ONNX Runtime sessions for detector models on the CPU or on the Ryzen AI NPU (BF16 via
the VitisAI execution provider), and scoring of token windows into AI probabilities.
The first NPU session compiles the model into a per-model cache; later sessions reuse it.

Author: Aritra Bal (ITP)
Date: 2026-11-17
"""

import json
import os
from pathlib import Path

import numpy as np
import onnxruntime as ort
from transformers import PreTrainedTokenizerBase

from detector.models import ModelSpec


def write_bf16_config(path: Path) -> None:
    """Derive a BF16 config from AMD's default VAIP config by switching to the VAIML target."""
    default_cfg = Path(os.environ["RYZEN_AI_INSTALLATION_PATH"]) / "voe-4.0-linux_x86_64" / "vaip_config.json"
    cfg = json.loads(default_cfg.read_text())
    cfg["target"] = "VAIML"
    for p in cfg["passes"]:
        if p.get("name") == "vaiml_partition":
            # AMD docs recommend the unvectorized layout for transformers
            p["vaiml_config"]["preferred_data_storage"] = "unvectorized"
    path.write_text(json.dumps(cfg, indent=2))


def make_session(spec: ModelSpec, npu: bool) -> ort.InferenceSession:
    """Create an ONNX Runtime session for a model on the NPU (VitisAI EP) or on the CPU."""
    opts = ort.SessionOptions()
    if not npu:
        opts.log_severity_level = 3
        return ort.InferenceSession(str(spec.onnx_path), sess_options=opts, providers=["CPUExecutionProvider"])

    cfg = spec.onnx_dir / "vai_ep_config_bf16.json"
    if not cfg.exists():
        write_bf16_config(cfg)
    opts.log_severity_level = 1  # info level prints how many ops landed on the NPU
    provider_options = {
        "config_file": str(cfg),
        "cache_dir": str(spec.npu_cache_dir),
        "cache_key": f"{spec.name}_bf16",
        "enable_cache_file_io_in_mem": "0",
    }
    return ort.InferenceSession(
        str(spec.onnx_path), sess_options=opts,
        providers=["VitisAIExecutionProvider"], provider_options=[provider_options],
    )


def score_chunks(
    chunks: list[list[int]],
    tokenizer: PreTrainedTokenizerBase,
    session: ort.InferenceSession,
    spec: ModelSpec,
) -> np.ndarray:
    """Run each window through the model and return its AI probability.

    Args:
        chunks: Token ids per window, as returned by chunk_text.
        tokenizer: Tokenizer providing the special and padding token ids.
        session: ONNX Runtime session of the static-shape model.
        spec: Model description (input length and output head).

    Returns:
        Array of shape (num_windows,) with the AI probability of each window.
    """
    ai_probs = []
    for chunk in chunks:
        ids = [tokenizer.cls_token_id] + chunk + [tokenizer.sep_token_id]
        if len(ids) > spec.seq_len:
            raise ValueError(f"Window of {len(ids)} tokens exceeds model length {spec.seq_len}")
        pad = spec.seq_len - len(ids)
        feed = {
            "input_ids": np.array([ids + [tokenizer.pad_token_id] * pad], dtype=np.int64),
            "attention_mask": np.array([[1] * len(ids) + [0] * pad], dtype=np.int64),
        }
        logits = session.run(["logits"], feed)[0][0].astype(np.float64)
        if spec.head == "softmax2":
            e = np.exp(logits - logits.max())
            ai_probs.append(e[spec.ai_index] / e.sum())
        elif spec.head == "sigmoid1":
            ai_probs.append(1.0 / (1.0 + np.exp(-logits[0])))
        else:
            raise ValueError(f"Head '{spec.head}' is not supported by the ONNX runtime")
    return np.array(ai_probs)
