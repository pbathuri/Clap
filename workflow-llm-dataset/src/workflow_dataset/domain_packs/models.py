"""
M23U: Domain pack model — vertical-specific pack with job packs, routines, model/dataset/integration classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DomainPack:
    """A domain pack for a vertical (e.g. founder_ops, office_admin)."""
    domain_id: str
    name: str
    description: str = ""
    # Suggested local entities
    suggested_job_packs: list[str] = field(default_factory=list)
    suggested_routines: list[str] = field(default_factory=list)
    # Model / tool classes (IDs from catalog or internal; filtered by policy)
    suggested_model_classes: list[str] = field(default_factory=list)
    suggested_embedding_classes: list[str] = field(default_factory=list)
    suggested_ocr_vision_classes: list[str] = field(default_factory=list)
    suggested_integration_classes: list[str] = field(default_factory=list)
    # Specialization
    suggested_recipe_id: str = ""   # e.g. retrieval_only, adapter_finetune
    # Safety / approvals
    expected_approvals: list[str] = field(default_factory=list)
    trust_notes: str = ""
    # Matching hints for recommendation
    field_keywords: list[str] = field(default_factory=list)   # e.g. operations, founder
    job_family_keywords: list[str] = field(default_factory=list)  # e.g. admin, analyst
