"""
M21: Build a minimal manifest dict from available fields. For future use by pack installer or GitHub parser.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.capability_intake.source_models import ExternalSourceCandidate


def candidate_to_manifest(c: ExternalSourceCandidate) -> dict[str, Any]:
    """Export ExternalSourceCandidate to a manifest-like dict (e.g. for writing to file or index)."""
    return {
        "source_id": c.source_id,
        "name": c.name,
        "source_type": c.source_type,
        "canonical_url": c.canonical_url,
        "source_kind": c.source_kind,
        "description": c.description,
        "license": c.license,
        "primary_language": c.primary_language,
        "recommended_role": c.recommended_role,
        "safety_risk_level": c.safety_risk_level,
        "local_runtime_fit": c.local_runtime_fit,
        "cloud_pack_fit": c.cloud_pack_fit,
        "adoption_recommendation": c.adoption_recommendation,
        "product_layers": c.product_layers,
        "unresolved_reason": c.unresolved_reason or None,
    }


def build_manifest_template() -> dict[str, Any]:
    """Return a minimal template for a new source manifest (for docs or tooling)."""
    return {
        "source_id": "",
        "name": "",
        "source_type": "repo",
        "canonical_url": "",
        "source_kind": "github",
        "description": "",
        "license": "",
        "primary_language": "",
        "product_layers": [],
        "notes": "",
        "unresolved_reason": "",
    }
