"""
M23U: Specialization recipe model — mode, data sources, licensing metadata. No auto_download / auto_train.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


RECIPE_MODES = (
    "local_user_data_only",
    "local_user_data_plus_approved_open_datasets",
    "local_user_data_plus_approved_public_model",
    "retrieval_only",
    "adapter_finetune",
    "embedding_refresh",
    "ocr_doc",
    "coding_agent",
)


@dataclass
class SpecializationRecipe:
    """Explicit specialization recipe: mode, data sources, licensing. Generation only."""
    recipe_id: str
    name: str
    description: str = ""
    mode: str = "retrieval_only"  # one of RECIPE_MODES
    # Data sources (references only; no auto-download)
    data_sources: dict[str, Any] = field(default_factory=dict)
    # e.g. local_only: true; approved_dataset_refs: [...]; approved_model_refs: [...]
    licensing_compliance_metadata: dict[str, Any] = field(default_factory=dict)
    # e.g. dataset_licenses: [...], model_license: "", attribution: ""
    # Explicit no-auto flags (documentation)
    auto_download: bool = False
    auto_train: bool = False
    # Optional steps (declarative; for operator review)
    steps_summary: list[str] = field(default_factory=list)
