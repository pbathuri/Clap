"""
M21: Classify source role from metadata. Keyword-based; no network.
"""

from __future__ import annotations

from workflow_dataset.capability_intake.source_models import ExternalSourceCandidate, SourceRole


def classify_role(c: ExternalSourceCandidate) -> str:
    """
    Return recommended_role (SourceRole value) from name, description, notes.
    """
    if c.recommended_role and c.recommended_role in [r.value for r in SourceRole]:
        return c.recommended_role
    text = (c.name + " " + c.description + " " + c.notes).lower()
    if "unsafe" in text or "reject" in text:
        return SourceRole.UNSAFE_OR_REJECTED.value
    if "orchestrat" in text or "multi-agent" in text or "routing" in text:
        return SourceRole.AGENT_ORCHESTRATOR.value
    if "agent" in text and "runtime" in text:
        return SourceRole.AGENT_RUNTIME.value
    if "retrieval" in text or "embed" in text:
        return SourceRole.RETRIEVAL_LAYER.value
    if "embedding" in text:
        return SourceRole.EMBEDDING_LAYER.value
    if "parser" in text or "parse" in text:
        return SourceRole.PARSER.value
    if "spreadsheet" in text or "excel" in text:
        return SourceRole.SPREADSHEET_TOOLING.value
    if "creative" in text or "design" in text:
        return SourceRole.CREATIVE_PACKAGING.value
    if "simulation" in text or "swarm" in text:
        return SourceRole.SIMULATION_ENGINE.value
    if "dashboard" in text or "ui" in text or "ux" in text:
        return SourceRole.DASHBOARD_UI.value
    if "proxy" in text or "cli proxy" in text:
        return SourceRole.NETWORK_PROXY.value
    if "eval" in text or "harness" in text:
        return SourceRole.EVALUATION_HARNESS.value
    if "pack" in text:
        return SourceRole.CAPABILITY_PACK_REFERENCE.value
    return SourceRole.CAPABILITY_PACK_REFERENCE.value
