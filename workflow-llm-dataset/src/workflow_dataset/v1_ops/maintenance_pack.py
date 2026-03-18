"""
M50E–M50H Phase A/B: Build stable-v1 maintenance pack — posture, rhythm, review cadence, recovery paths, escalation, rollback readiness, ownership.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.v1_ops.models import (
    V1SupportPosture,
    MaintenanceRhythm,
    ReviewCadenceRef,
    RecoveryPath,
    EscalationPath,
    RollbackReadiness,
    SupportOwnershipNote,
    StableV1MaintenancePack,
)
from workflow_dataset.v1_ops.posture import build_v1_support_posture


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _default_maintenance_rhythm() -> MaintenanceRhythm:
    return MaintenanceRhythm(
        rhythm_id="stable_v1_daily_weekly",
        label="Stable v1 daily/weekly",
        description="Daily: supportability check, repair loop status. Weekly: stability decision pack, review cadence.",
        interval_days=1,
        daily_tasks=[
            "Run: workflow-dataset supportability",
            "Check: workflow-dataset repair-loops list (top repair-needed)",
            "Optional: workflow-dataset v1-ops status",
        ],
        weekly_tasks=[
            "Run: workflow-dataset stability-reviews generate",
            "Run: workflow-dataset stability-decision pack",
            "Review: workflow-dataset v1-ops maintenance-pack",
        ],
    )


def _review_cadence_ref(root: Path) -> ReviewCadenceRef:
    try:
        from workflow_dataset.stability_reviews.cadences import load_active_cadence, next_review_due_iso
        c = load_active_cadence(root)
        next_due = next_review_due_iso(c)
        return ReviewCadenceRef(
            cadence_id=c.cadence_id,
            label=c.label,
            kind=c.kind,
            next_due_iso=next_due,
            description=c.description or "",
        )
    except Exception:
        return ReviewCadenceRef(
            cadence_id="rolling_stability",
            label="Rolling stability review (7d)",
            kind="rolling_stability",
            next_due_iso="",
            description="Review on weekly cadence.",
        )


def _recovery_paths_from_reliability() -> list[RecoveryPath]:
    paths: list[RecoveryPath] = []
    try:
        from workflow_dataset.reliability.recovery_playbooks import RECOVERY_CASES
        for c in RECOVERY_CASES:
            first = c.steps_guide[0] if c.steps_guide else ""
            paths.append(RecoveryPath(
                path_id=c.case_id,
                incident_class=c.case_id,
                label=c.name,
                steps=list(c.steps_guide),
                first_step_command=first[:120] if first else "",
            ))
    except Exception:
        paths = [
            RecoveryPath(path_id="generic", incident_class="other", label="Recovery guide", steps=["workflow-dataset recovery guide"], first_step_command="workflow-dataset recovery guide"),
        ]
    return paths


def _escalation_paths_default() -> list[EscalationPath]:
    return [
        EscalationPath(
            path_id="guidance_rollback",
            trigger_condition="Post-deployment guidance = needs_rollback or rollback",
            escalate_to="Operator / release owner",
            handoff_artifact="support_bundle",
        ),
        EscalationPath(
            path_id="repair_failed",
            trigger_condition="Repair loop failed and rollback not sufficient",
            escalate_to="Operator / reliability owner",
            handoff_artifact="repair_loop_id + support_bundle",
        ),
        EscalationPath(
            path_id="blocked_approval",
            trigger_condition="Blocked approval or policy mode",
            escalate_to="Trust / approval owner",
            handoff_artifact="support_bundle",
        ),
    ]


def _rollback_readiness(root: Path) -> RollbackReadiness:
    try:
        from workflow_dataset.deploy_bundle import get_active_bundle, get_rollback_readiness
        active = get_active_bundle(root)
        if not active:
            return RollbackReadiness(ready=False, prior_stable_ref="", reason="No active bundle", recommended_action="Set active bundle or run deploy-bundle recovery-report.")
        bid = active.get("active_bundle_id") or active.get("bundle_id") or active.get("id") or "founder_operator_prod"
        r = get_rollback_readiness(bid, repo_root=root)
        return RollbackReadiness(
            ready=bool(r.get("ready", False)),
            prior_stable_ref=r.get("latest_checkpoint_id") or r.get("prior_stable_ref") or "",
            reason=r.get("reason") or ("Ready" if r.get("ready") else "No checkpoint or not ready"),
            recommended_action=r.get("recommended_action") or ("Run release rollback if needed" if r.get("ready") else "Create checkpoint: release upgrade-apply"),
        )
    except Exception as e:
        return RollbackReadiness(
            ready=False,
            prior_stable_ref="",
            reason=str(e)[:200],
            recommended_action="Run workflow-dataset release upgrade-status and deploy-bundle recovery-report.",
        )


def _ownership_notes_default() -> list[SupportOwnershipNote]:
    return [
        SupportOwnershipNote(
            role_or_owner="Operator / release owner",
            responsibility="Daily supportability, stability decision, rollback decision",
            scope_note="Stable v1",
        ),
        SupportOwnershipNote(
            role_or_owner="Reliability owner",
            responsibility="Recovery playbooks, repair loops, golden path",
            scope_note="v1 health",
        ),
    ]


def build_stable_v1_maintenance_pack(repo_root: Path | str | None = None) -> StableV1MaintenancePack:
    """Build the stable-v1 maintenance pack: posture, rhythm, review cadence, recovery paths, escalation, rollback readiness, ownership."""
    root = _repo_root(repo_root)
    now = datetime.now(timezone.utc)
    generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    support_posture = build_v1_support_posture(root)
    maintenance_rhythm = _default_maintenance_rhythm()
    review_cadence_ref = _review_cadence_ref(root)
    recovery_paths = _recovery_paths_from_reliability()
    escalation_paths = _escalation_paths_default()
    rollback_readiness = _rollback_readiness(root)
    ownership_notes = _ownership_notes_default()

    return StableV1MaintenancePack(
        pack_id="stable_v1_maintenance_pack",
        label="Stable v1 maintenance pack",
        support_posture=support_posture,
        maintenance_rhythm=maintenance_rhythm,
        review_cadence_ref=review_cadence_ref,
        recovery_paths=recovery_paths,
        escalation_paths=escalation_paths,
        rollback_readiness=rollback_readiness,
        ownership_notes=ownership_notes,
        generated_at_utc=generated_at,
    )
