"""
Abstract training backend interface for LoRA fine-tuning.

Concrete backends: MLX (Apple Silicon), with hooks for future JAX/Flax or PyTorch.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from workflow_dataset.llm.schemas import TrainingRunConfig


class TrainBackend(ABC):
    """Abstract backend for prepare_model, train_lora, merge_adapter, run_inference."""

    @abstractmethod
    def prepare_model(self, config: TrainingRunConfig) -> Any:
        """Load base model (and optionally tokenizer). Return backend-specific model handle."""
        pass

    @abstractmethod
    def train_lora(
        self,
        config: TrainingRunConfig,
        train_data_path: str | Path,
        eval_data_path: str | Path | None,
        output_dir: str | Path,
    ) -> Path:
        """
        Run LoRA training. Returns path to saved adapter.
        """
        pass

    @abstractmethod
    def merge_adapter_if_requested(
        self,
        base_model_path: str,
        adapter_path: str | Path,
        output_path: str | Path,
    ) -> bool:
        """Merge adapter into base model and save if requested. Returns True if merged."""
        pass

    @abstractmethod
    def run_inference(
        self,
        model_path: str | Path,
        prompt: str,
        max_tokens: int = 256,
        **kwargs: Any,
    ) -> str:
        """Run inference and return generated text."""
        pass


def get_backend(name: str) -> TrainBackend:
    """Return the requested backend. name in ('mlx', ...)."""
    if name == "mlx":
        from workflow_dataset.llm.mlx_backend import MLXBackend
        return MLXBackend()
    raise ValueError(f"Unknown backend: {name}. Use 'mlx' for Apple Silicon.")
