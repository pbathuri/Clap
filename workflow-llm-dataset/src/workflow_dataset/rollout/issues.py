"""
M24F: Issue report — template for support/issue bundle (environment, runtime, pack state,
acceptance outcome, trust, steps to reproduce).
"""

from __future__ import annotations

from typing import Any


def format_issues_report(bundle_summary: dict[str, Any] | None) -> str:
    """
    Format a local operator issue summary from support bundle summary or rollout state.
    Use for handoff to support or for go/no-go notes.
    """
    if not bundle_summary:
        return _skeleton()

    lines = [
        "--- Support / issue summary (local operator bundle) ---",
        "",
        "Environment:",
    ]
    env = bundle_summary.get("environment_health") or {}
    if isinstance(env, dict) and env.get("error"):
        lines.append("  Error: " + str(env["error"]))
    else:
        for k, v in (env or {}).items():
            if k != "error":
                lines.append(f"  {k}: {v}")
    lines.append("")

    lines.append("Runtime mesh:")
    mesh = bundle_summary.get("runtime_mesh") or {}
    if isinstance(mesh, dict):
        for k, v in mesh.items():
            if k != "error":
                lines.append(f"  {k}: {v}")
    lines.append("")

    lines.append("Starter kits / pack state:")
    kits = bundle_summary.get("starter_kits") or {}
    if isinstance(kits, dict):
        for k, v in kits.items():
            if k != "error":
                lines.append(f"  {k}: {v}")
    lines.append("")

    acc = bundle_summary.get("latest_acceptance") or {}
    if isinstance(acc, dict) and acc.get("error"):
        lines.append("Latest acceptance: Error: " + str(acc["error"]))
    else:
        lines.append("Latest acceptance:")
        lines.append(f"  scenario_id: {acc.get('scenario_id')}")
        lines.append(f"  outcome: {acc.get('outcome')}")
        lines.append(f"  ready_for_trial: {acc.get('ready_for_trial')}")
        for r in acc.get("reasons") or []:
            lines.append(f"  reason: {r}")
    lines.append("")

    rollout = bundle_summary.get("rollout_state") or {}
    if isinstance(rollout, dict) and not rollout.get("error"):
        lines.append("Rollout state:")
        lines.append(f"  target_scenario_id: {rollout.get('target_scenario_id')}")
        lines.append(f"  current_stage: {rollout.get('current_stage')}")
        lines.append(f"  next_required_action: {rollout.get('next_required_action')}")
        for b in rollout.get("blocked_items") or []:
            lines.append(f"  blocked: {b}")
    lines.append("")

    trust = bundle_summary.get("trust_cockpit") or {}
    if isinstance(trust, dict) and trust:
        lines.append("Trust cockpit: (see trust_cockpit.json in bundle)")
    lines.append("")

    lines.append("Steps to reproduce / operator actions:")
    lines.append("  1. workflow-dataset rollout status")
    lines.append("  2. workflow-dataset acceptance report")
    lines.append("  3. workflow-dataset trust cockpit")
    lines.append("  4. workflow-dataset mission-control")
    lines.append("")
    lines.append("--- End of issue summary ---")
    return "\n".join(lines)


def _skeleton() -> str:
    return """--- Support / issue summary (local operator bundle) ---

Environment: (not collected)
Runtime mesh: (not collected)
Starter kits: (not collected)
Latest acceptance: (not collected)
Rollout state: (not collected)

Steps to reproduce:
  1. workflow-dataset rollout status
  2. workflow-dataset acceptance report
  3. workflow-dataset trust cockpit
  4. workflow-dataset mission-control

--- End of issue summary ---
"""
