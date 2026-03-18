"""
M24C: Acceptance report — summarize scenario outcome, where succeeded, where blocked, where failed, ready for trial.
"""

from __future__ import annotations

from typing import Any


def format_acceptance_report(run_result: dict[str, Any] | None) -> str:
    """
    Produce human-readable acceptance report: scenario outcome, where succeeded,
    where blocked correctly, where failed unexpectedly, ready for real-user trial.
    """
    if not run_result:
        return "No run result to report."

    scenario_id = run_result.get("scenario_id", "")
    value_pack_id = ""
    try:
        from workflow_dataset.acceptance.scenarios import get_scenario
        from workflow_dataset.value_packs.recommend import STARTER_KIT_TO_VALUE_PACK
        scenario = get_scenario(scenario_id) if scenario_id else None
        if scenario and scenario.starter_kit_id:
            value_pack_id = STARTER_KIT_TO_VALUE_PACK.get(scenario.starter_kit_id, "")
    except Exception:
        pass

    lines = [
        "=== Acceptance report (M24C) ===",
        "",
        f"Scenario: {run_result.get('scenario_name', run_result.get('scenario_id', ''))}",
        f"Outcome: {run_result.get('outcome', '')}",
        "",
    ]
    if value_pack_id:
        lines.append(f"Value pack for this scenario: {value_pack_id} (workflow-dataset value-packs show --id {value_pack_id})")
        lines.append("")
    lines.append("--- Reasons ---")
    lines.append("")
    for r in run_result.get("reasons", []):
        lines.append(f"  · {r}")
    lines.append("")

    # Where succeeded
    steps = run_result.get("steps_results", [])
    succeeded = [s["step_id"] for s in steps if not s.get("actual", {}).get("error") and not s.get("actual", {}).get("skipped")]
    lines.append("--- Where the system succeeded ---")
    lines.append("")
    if succeeded:
        for step_id in succeeded:
            lines.append(f"  · {step_id}")
    else:
        lines.append("  (none)")
    lines.append("")

    # Where blocked (expected)
    outcome = run_result.get("outcome", "")
    if outcome == "blocked":
        lines.append("--- Where it blocked (expected or fixable) ---")
        lines.append("")
        for r in run_result.get("reasons", []):
            lines.append(f"  · {r}")
        lines.append("")
    elif outcome == "partial":
        lines.append("--- Partial: some steps met, some blocked ---")
        lines.append("")
        for r in run_result.get("reasons", []):
            lines.append(f"  · {r}")
        lines.append("")

    # Where failed unexpectedly
    failed_steps = [s["step_id"] for s in steps if s.get("actual", {}).get("error")]
    if failed_steps:
        lines.append("--- Where it failed unexpectedly ---")
        lines.append("")
        for s in steps:
            if s.get("actual", {}).get("error"):
                lines.append(f"  · {s['step_id']}: {s['actual'].get('error')}")
        lines.append("")

    # Ready for trial
    ready = run_result.get("ready_for_trial", False)
    lines.append("--- Ready for real-user trial? ---")
    lines.append("")
    lines.append("  " + ("Yes. Evidence: all critical steps met; product ready for controlled first-user rollout." if ready else "No. Address reasons above before a small real-user rollout."))
    lines.append("")
    lines.append("(Acceptance harness is report-only; no automatic execution of real actions.)")
    return "\n".join(lines)
