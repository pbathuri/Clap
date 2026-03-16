"""
M21X: Eval harness — run one case or a suite. Creates run dir, manifest, and captures outputs.
Placeholder execution (writes artifact from task_context) when no LLM config; no hidden model dependence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.eval.case_format import _find_case_by_id, load_suite
from workflow_dataset.eval.config import get_cases_dir, get_runs_dir
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def run_case(
    case_id: str,
    case_path: str | Path | None = None,
    llm_config_path: str | Path | None = None,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Run a single eval case. Creates run dir, writes placeholder artifact, run_manifest. Returns run_id, run_path, suite; or error."""
    runs_dir = get_runs_dir(root)
    cases_dir = get_cases_dir(root)
    case = None
    if case_path:
        p = Path(case_path)
        if p.exists():
            from workflow_dataset.eval.case_format import load_case
            case = load_case(p)
    if not case:
        case = _find_case_by_id(cases_dir, case_id)
    if not case:
        return {"error": f"Case not found: {case_id}"}
    run_id = stable_id("run", case_id, utc_now_iso(), prefix="")[:16]
    run_path = runs_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    case_dir = run_path / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    workflow = case.get("workflow", "weekly_status")
    task = case.get("task_context", "")
    artifact_name = "weekly_status.md" if workflow == "weekly_status" else f"{workflow}.md"
    placeholder = f"**Summary** {task[:200]}.\n**Wins** —\n**Blockers** —\n**Risks** —\n**Next steps** —\n"
    (case_dir / artifact_name).write_text(placeholder, encoding="utf-8")
    manifest = {
        "run_id": run_id,
        "suite": "single",
        "timestamp": utc_now_iso(),
        "cases": [
            {"case_id": case_id, "workflow": workflow, "output_dir": str(case_dir)},
        ],
        "run_path": str(run_path),
    }
    (run_path / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"run_id": run_id, "run_path": str(run_path), "suite": "single"}


def run_suite(
    suite_name: str,
    llm_config_path: str | Path | None = None,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Run benchmark suite. Loads cases, creates run dir, writes placeholder artifact per case, run_manifest. Returns run_id, run_path; or error."""
    cases = load_suite(suite_name, root)
    if not cases:
        return {"error": f"Suite not found or empty: {suite_name}"}
    runs_dir = get_runs_dir(root)
    run_id = stable_id("run", suite_name, utc_now_iso(), prefix="")[:16]
    run_path = runs_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    case_entries: list[dict[str, Any]] = []
    for c in cases:
        cid = c.get("case_id", "case")
        case_dir = run_path / cid
        case_dir.mkdir(parents=True, exist_ok=True)
        workflow = c.get("workflow", "weekly_status")
        task = c.get("task_context", "")
        artifact_name = "weekly_status.md" if workflow == "weekly_status" else f"{workflow}.md"
        placeholder = f"**Summary** {task[:200]}.\n**Wins** —\n**Blockers** —\n**Risks** —\n**Next steps** —\n"
        (case_dir / artifact_name).write_text(placeholder, encoding="utf-8")
        case_entries.append({"case_id": cid, "workflow": workflow, "output_dir": str(case_dir)})
    manifest = {
        "run_id": run_id,
        "suite": suite_name,
        "timestamp": utc_now_iso(),
        "cases": case_entries,
        "run_path": str(run_path),
    }
    (run_path / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"run_id": run_id, "run_path": str(run_path)}
