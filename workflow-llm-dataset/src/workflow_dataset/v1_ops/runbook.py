"""
M50E–M50H Phase C: Operator/owner runbook — daily/weekly review, when v1 degrades, safe repair, rollback, pause/narrow.
"""

from __future__ import annotations

# Daily review items for v1
DAILY_REVIEW_ITEMS = [
    "Run: workflow-dataset supportability — check guidance (safe_to_continue / needs_operator / needs_rollback).",
    "Check: workflow-dataset repair-loops list — top repair-needed, active, failed.",
    "Optional: workflow-dataset v1-ops status — current support posture and recommended action.",
]

# Weekly review items for v1
WEEKLY_REVIEW_ITEMS = [
    "Run: workflow-dataset stability-reviews generate — then stability-decision pack.",
    "Review: workflow-dataset v1-ops maintenance-pack — rhythm, recovery paths, rollback readiness.",
    "Review: workflow-dataset v1-ops review-cadence — next due and overdue.",
]

# When v1 degrades: what to do
WHEN_V1_DEGRADES = [
    "Check supportability: workflow-dataset supportability. If guidance is needs_operator or needs_rollback, follow recommended_next_support_action.",
    "Check stability decision: workflow-dataset stability-decision pack. If decision is repair, follow repair actions; if pause or rollback, follow that path.",
    "Check repair loops: workflow-dataset repair-loops list. If top repair needed, run repair or escalate.",
    "Recovery: workflow-dataset recovery guide (or recovery suggest) for matched playbook; workflow-dataset deploy-bundle recovery-report for bundle recovery.",
]

# What can be repaired safely (production-cut-safe repair discipline)
SAFE_REPAIR_ACTIONS = [
    "Repair loops that have bounded plans and rollback_command defined — run repair-loops execute then verify; on failure use repair-loops rollback.",
    "Approval/trust fixes — create or fix approval registry; review human_policy; run trust status.",
    "Workspace/context fixes — fix or reset workspace state; re-run reliability golden path after fix.",
    "Pack suspend/uninstall for broken pack — workflow-dataset packs suspend / uninstall; then re-run reliability.",
]

# What requires rollback
REQUIRES_ROLLBACK = [
    "Post-deployment guidance = needs_rollback or rollback.",
    "Stability decision = rollback.",
    "Rollback policy evaluation recommends rollback (e.g. consecutive pause count exceeded).",
    "Failed upgrade with no safe repair path — revert to last checkpoint: workflow-dataset release rollback.",
]

# What requires pause or narrow deployment
REQUIRES_PAUSE_OR_NARROW = [
    "Stability decision = pause — narrow cohort or pause new deployments until repair.",
    "Stability decision = narrow — reduce deployment scope (e.g. cohort, vertical) per pack recommendation.",
    "Multiple blockers or repeated repair failures — consider pause then repair or rollback.",
]


def get_daily_review_items() -> list[str]:
    """Return what to review daily for v1."""
    return list(DAILY_REVIEW_ITEMS)


def get_weekly_review_items() -> list[str]:
    """Return what to review weekly for v1."""
    return list(WEEKLY_REVIEW_ITEMS)


def get_when_v1_degrades() -> list[str]:
    """Return what to do when v1 degrades."""
    return list(WHEN_V1_DEGRADES)


def get_safe_repair_actions() -> list[str]:
    """Return what can be repaired safely (production-cut-safe)."""
    return list(SAFE_REPAIR_ACTIONS)


def get_requires_rollback() -> list[str]:
    """Return conditions that require rollback."""
    return list(REQUIRES_ROLLBACK)


def get_requires_pause_or_narrow() -> list[str]:
    """Return conditions that require pause or narrow deployment."""
    return list(REQUIRES_PAUSE_OR_NARROW)
