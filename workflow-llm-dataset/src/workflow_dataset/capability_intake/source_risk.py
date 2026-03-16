"""
M21: Risk assessment for external sources. Policy-driven; no network.
"""

from __future__ import annotations

from workflow_dataset.capability_intake.source_models import ExternalSourceCandidate


def assess_risk(c: ExternalSourceCandidate) -> str:
    """
    Return safety_risk_level: low | medium | high | unknown.
    Uses description, license, notes, and adoption_recommendation hints.
    """
    if c.safety_risk_level and c.safety_risk_level in ("low", "medium", "high", "unknown"):
        return c.safety_risk_level
    text = (c.description + " " + c.notes + " " + (c.license or "")).lower()
    if "unsafe" in text or "reject" in text or "network" in text and "local" not in text:
        return "high"
    if "mit" in text or "apache" in text or "bsd" in text:
        license_risk = "low"
    elif "gpl" in text or "agpl" in text:
        license_risk = "medium"
    else:
        license_risk = "unknown"
    if c.maintainer_signal == "stale":
        return "medium" if license_risk == "low" else "high"
    return license_risk if license_risk != "unknown" else "unknown"
