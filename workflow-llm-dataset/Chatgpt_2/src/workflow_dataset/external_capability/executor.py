"""
M24D: Safe local activation executor — enable/disable integration manifests, verify backends, instructions-only for models.
No auto-pull; no silent enablement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.external_capability.activation_models import ActivationRequest
from workflow_dataset.external_capability.activation_store import (
    load_request,
    save_request,
    save_execution_result,
)
from workflow_dataset.external_capability.preview import build_preview
from workflow_dataset.external_capability.plans import build_activation_plan
from workflow_dataset.external_capability.registry import get_external_source


EXECUTABLE_INTEGRATION_IDS = ("openclaw", "coding_agent", "ide_editor", "notebook_rag")


@dataclass
class ExecutionResult:
    """Result of executing an activation request."""

    activation_id: str
    outcome: str  # executed | failed | instructions_only | blocked
    details: dict[str, Any] = field(default_factory=dict)
    message: str = ""


def execute_activation(
    activation_id: str,
    repo_root: Path | str | None = None,
    approved: bool = False,
) -> ExecutionResult:
    """
    Execute an activation request. Safe local only: enable/disable integration manifest, verify, or instructions_only.
    For enable/disable of integrations, approved=True is required when preview.approval_required.
    """
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    request = load_request(activation_id, root)
    if not request:
        return ExecutionResult(activation_id=activation_id, outcome="failed", message=f"Request {activation_id} not found.")

    preview = build_preview(request, root)
    if preview.blocked:
        request.status = "blocked"
        save_request(request, root)
        save_execution_result(activation_id, "blocked", {"block_reason": preview.block_reason}, root)
        return ExecutionResult(activation_id=activation_id, outcome="blocked", details={"block_reason": preview.block_reason}, message=preview.block_reason)

    if preview.approval_required and not approved:
        return ExecutionResult(
            activation_id=activation_id,
            outcome="blocked",
            details={"reason": "approval_required"},
            message="Operator approval required; run with --approved after review.",
        )

    source = get_external_source(request.source_id, root)

    # disable
    if request.requested_action == "disable":
        if request.source_id in EXECUTABLE_INTEGRATION_IDS:
            try:
                from workflow_dataset.runtime_mesh.integration_registry import set_integration_enabled
                ok = set_integration_enabled(request.source_id, False, root)
                if ok:
                    request.status = "executed"
                    save_request(request, root)
                    save_execution_result(activation_id, "executed", {"action": "disable", "source_id": request.source_id}, root)
                    return ExecutionResult(activation_id=activation_id, outcome="executed", details={"action": "disable"}, message="Integration disabled.")
            except Exception as e:
                request.status = "failed"
                save_request(request, root)
                save_execution_result(activation_id, "failed", {"error": str(e)}, root)
                return ExecutionResult(activation_id=activation_id, outcome="failed", message=str(e))
        request.status = "executed"
        save_request(request, root)
        save_execution_result(activation_id, "executed", {"action": "disable", "note": "no local toggle for this source"}, root)
        return ExecutionResult(activation_id=activation_id, outcome="executed", message="Disable recorded (no local manifest for this source).")

    # verify
    if request.requested_action == "verify":
        if request.source_id.startswith("backend_"):
            backend_id = request.source_id.replace("backend_", "", 1)
            try:
                from workflow_dataset.runtime_mesh.backend_registry import get_backend_status
                status = get_backend_status(backend_id, root)
                save_execution_result(activation_id, "executed", {"action": "verify", "backend_id": backend_id, "status": status}, root)
                return ExecutionResult(activation_id=activation_id, outcome="executed", details={"status": status}, message=f"Backend {backend_id}: {status}.")
            except Exception as e:
                return ExecutionResult(activation_id=activation_id, outcome="failed", message=str(e))
        return ExecutionResult(activation_id=activation_id, outcome="executed", message="Verify completed.")

    # enable (only for integration manifests; ollama_model = instructions_only)
    if request.requested_action in ("enable", "install"):
        if request.source_id in EXECUTABLE_INTEGRATION_IDS:
            try:
                from workflow_dataset.runtime_mesh.integration_registry import set_integration_enabled
                ok = set_integration_enabled(request.source_id, True, root)
                if ok:
                    request.status = "executed"
                    save_request(request, root)
                    save_execution_result(activation_id, "executed", {"action": "enable", "source_id": request.source_id}, root)
                    return ExecutionResult(activation_id=activation_id, outcome="executed", message="Integration enabled.")
            except Exception as e:
                request.status = "failed"
                save_request(request, root)
                save_execution_result(activation_id, "failed", {"error": str(e)}, root)
                return ExecutionResult(activation_id=activation_id, outcome="failed", message=str(e))

        if source and source.category == "ollama_model":
            steps = build_activation_plan(request.source_id, root)
            request.status = "executed"
            save_request(request, root)
            save_execution_result(
                activation_id,
                "instructions_only",
                {"action": "enable", "source_id": request.source_id, "steps": [s.get("detail") for s in steps]},
                root,
            )
            return ExecutionResult(
                activation_id=activation_id,
                outcome="instructions_only",
                details={"steps": [s.get("detail") for s in steps]},
                message="No auto-download. Follow instructions: " + "; ".join([s.get("detail", "")[:60] for s in steps[:2]]),
            )

    request.status = "failed"
    save_request(request, root)
    save_execution_result(activation_id, "failed", {"reason": "unsupported_action_or_source"}, root)
    return ExecutionResult(activation_id=activation_id, outcome="failed", message="Unsupported action or source for local execution.")


def disable_source(source_id: str, repo_root: Path | str | None = None) -> ExecutionResult:
    """
    Disable a source by id. Creates a synthetic activation context and disables if the source is an integration.
    """
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    if source_id in EXECUTABLE_INTEGRATION_IDS:
        try:
            from workflow_dataset.runtime_mesh.integration_registry import set_integration_enabled
            ok = set_integration_enabled(source_id, False, root)
            if ok:
                save_execution_result(f"disable_{source_id}", "executed", {"action": "disable", "source_id": source_id}, root)
                return ExecutionResult(activation_id="", outcome="executed", message=f"Disabled {source_id}.")
        except Exception as e:
            return ExecutionResult(activation_id="", outcome="failed", message=str(e))
    return ExecutionResult(activation_id="", outcome="executed", details={"note": "no local manifest"}, message=f"No local toggle for {source_id}.")


def create_activation_request(
    source_id: str,
    action: str = "enable",
    repo_root: Path | str | None = None,
) -> ActivationRequest | None:
    """Create an activation request from source_id and action. Returns None if source not found."""
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    source = get_external_source(source_id, root)
    if not source:
        return None
    try:
        from workflow_dataset.utils.dates import utc_now_iso
        now = utc_now_iso()
    except Exception:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
    safe_src = "".join(c if c.isalnum() or c in "-_" else "_" for c in source_id)
    t = now.replace(":", "").replace("-", "")[:15]
    act_id = f"act_{safe_src}_{t}"
    return ActivationRequest(
        activation_id=act_id,
        source_id=source_id,
        source_category=source.category,
        requested_action=action,
        prerequisites=list(source.install_prerequisites or []),
        approvals_required=[x for x in (source.approval_notes or "").split(";") if x.strip()],
        expected_resource_cost=source.estimated_resource or "medium",
        reversible=True,
        status="pending",
        notes=source.notes or "",
        risks=source.security_notes or "",
        created_at=now,
        updated_at=now,
    )
