"""
M30H.1: Safe fallback matrix — when a subsystem is unavailable, what to disable and what to use instead.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.reliability.models import FallbackRule


# Subsystem -> list of fallback rules (safe routing when that subsystem is down).
FALLBACK_MATRIX: dict[str, list[FallbackRule]] = {
    "install": [
        FallbackRule(
            when_subsystem_unavailable="install",
            disable_flows=["golden_first_run", "project_plan_approve_simulate", "pack_install_behavior_query", "recovery_blocked_upgrade"],
            fallback_capability="read_only_ops",
            operator_explanation="Use inbox, trust status, workspace read-only, recovery suggest. Run package install-check and fix prerequisites before re-running golden paths.",
        ),
    ],
    "distribution": [
        FallbackRule(
            when_subsystem_unavailable="distribution",
            disable_flows=["recovery_blocked_upgrade", "upgrade_apply"],
            fallback_capability="current_version_only",
            operator_explanation="Upgrade and migration paths disabled. Remain on current version; use install check and recovery guide failed_upgrade when ready.",
        ),
    ],
    "packs": [
        FallbackRule(
            when_subsystem_unavailable="packs",
            disable_flows=["pack_install_behavior_query", "behavior_resolution", "workspace_command_query"],
            fallback_capability="no_pack_context",
            operator_explanation="Pack-dependent flows disabled. First-run (without pack steps), inbox, trust, planner without pack context still available. Run recovery guide broken_pack_state.",
        ),
    ],
    "runtime_mesh": [
        FallbackRule(
            when_subsystem_unavailable="runtime_mesh",
            disable_flows=["pack_install_behavior_query", "behavior_resolution"],
            fallback_capability="local_templates_only",
            operator_explanation="Behavior resolution and pack-runtime flows disabled. Use local templates and recovery guide missing_runtime_capability.",
        ),
    ],
    "trust": [
        FallbackRule(
            when_subsystem_unavailable="trust",
            disable_flows=["real apply", "approval_gated_execution", "review_inbox_approve_progress"],
            fallback_capability="simulate_only",
            operator_explanation="Real apply and approval-gated execution disabled. Simulate-only, inbox, planner, workspace still work. Run recovery guide blocked_approval_policy.",
        ),
    ],
    "human_policy": [
        FallbackRule(
            when_subsystem_unavailable="human_policy",
            disable_flows=["review_inbox_approve_progress", "approve_defer_workflow"],
            fallback_capability="simulate_only",
            operator_explanation="Approve/defer and policy-gated flows disabled. Simulate and read-only flows available.",
        ),
    ],
    "workspace": [
        FallbackRule(
            when_subsystem_unavailable="workspace",
            disable_flows=["workspace_command_query", "command_center_workspace_filter"],
            fallback_capability="workspace_read_only",
            operator_explanation="Workspace command query disabled. Core flows and workspace read-only available. Run recovery guide invalid_workspace_state.",
        ),
    ],
    "planner": [
        FallbackRule(
            when_subsystem_unavailable="planner",
            disable_flows=["project_plan_approve_simulate", "plan_preview", "simulate_available"],
            fallback_capability="no_plan_execution",
            operator_explanation="Plan compile and simulate execution disabled. First-run, inbox, trust, pack path may still work. Run recovery guide stuck_project_session_agent.",
        ),
    ],
    "executor": [
        FallbackRule(
            when_subsystem_unavailable="executor",
            disable_flows=["project_plan_approve_simulate", "simulate_available", "real apply"],
            fallback_capability="plan_only",
            operator_explanation="Execution and simulate disabled. Plan preview and read-only flows available.",
        ),
    ],
    "onboarding": [
        FallbackRule(
            when_subsystem_unavailable="onboarding",
            disable_flows=["golden_first_run"],
            fallback_capability="post_onboard_flows_only",
            operator_explanation="First-run blocked until onboarding complete. Other paths may work if already onboarded.",
        ),
    ],
    "inbox": [
        FallbackRule(
            when_subsystem_unavailable="inbox",
            disable_flows=["review_inbox_approve_progress", "inbox_digest"],
            fallback_capability="no_inbox",
            operator_explanation="Inbox and review-inbox flows disabled. Remaining golden paths and recovery still available.",
        ),
    ],
    "progress": [
        FallbackRule(
            when_subsystem_unavailable="progress",
            disable_flows=["review_inbox_approve_progress", "progress_board"],
            fallback_capability="no_progress_board",
            operator_explanation="Progress board and review-inbox progress update disabled. Other flows unchanged.",
        ),
    ],
}


def list_subsystems_with_fallback() -> list[str]:
    """Return subsystem ids that have fallback rules."""
    return sorted(FALLBACK_MATRIX.keys())


def get_fallback_rules(subsystem: str) -> list[FallbackRule]:
    """Return fallback rules for a subsystem (empty if none)."""
    return list(FALLBACK_MATRIX.get(subsystem, []))


def build_fallback_matrix_output(
    subsystem_filter: str | None = None,
) -> dict[str, Any]:
    """
    Build fallback matrix for CLI/report. If subsystem_filter is set, return only that row.
    Returns: { "matrix": { subsystem: [ rule_dict, ... ] }, "subsystems": [...] }.
    """
    rule_to_dict = lambda r: {
        "when_subsystem_unavailable": r.when_subsystem_unavailable,
        "disable_flows": r.disable_flows,
        "fallback_capability": r.fallback_capability,
        "operator_explanation": r.operator_explanation,
    }
    if subsystem_filter:
        rules = get_fallback_rules(subsystem_filter)
        return {
            "matrix": {subsystem_filter: [rule_to_dict(r) for r in rules]},
            "subsystems": [subsystem_filter],
        }
    matrix = {
        sub: [rule_to_dict(r) for r in rules]
        for sub, rules in FALLBACK_MATRIX.items()
    }
    return {
        "matrix": matrix,
        "subsystems": list_subsystems_with_fallback(),
    }


def format_fallback_matrix_text(matrix_output: dict[str, Any]) -> str:
    """Format matrix as human-readable text (operator explanation)."""
    lines = ["# Safe fallback matrix", ""]
    for sub in matrix_output.get("subsystems", []):
        rules = matrix_output.get("matrix", {}).get(sub, [])
        if not rules:
            continue
        lines.append(f"## When '{sub}' is unavailable")
        for r in rules:
            lines.append(f"  Disable: {', '.join(r.get('disable_flows', [])[:6])}")
            lines.append(f"  Fallback: {r.get('fallback_capability', '')}")
            lines.append(f"  → {r.get('operator_explanation', '')}")
        lines.append("")
    return "\n".join(lines).strip()
