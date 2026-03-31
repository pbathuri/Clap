"""
Task plan / approve / run payloads must be JSON-serializable for CLI --json and tooling.
No Typer/cli import required.
"""

from __future__ import annotations

import json
from pathlib import Path

from workflow_dataset.capability_discovery.approval_registry import ApprovalRegistry, save_approval_registry
from workflow_dataset.local_operator.task_planning import WORKFLOW_PATTERNS, plan_task
from workflow_dataset.local_operator.task_runs import approve_task_plan, run_task_plan


def _approved_path(path: str, ops: list[str] | None = None, **overrides):
    return {
        "path": path,
        "allowed_operations": ops or ["read"],
        "recursive": True,
        "inherit_mode": "inherit",
        "sensitivity_tag": "unspecified",
        "approval_source": "explicit_user",
        "revocation_state": "active",
        "approved_at": "",
        "reviewed_at": "",
        "expires_at": "",
        **overrides,
    }


def test_plan_task_json_serializable_all_branches(tmp_path: Path) -> None:
    empty = plan_task("Inspect folder", repo_root=tmp_path)
    json.dumps(empty, default=str)
    assert empty.get("status") == "unsupported"

    alpha = tmp_path / "proj"
    alpha.mkdir()
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(alpha), ["read", "write"])])
    save_approval_registry(reg, tmp_path)
    ok = plan_task("Inspect folder and create a structured status report", repo_root=tmp_path)
    json.dumps(ok, default=str)
    assert ok.get("status") == "planned"
    assert ok.get("workflow_pattern") in WORKFLOW_PATTERNS


def test_approve_and_run_json_serializable(tmp_path: Path) -> None:
    folder = tmp_path / "w"
    folder.mkdir()
    (folder / "README.md").write_text("x", encoding="utf-8")
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(folder), ["read", "write"])])
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Inspect folder and create a structured status report", repo_root=tmp_path)
    assert plan["status"] == "planned"

    bad = approve_task_plan("plan_nonexistent", repo_root=tmp_path)
    json.dumps(bad, default=str)
    assert bad.get("error")

    approved = approve_task_plan(plan["plan_id"], repo_root=tmp_path)
    json.dumps(approved, default=str)
    assert approved.get("approved") is True

    blocked = run_task_plan(plan["plan_id"], approved=False, repo_root=tmp_path)
    json.dumps(blocked, default=str)
    assert blocked.get("status") == "blocked"

    done = run_task_plan(plan["plan_id"], approved=True, repo_root=tmp_path)
    json.dumps(done, default=str)
    assert done.get("status") == "completed"
    assert done.get("steps")
