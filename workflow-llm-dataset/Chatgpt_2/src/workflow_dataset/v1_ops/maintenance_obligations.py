"""
M50H.1: Summary of what must be maintained to preserve stable-v1 posture.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.v1_ops.models import MaintenanceObligation, MaintenanceObligationsSummary
from workflow_dataset.v1_ops.maintenance_pack import build_stable_v1_maintenance_pack


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_maintenance_obligations_summary(
    repo_root: Path | str | None = None,
) -> MaintenanceObligationsSummary:
    """
    Build a clear summary of what must be maintained to preserve stable-v1 posture.
    Derived from the current stable-v1 maintenance pack: daily tasks, weekly tasks,
    review cadence, rollback readiness, support paths.
    """
    root = _repo_root(repo_root)
    pack = build_stable_v1_maintenance_pack(root)
    now = datetime.now(timezone.utc)
    generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    obligations: list[MaintenanceObligation] = []

    # Daily
    if pack.maintenance_rhythm:
        for t in pack.maintenance_rhythm.daily_tasks:
            obligations.append(MaintenanceObligation(
                category="daily",
                label="Daily task",
                frequency="daily",
                command_or_description=t,
            ))

    # Weekly
    if pack.maintenance_rhythm:
        for t in pack.maintenance_rhythm.weekly_tasks:
            obligations.append(MaintenanceObligation(
                category="weekly",
                label="Weekly task",
                frequency="weekly",
                command_or_description=t,
            ))

    # Review cadence
    if pack.review_cadence_ref:
        obligations.append(MaintenanceObligation(
            category="review_cadence",
            label=pack.review_cadence_ref.label or "Stability review",
            frequency="on_cadence",
            command_or_description="Next due: %s. Run: workflow-dataset stability-reviews generate" % (pack.review_cadence_ref.next_due_iso or "—"),
        ))

    # Rollback readiness
    if pack.rollback_readiness:
        obligations.append(MaintenanceObligation(
            category="rollback",
            label="Rollback readiness",
            frequency="on_demand",
            command_or_description=pack.rollback_readiness.recommended_action or "Ensure checkpoint exists; run release rollback if needed.",
        ))

    # Support paths (first few as obligations to keep paths healthy)
    if pack.support_posture and pack.support_posture.support_paths:
        for p in pack.support_posture.support_paths[:5]:
            obligations.append(MaintenanceObligation(
                category="support_path",
                label="Support path",
                frequency="on_demand",
                command_or_description=p,
            ))

    summary_text = (
        "To preserve stable-v1 posture: run daily tasks (supportability, repair-loops), "
        "weekly tasks (stability-reviews generate, stability-decision pack, v1-ops maintenance-pack), "
        "complete review on cadence, and keep rollback readiness. Use v1-ops maintenance-obligations for full list."
    )

    return MaintenanceObligationsSummary(
        summary_id="stable_v1_maintenance_obligations",
        obligations=obligations,
        generated_at_utc=generated_at,
        summary_text=summary_text,
    )
