"""
M21: Architecture fit assessment — local runtime and cloud pack fit.
"""

from __future__ import annotations

from workflow_dataset.capability_intake.source_models import ExternalSourceCandidate


def assess_fit(c: ExternalSourceCandidate) -> tuple[str, str]:
    """
    Return (local_runtime_fit, cloud_pack_fit) each: high | medium | low | none.
    Based on description, recommended_role, product_layers, notes.
    """
    local = _local_fit(c)
    cloud = _cloud_fit(c)
    return local, cloud


def _local_fit(c: ExternalSourceCandidate) -> str:
    if c.local_runtime_fit and c.local_runtime_fit in ("high", "medium", "low", "none"):
        return c.local_runtime_fit
    text = (c.description + " " + c.notes).lower()
    if "local" in text or "offline" in text or "agent" in text or "orchestrat" in text:
        if "cloud" in text and "optional" not in text:
            return "low"
        return "high"
    if "api" in text or "network" in text or "proxy" in text:
        return "medium"
    if "ui" in text or "dashboard" in text or "parser" in text:
        return "medium"
    return "low"


def _cloud_fit(c: ExternalSourceCandidate) -> str:
    if c.cloud_pack_fit and c.cloud_pack_fit in ("high", "medium", "low", "none"):
        return c.cloud_pack_fit
    # Default: pack distribution is future; most candidates start as low/none until specified
    if "pack" in (c.description + " " + c.notes).lower():
        return "medium"
    return "low"
