"""
MLX / mlx-lm backend for Apple-Silicon-first LoRA training.

Uses mlx_lm.lora CLI when available; falls back to clear error if not installed.
All artifacts under a reproducible run directory.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from workflow_dataset.llm.schemas import TrainingRunConfig
from workflow_dataset.llm.train_backend import TrainBackend


def _check_mlx_lm() -> bool:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "mlx_lm.lora", "--help"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


def _val_to_valid(data_dir: Path) -> None:
    """mlx_lm.lora expects valid.jsonl; we write val.jsonl. Copy val -> valid if needed."""
    val_path = data_dir / "val.jsonl"
    valid_path = data_dir / "valid.jsonl"
    if val_path.exists() and not valid_path.exists():
        shutil.copy2(val_path, valid_path)


class MLXBackend(TrainBackend):
    """Apple Silicon training via mlx-lm LoRA CLI."""

    def prepare_model(self, config: TrainingRunConfig) -> Any:
        """MLX loads on-the-fly during train; return config for compatibility."""
        if not _check_mlx_lm():
            raise RuntimeError(
                "mlx-lm is not installed or not runnable. Install with: pip install 'mlx-lm[train]'"
            )
        return {"base_model": config.base_model}

    def train_lora(
        self,
        config: TrainingRunConfig,
        train_data_path: str | Path,
        eval_data_path: str | Path | None,
        output_dir: str | Path,
    ) -> Path:
        """Run LoRA training via mlx_lm.lora CLI. Data dir must contain train.jsonl (and optionally valid.jsonl)."""
        if not _check_mlx_lm():
            raise RuntimeError("mlx-lm is not installed. Install with: pip install 'mlx-lm[train]'")
        data_dir = Path(train_data_path)
        if not data_dir.is_dir():
            raise FileNotFoundError(f"Training data directory not found: {data_dir}")
        train_file = data_dir / "train.jsonl"
        if not train_file.exists():
            raise FileNotFoundError(f"train.jsonl not found in {data_dir}")
        _val_to_valid(data_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        adapter_path = output_dir / "adapters"
        # Compute iters from epochs and dataset size if needed
        num_epochs = config.num_epochs
        with open(train_file) as f:
            n_lines = sum(1 for _ in f)
        steps_per_epoch = max(1, n_lines // max(1, config.train_batch_size * config.grad_accumulation))
        iters = num_epochs * steps_per_epoch
        cmd = [
            sys.executable, "-m", "mlx_lm.lora",
            "--model", config.base_model,
            "--train",
            "--data", str(data_dir),
            "--adapter-path", str(adapter_path),
            "--iters", str(iters),
            "--batch-size", str(config.train_batch_size),
            "--learning-rate", str(config.learning_rate),
            "--lora-layers", "16",
        ]
        if config.max_seq_length:
            cmd.extend(["--max-seq-length", str(config.max_seq_length)])
        try:
            subprocess.run(cmd, check=True, cwd=str(output_dir), timeout=3600 * 24)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"mlx_lm.lora training failed: {e}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("mlx_lm.lora training timed out")
        if not adapter_path.exists():
            adapter_path = output_dir / "adapters"
        return adapter_path

    def merge_adapter_if_requested(
        self,
        base_model_path: str,
        adapter_path: str | Path,
        output_path: str | Path,
    ) -> bool:
        """MLX merge: optional; not required for inference with adapter. Return False to skip."""
        return False

    def run_inference(
        self,
        model_path: str | Path,
        prompt: str,
        max_tokens: int = 256,
        **kwargs: Any,
    ) -> str:
        """Run inference via mlx_lm.generate. model_path can be base model or adapter dir."""
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "mlx_lm.generate",
                    "--model", str(model_path),
                    "--prompt", prompt,
                    "--max-tokens", str(max_tokens),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                return f"[inference error: {result.stderr or result.stdout}]"
            return result.stdout or ""
        except Exception as e:
            return f"[inference error: {e}]"
