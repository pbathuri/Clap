"""
Pydantic models and typed structures for the LLM pipeline.

Used by corpus builder, SFT builder, training backend, and eval.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CorpusDocument(BaseModel):
    """Single document in the domain-adaptation / retrieval corpus."""

    doc_id: str = Field(..., description="Stable unique ID")
    source_type: str = Field(..., description="e.g. occupation, workflow_step, tool_bundle")
    title: str = Field(default="", description="Short title")
    text: str = Field(default="", description="Full text content")
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict, description="source_id, table, row refs")


class SFTExample(BaseModel):
    """Single supervised fine-tuning (instruction) example."""

    example_id: str = Field(..., description="Stable unique ID")
    task_type: str = Field(..., description="e.g. knowledge_qa, routine_interpretation")
    messages: list[dict[str, str]] = Field(
        ...,
        description="Chat format: [{\"role\": \"system\", \"content\": \"...\"}, {\"role\": \"user\", \"content\": \"...\"}, {\"role\": \"assistant\", \"content\": \"...\"}]",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)


class EvalExample(BaseModel):
    """Single evaluation example with optional reference answer."""

    eval_id: str = Field(...)
    task_type: str = Field(...)
    input_prompt: str = Field(default="")
    messages: list[dict[str, str]] = Field(default_factory=list)
    reference: str | None = Field(default=None)
    reference_short: str | None = Field(default=None, description="For exact-match / short-label tasks")
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrainingRunConfig(BaseModel):
    """Resolved configuration for a single training run."""

    backend: str = Field(default="mlx")
    base_model: str = Field(...)
    adapter_type: str = Field(default="lora")
    output_dir: str = Field(...)
    max_seq_length: int = Field(default=2048)
    train_batch_size: int = Field(default=2)
    eval_batch_size: int = Field(default=4)
    grad_accumulation: int = Field(default=4)
    learning_rate: float = Field(default=1e-5)
    num_epochs: int = Field(default=3)
    warmup_ratio: float = Field(default=0.1)
    lora_rank: int = Field(default=8)
    lora_alpha: int = Field(default=16)
    lora_dropout: float = Field(default=0.05)
    max_train_examples: int | None = Field(default=None)
    max_eval_examples: int | None = Field(default=None)
    random_seed: int = Field(default=42)
    train_data_path: str = Field(default="")
    eval_data_path: str = Field(default="")


class EvalResult(BaseModel):
    """Aggregate evaluation result for a run."""

    run_id: str = Field(default="")
    model_id: str = Field(default="")
    retrieval_used: bool = Field(default=False)
    metrics: dict[str, float] = Field(default_factory=dict)
    num_examples: int = Field(default=0)
    predictions_path: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)
