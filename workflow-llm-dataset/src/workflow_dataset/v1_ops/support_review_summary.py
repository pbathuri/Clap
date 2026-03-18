"""
M50H.1: Operator/owner support review summary — what was reviewed, overdue, next actions, ownership.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.v1_ops.models import SupportReviewSummary
from workflow_dataset.v1_ops.maintenance_pack import build_stable_v1_maintenance_pack
from workflow_dataset.v1_ops.mission_control import get_v1_ops_state


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_support_review_summary(
    repo_root: Path | str | None = None,
) -> SupportReviewSummary:
    """
    Build operator/owner support review summary: items reviewed (from last review or current pack),
    overdue items, next actions, ownership roles. Uses v1_ops_state and maintenance pack.
    """
    root = _repo_root(repo_root)
    now = datetime.now(timezone.utc)
    generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    pack = build_stable_v1_maintenance_pack(root)
    state = get_v1_ops_state(root)

    # Items reviewed: from last stability review if available, else placeholder from pack
    items_reviewed: list[str] = []
    try:
        from workflow_dataset.stability_reviews.store import load_latest_review
        latest = load_latest_review(root)
        if latest:
            pack_data = latest.get("decision_pack", {})
            items_reviewed.append("Stability decision: %s" % pack_data.get("recommended_decision", "—"))
            items_reviewed.append("Window: %s" % (pack_data.get("stability_window", {}).get("label", "—")))
            reviewed_at_iso = latest.get("at_iso", "")
        else:
            reviewed_at_iso = ""
            items_reviewed.append("Supportability and support paths (no stability review recorded yet)")
    except Exception:
        reviewed_at_iso = ""
        items_reviewed.append("Supportability and support paths")

    # Overdue
    overdue_items: list[str] = []
    if state.get("overdue_maintenance_or_review"):
        overdue_items.append("Stability review (next due passed)")
    if state.get("top_unresolved_v1_risk"):
        overdue_items.append("v1 risk: %s" % (state["top_unresolved_v1_risk"][:80]))

    # Next actions
    next_actions: list[str] = []
    rec = state.get("recommended_stable_v1_support_action")
    if rec:
        next_actions.append(rec)
    if pack.rollback_readiness and not pack.rollback_readiness.ready and pack.rollback_readiness.recommended_action:
        next_actions.append(pack.rollback_readiness.recommended_action)
    if overdue_items:
        next_actions.append("Address overdue items above; run stability-reviews generate if review is overdue.")

    # Ownership roles from pack
    ownership_roles: list[str] = []
    for o in pack.ownership_notes:
        ownership_roles.append("%s: %s" % (o.role_or_owner, o.responsibility))

    summary_text = (
        "Support review: %s. Overdue: %s. Next: %s. Owners: %s."
        % (
            len(items_reviewed),
            len(overdue_items),
            next_actions[0][:60] if next_actions else "—",
            ownership_roles[0][:40] if ownership_roles else "—",
        )
    )

    return SupportReviewSummary(
        review_id="v1_support_review_%s" % now.strftime("%Y%m%d"),
        period_label="Stable v1 support review",
        reviewed_at_iso=reviewed_at_iso,
        items_reviewed=items_reviewed,
        overdue_items=overdue_items,
        next_actions=next_actions,
        ownership_roles=ownership_roles,
        summary_text=summary_text,
        generated_at_utc=generated_at,
    )
