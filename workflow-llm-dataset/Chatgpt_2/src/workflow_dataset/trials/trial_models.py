"""
M17: Models for workflow trials — trial definition, result, and bundle linkage.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class TrialMode(str, Enum):
    """How the trial was run: baseline (no model), adapter, retrieval_only, adapter_retrieval."""

    BASELINE = "baseline"
    ADAPTER = "adapter"
    RETRIEVAL_ONLY = "retrieval_only"
    ADAPTER_RETRIEVAL = "adapter_retrieval"


class WorkflowTrial(BaseModel):
    """Definition of a single workflow trial scenario."""

    trial_id: str = Field(default="", description="Unique id")
    scenario_id: str = Field(default="", description="Scenario group id")
    domain: str = Field(default="", description="ops | spreadsheet | founder | creative")
    workflow_type: str = Field(default="", description="e.g. summarize_reporting, scaffold_status")
    task_goal: str = Field(default="", description="Human-readable goal")
    required_inputs: list[str] = Field(default_factory=list, description="Input keys expected")
    expected_outputs: list[str] = Field(default_factory=list, description="Output kinds expected")
    requires_retrieval: bool = Field(default=False)
    requires_adapter: bool = Field(default=False)
    prompt_template: str = Field(default="", description="Optional template; {context} etc.")
    created_utc: str = Field(default="")


class WorkflowTrialResult(BaseModel):
    """Result of running one trial in one mode."""

    result_id: str = Field(default="")
    trial_id: str = Field(default="")
    model_mode: str = Field(default="", description="baseline | adapter | retrieval_only | adapter_retrieval")
    retrieval_used: bool = Field(default=False)
    adapter_used: bool = Field(default=False)
    output_paths: list[str] = Field(default_factory=list)
    model_response: str = Field(default="")
    evidence_used: list[str] = Field(default_factory=list)
    task_completion_score: float = Field(default=0.0, description="Heuristic 0–1")
    style_match_score: float = Field(default=0.0, description="Heuristic 0–1")
    retrieval_grounding_score: float = Field(default=0.0, description="Heuristic 0–1")
    bundle_usefulness_score: float = Field(default=0.0, description="Heuristic 0–1")
    safety_score: float = Field(default=1.0, description="Heuristic 0–1")
    adoption_ready: bool = Field(default=False)
    completion_status: str = Field(default="completed", description="completed | partial | failed")
    notes: str = Field(default="")
    created_utc: str = Field(default="")


class WorkflowTrialBundle(BaseModel):
    """Link from a trial result to a produced bundle and optional adoption candidate."""

    bundle_id: str = Field(default="")
    trial_id: str = Field(default="")
    result_id: str = Field(default="")
    produced_artifacts: list[str] = Field(default_factory=list)
    selected_output_paths: list[str] = Field(default_factory=list)
    adoption_candidate_id: str = Field(default="")
    created_utc: str = Field(default="")
