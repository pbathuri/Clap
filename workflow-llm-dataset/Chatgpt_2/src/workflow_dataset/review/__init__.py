"""
M12: Generated output review, refinement, variant management, and adoption bridge.

Local-only; no cloud; preserves apply confirmation safety.
"""

from __future__ import annotations

from workflow_dataset.review.review_models import (
    GeneratedArtifactReview,
    VariantRecord,
    RefineRequest,
    AdoptionCandidate,
)
from workflow_dataset.review.artifact_preview import (
    preview_artifact,
    preview_artifacts_from_manifest,
    build_summary,
)
from workflow_dataset.review.variant_manager import (
    create_variant_record,
    register_variant,
    get_variants_for_generation,
    compare_variants,
    set_preferred_variant,
)
from workflow_dataset.review.refine_request_builder import build_refine_request
from workflow_dataset.review.document_refiner import (
    refine_document,
    get_llm_refine_fn_for_review,
)
from workflow_dataset.review.adoption_bridge import (
    create_adoption_candidate,
    save_adoption_candidate,
    load_adoption_candidate,
    build_apply_plan_for_adoption,
    list_adoption_candidates,
)
from workflow_dataset.review.version_store import (
    save_variant_record,
    load_variant_record,
    list_variants_for_generation,
    save_review,
    load_review,
)

__all__ = [
    "GeneratedArtifactReview",
    "VariantRecord",
    "RefineRequest",
    "AdoptionCandidate",
    "preview_artifact",
    "preview_artifacts_from_manifest",
    "build_summary",
    "create_variant_record",
    "register_variant",
    "get_variants_for_generation",
    "compare_variants",
    "set_preferred_variant",
    "build_refine_request",
    "refine_document",
    "get_llm_refine_fn_for_review",
    "create_adoption_candidate",
    "save_adoption_candidate",
    "load_adoption_candidate",
    "build_apply_plan_for_adoption",
    "list_adoption_candidates",
    "save_variant_record",
    "load_variant_record",
    "list_variants_for_generation",
    "save_review",
    "load_review",
]
