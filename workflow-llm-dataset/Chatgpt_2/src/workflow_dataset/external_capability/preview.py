"""
M24D: Activation preview — what would change, approval required, blocked, safe to proceed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.external_capability.activation_models import ActivationRequest
from workflow_dataset.external_capability.registry import get_external_source
from workflow_dataset.external_capability.policy import apply_rejection_policy
from workflow_dataset.external_capability.plans import build_activation_plan


@dataclass
class ActivationPreview:
    """Preview of what would happen for an activation request."""

    activation_id: str
    source_id: str
    requested_action: str
    what_would_change: list[str] = field(default_factory=list)
    files_or_configs_affected: list[str] = field(default_factory=list)
    approval_required: bool = False
    blocked: bool = False
    block_reason: str = ""
    safe_to_proceed: bool = False
    steps_summary: list[str] = field(default_factory=list)


def build_preview(
    request: ActivationRequest,
    repo_root: Path | str | None = None,
    machine_profile: dict[str, Any] | None = None,
    trust_posture: dict[str, Any] | None = None,
) -> ActivationPreview:
    """
    Build preview for an activation request: what would change, approval required, blocked, safe to proceed.
    """
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    source = get_external_source(request.source_id, root)
    preview = ActivationPreview(
        activation_id=request.activation_id,
        source_id=request.source_id,
        requested_action=request.requested_action,
    )

    if not source:
        preview.blocked = True
        preview.block_reason = f"Source '{request.source_id}' not in registry."
        return preview

    machine_profile = machine_profile or {}
    trust_posture = trust_posture or {}
    if request.requested_action in ("enable", "install"):
        allowed, reject_reason = apply_rejection_policy(source, machine_profile, trust_posture)
        if not allowed:
            preview.blocked = True
            preview.block_reason = reject_reason or "policy"
            return preview

    # What would change
    if request.requested_action == "enable" and source.source_id in ("openclaw", "coding_agent", "ide_editor", "notebook_rag"):
        preview.what_would_change.append(f"Set integration '{source.source_id}' enabled=true in integration manifest.")
        preview.files_or_configs_affected.append("data/local/runtime/integration_manifests.json")
    elif request.requested_action == "disable":
        preview.what_would_change.append(f"Set integration or source '{request.source_id}' enabled=false.")
        preview.files_or_configs_affected.append("data/local/runtime/integration_manifests.json")
    elif request.requested_action == "enable" and source.category == "ollama_model":
        preview.what_would_change.append("No local file change; model must be pulled via Ollama (instructions only).")
        preview.steps_summary = [s.get("detail", "") for s in build_activation_plan(request.source_id, root)]
        preview.approval_required = True
        preview.safe_to_proceed = True
        return preview
    elif request.requested_action == "verify":
        preview.what_would_change.append("Verify backend/source availability (read-only checks).")
        preview.safe_to_proceed = True
        return preview

    # Approval required if source has approval_notes or request has approvals_required
    preview.approval_required = bool(source.approval_notes or request.approvals_required)
    if request.requested_action in ("enable", "install") and source.source_id in ("openclaw", "coding_agent", "ide_editor", "notebook_rag"):
        preview.safe_to_proceed = True
    if request.requested_action == "disable":
        preview.safe_to_proceed = True

    steps = build_activation_plan(request.source_id, root)
    preview.steps_summary = [s.get("detail", "") for s in steps]
    return preview
