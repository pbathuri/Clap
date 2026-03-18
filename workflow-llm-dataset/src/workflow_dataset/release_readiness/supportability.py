"""
M30I–M30L: Triage and supportability — reproducible state summary, supportability report, guidance (safe_to_continue / needs_operator / needs_rollback).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.release_readiness.readiness import build_release_readiness
from workflow_dataset.release_readiness.models import GUIDANCE_SAFE_TO_CONTINUE, GUIDANCE_NEEDS_OPERATOR, GUIDANCE_NEEDS_ROLLBACK


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


# Structured issue triage template (fields for reproducible state)
TRIAGE_TEMPLATE = {
    "title": "Issue / support triage",
    "fields": [
        "reproducible_state_summary_path",
        "release_readiness_status",
        "highest_severity_blocker",
        "environment_ok",
        "acceptance_outcome",
        "recommended_next_support_action",
        "guidance",
        "steps_to_reproduce",
    ],
}


def build_reproducible_state_summary(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build a reproducible state summary for triage: readiness, mission_control snapshot keys, support bundle ref, env, acceptance.
    """
    root = _repo_root(repo_root)
    readiness = build_release_readiness(root)
    out: dict[str, Any] = {
        "release_readiness_status": readiness.status,
        "blocker_count": len(readiness.blockers),
        "warning_count": len(readiness.warnings),
        "supportability_confidence": readiness.supportability.confidence,
        "guidance": readiness.supportability.guidance,
    }
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        state = get_mission_control_state(root)
        out["goal_plan"] = bool(state.get("goal_plan"))
        out["project_case"] = bool(state.get("project_case") and state.get("project_case", {}).get("active_project_id"))
        out["executor"] = state.get("executor", {}).get("status")
        out["supervised_loop"] = state.get("supervised_loop", {}).get("status")
        env = state.get("environment_health") or {}
        out["environment_required_ok"] = env.get("required_ok")
    except Exception as e:
        out["mission_control_error"] = str(e)
    try:
        from workflow_dataset.rollout.support_bundle import build_support_bundle_summary_only
        out["support_bundle_summary_keys"] = list((build_support_bundle_summary_only(root) or {}).keys())
    except Exception:
        pass
    return out


def build_supportability_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build supportability report: readiness, reproducible state summary, recommended next support action, guidance.
    """
    root = _repo_root(repo_root)
    readiness = build_release_readiness(root)
    state_summary = build_reproducible_state_summary(root)
    return {
        "release_readiness_status": readiness.status,
        "reproducible_state_summary": state_summary,
        "recommended_next_support_action": readiness.supportability.recommended_next_support_action,
        "guidance": readiness.supportability.guidance,
        "blockers": [b.to_dict() for b in readiness.blockers],
        "warnings": [w.to_dict() for w in readiness.warnings],
        "triage_template": TRIAGE_TEMPLATE,
    }


def format_supportability_report(repo_root: Path | str | None = None) -> str:
    """Format supportability report as readable text."""
    r = build_supportability_report(repo_root)
    lines = [
        "=== Supportability report ===",
        "",
        "Release readiness: " + r["release_readiness_status"],
        "Guidance: " + r["guidance"],
        "",
        "Recommended next support action:",
        "  " + r["recommended_next_support_action"],
        "",
        "[Reproducible state summary]",
    ]
    for k, v in (r.get("reproducible_state_summary") or {}).items():
        if k != "support_bundle_summary_keys":
            lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("[Blockers]")
    for b in r.get("blockers") or []:
        lines.append("  - " + b.get("summary", ""))
    if not r.get("blockers"):
        lines.append("  (none)")
    lines.append("")
    lines.append("[Triage template fields] " + ", ".join(TRIAGE_TEMPLATE["fields"]))
    return "\n".join(lines)


def build_triage_output(repo_root: Path | str | None = None, latest_only: bool = True) -> dict[str, Any]:
    """
    Build triage output for --latest: reproducible state, readiness, guidance, recommended action.
    """
    root = _repo_root(repo_root)
    readiness = build_release_readiness(root)
    state_summary = build_reproducible_state_summary(root)
    highest_blocker = readiness.blockers[0].summary if readiness.blockers else None
    return {
        "reproducible_state_summary": state_summary,
        "release_readiness_status": readiness.status,
        "highest_severity_blocker": highest_blocker,
        "guidance": readiness.supportability.guidance,
        "recommended_next_support_action": readiness.supportability.recommended_next_support_action,
        "triage_template_fields": TRIAGE_TEMPLATE["fields"],
    }
