"""
M21X: Eval case format — case JSON, suite JSON. Supports weekly_status, status_action_bundle, stakeholder_update_bundle, ops_reporting_workspace.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.eval.config import get_cases_dir, get_eval_root, get_suites_dir

WORKFLOWS = ("weekly_status", "status_action_bundle", "stakeholder_update_bundle", "ops_reporting_workspace")


def add_case(
    case_id: str,
    workflow: str,
    task_context: str,
    root: Path | str | None = None,
    context_file: str = "",
    retrieval: bool = False,
    rubric_hints: str = "",
) -> Path:
    """Add an evaluation case. Writes cases/<case_id>.json. Returns path to case file."""
    cases_dir = get_cases_dir(root)
    case: dict[str, Any] = {
        "case_id": case_id,
        "workflow": workflow,
        "task_context": task_context,
    }
    if context_file:
        case["context_file"] = context_file
    if retrieval:
        case["retrieval"] = True
    if rubric_hints:
        case["rubric_hints"] = rubric_hints
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in case_id).strip("_") or "case"
    path = cases_dir / f"{safe_id}.json"
    path.write_text(json.dumps(case, indent=2), encoding="utf-8")
    return path


def load_case(path: Path | str) -> dict[str, Any] | None:
    """Load a case from JSON file."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_cases(root: Path | str | None = None) -> list[dict[str, Any]]:
    """List all cases from cases dir."""
    cases_dir = get_cases_dir(root)
    out: list[dict[str, Any]] = []
    for f in sorted(cases_dir.glob("*.json")):
        c = load_case(f)
        if c:
            out.append(c)
    return out


def _find_case_by_id(cases_dir: Path | str, case_id: str) -> dict[str, Any] | None:
    """Find case by id in cases dir (by filename stem or case_id in JSON)."""
    cases_dir = Path(cases_dir)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in case_id).strip("_")
    p = cases_dir / f"{safe_id}.json"
    if p.exists():
        return load_case(p)
    for f in cases_dir.glob("*.json"):
        c = load_case(f)
        if c and (c.get("case_id") == case_id or f.stem == case_id):
            return c
    return None


def load_suite(suite_name: str, root: Path | str | None = None) -> list[dict[str, Any]]:
    """Load suite: list of case dicts. Suite JSON contains list of case_ids."""
    suites_dir = get_suites_dir(root)
    cases_dir = get_cases_dir(root)
    path = suites_dir / f"{suite_name}.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        case_ids = data if isinstance(data, list) else data.get("cases", data.get("case_ids", []))
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for cid in case_ids:
        c = _find_case_by_id(cases_dir, cid if isinstance(cid, str) else cid.get("case_id", ""))
        if c:
            out.append(c)
    return out


def seed_default_cases(root: Path | str | None = None) -> list[dict[str, Any]]:
    """Seed default ops_reporting_core cases (4 cases) and suite. Returns list of case dicts."""
    cases_dir = get_cases_dir(root)
    suites_dir = get_suites_dir(root)
    defaults = [
        {"case_id": "weekly_status_project_delivery", "workflow": "weekly_status", "task_context": "Project delivery status: shipped last week; blocker on API approval."},
        {"case_id": "weekly_status_risk_focus", "workflow": "weekly_status", "task_context": "Focus on risks: schedule slip, dependency on design."},
        {"case_id": "status_action_bundle_ops", "workflow": "status_action_bundle", "task_context": "Ops actions: follow up with PM, unblock deployment."},
        {"case_id": "ops_reporting_workspace_core", "workflow": "ops_reporting_workspace", "task_context": "Core ops reporting: status, actions, stakeholder summary."},
    ]
    for c in defaults:
        path = cases_dir / f"{c['case_id']}.json"
        path.write_text(json.dumps(c, indent=2), encoding="utf-8")
    suite_path = suites_dir / "ops_reporting_core.json"
    suite_path.write_text(json.dumps([c["case_id"] for c in defaults], indent=2), encoding="utf-8")
    return [load_case(cases_dir / f"{c['case_id']}.json") for c in defaults]


def seed_expanded_cases(root: Path | str | None = None) -> list[dict[str, Any]]:
    """Seed expanded case library (12 cases, 4 workflows) and suite ops_reporting_expanded."""
    cases_dir = get_cases_dir(root)
    suites_dir = get_suites_dir(root)
    expanded = [
        {"case_id": "weekly_status_project_delivery", "workflow": "weekly_status", "task_context": "Project delivery status."},
        {"case_id": "weekly_status_risk_focus", "workflow": "weekly_status", "task_context": "Risks focus."},
        {"case_id": "weekly_status_next_steps", "workflow": "weekly_status", "task_context": "Next steps clarity."},
        {"case_id": "status_action_bundle_ops", "workflow": "status_action_bundle", "task_context": "Ops actions."},
        {"case_id": "status_action_bundle_pm", "workflow": "status_action_bundle", "task_context": "PM handoff actions."},
        {"case_id": "status_action_bundle_stakeholder", "workflow": "status_action_bundle", "task_context": "Stakeholder actions."},
        {"case_id": "stakeholder_update_bundle_exec", "workflow": "stakeholder_update_bundle", "task_context": "Executive summary."},
        {"case_id": "stakeholder_update_bundle_team", "workflow": "stakeholder_update_bundle", "task_context": "Team update."},
        {"case_id": "stakeholder_update_bundle_external", "workflow": "stakeholder_update_bundle", "task_context": "External stakeholder."},
        {"case_id": "ops_reporting_workspace_core", "workflow": "ops_reporting_workspace", "task_context": "Core ops reporting."},
        {"case_id": "ops_reporting_workspace_detailed", "workflow": "ops_reporting_workspace", "task_context": "Detailed ops report."},
        {"case_id": "ops_reporting_workspace_brief", "workflow": "ops_reporting_workspace", "task_context": "Brief status."},
    ]
    for c in expanded:
        path = cases_dir / f"{c['case_id']}.json"
        path.write_text(json.dumps(c, indent=2), encoding="utf-8")
    suite_path = suites_dir / "ops_reporting_expanded.json"
    suite_path.write_text(json.dumps([c["case_id"] for c in expanded], indent=2), encoding="utf-8")
    return [load_case(cases_dir / f"{c['case_id']}.json") for c in expanded]
