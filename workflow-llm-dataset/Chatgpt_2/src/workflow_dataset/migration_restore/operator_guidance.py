"""
M49H.1: Operator-facing guidance after restore.
What was restored, what was rebuilt, what still needs review.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.migration_restore.flows import conflict_aware_reconcile


def build_restore_operator_summary(
    restore_result: dict[str, Any],
    reconcile_result: dict[str, Any] | None = None,
    restore_candidate_id: str = "",
    target_repo_root: Any = None,
) -> dict[str, Any]:
    """
    Build operator-facing summary: what was restored, what was rebuilt, what still needs review.
    If reconcile_result is None and restore_candidate_id is set, calls conflict_aware_reconcile to get it.
    """
    if reconcile_result is None and restore_candidate_id:
        try:
            reconcile_result = conflict_aware_reconcile(restore_candidate_id, target_repo_root=target_repo_root)
        except Exception:
            reconcile_result = {}

    applied = list(restore_result.get("applied_subsystems") or [])
    rebuild_required = [r.get("subsystem_id", "") for r in (reconcile_result or {}).get("rebuild_required", []) if r.get("subsystem_id")]
    reconcile_actions = reconcile_result.get("reconcile_actions", []) if reconcile_result else []
    needs_review = [a for a in reconcile_actions if a.get("requires_review") or a.get("kind") in ("overwrite_target", "resolve_conflict")]
    needs_review_subsystems = list(dict.fromkeys([a.get("subsystem_id", "") for a in needs_review if a.get("subsystem_id")]))

    summary_lines: list[str] = []
    summary_lines.append("--- Restore operator summary ---")
    summary_lines.append("What was restored: " + (", ".join(applied) if applied else "none (dry-run or not approved)"))
    summary_lines.append("What was rebuilt (or must be): " + (", ".join(rebuild_required) if rebuild_required else "none"))
    summary_lines.append("What still needs review: " + (", ".join(needs_review_subsystems) if needs_review_subsystems else "nothing"))

    return {
        "restore_candidate_id": restore_result.get("candidate_id", "") or restore_candidate_id,
        "status": restore_result.get("status", ""),
        "what_was_restored": applied,
        "what_was_rebuilt": rebuild_required,
        "what_still_needs_review": needs_review_subsystems,
        "summary_lines": summary_lines,
        "reconcile_actions_count": len(reconcile_actions),
        "rebuild_required_count": len(rebuild_required),
    }


def format_operator_summary_text(summary: dict[str, Any]) -> str:
    """Plain-text operator-facing summary."""
    lines = summary.get("summary_lines", [])
    if not lines:
        return "No summary available."
    return "\n".join(lines)
