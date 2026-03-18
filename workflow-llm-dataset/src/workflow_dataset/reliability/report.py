"""
M30E–M30H: Format reliability report for CLI and mission control.
M30H.1: Degraded profile and fallback matrix formatting.
"""

from __future__ import annotations

from typing import Any


def format_degraded_profile(profile: dict[str, Any]) -> str:
    """Format a degraded mode profile for operator (what still works vs disabled)."""
    lines = [
        f"# {profile.get('name', '')} ({profile.get('profile_id', '')})",
        "",
        profile.get("description", ""),
        "",
        "## Disabled subsystems",
        ", ".join(profile.get("disabled_subsystems", [])) or "—",
        "",
        "## Still works",
    ]
    for w in profile.get("still_works", []):
        lines.append(f"  • {w}")
    lines.extend(["", "## Disabled flows"])
    for f in profile.get("disabled_flows", []):
        lines.append(f"  ✗ {f}")
    lines.extend(["", "## Operator explanation", profile.get("operator_explanation", "")])
    return "\n".join(lines)


def format_reliability_report(run_result: dict[str, Any] | None) -> str:
    """Format a single reliability run as human-readable report. Returns empty string if run_result is None."""
    if not run_result:
        return "No reliability run found."
    lines = [
        f"Run: {run_result.get('run_id', '')}",
        f"Path: {run_result.get('path_id', '')} — {run_result.get('path_name', '')}",
        f"Outcome: {run_result.get('outcome', '')}",
    ]
    if run_result.get("subsystem"):
        lines.append(f"Subsystem: {run_result.get('subsystem')}")
    if run_result.get("failure_step_id"):
        lines.append(f"Failure step: {run_result.get('failure_step_id')} (index {run_result.get('failure_step_index')})")
    for r in run_result.get("reasons", []):
        lines.append(f"  • {r}")
    lines.append(f"Timestamp: {run_result.get('timestamp', '')}")
    if run_result.get("steps_results"):
        lines.append("Steps:")
        for sr in run_result["steps_results"]:
            step_id = sr.get("step_id", "")
            actual = sr.get("actual", {})
            err = actual.get("error")
            status = "error" if err else ("ok" if actual.get("passed", actual.get("ready", actual.get("runnable", actual.get("board_available", False)))) else "fail")
            lines.append(f"  - {step_id}: {status}" + (f" — {err}" if err else ""))
    return "\n".join(lines)
