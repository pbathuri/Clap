"""
Task plan/run storage roundtrip tests.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from workflow_dataset.capability_discovery.approval_registry import (
    ApprovalRegistry,
    save_approval_registry,
)
from workflow_dataset.desktop_adapters.execute import run_execute
from workflow_dataset.local_operator.task_planning import (
    WORKFLOW_PATTERNS,
    _infer_workflow_pattern,
    plan_task,
)
from workflow_dataset.local_operator.task_runs import approve_task_plan, run_task_plan
from workflow_dataset.local_operator.summary import build_operator_state_summary
from workflow_dataset.local_operator.task_store import (
    compact_steps_preview,
    get_task_plans_dir,
    get_task_runs_dir,
    list_recent_task_run_summaries,
    list_task_plans,
    list_task_runs,
    load_task_plan,
    load_task_run,
    save_task_plan,
    save_task_run,
)

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


def test_task_plan_store_roundtrip(tmp_path) -> None:
    plan = {"plan_id": "plan_alpha", "steps": [{"label": "Draft outline", "order": 1}]}
    path = save_task_plan(plan, repo_root=tmp_path)
    assert path.parent == get_task_plans_dir(tmp_path)
    loaded = load_task_plan("plan_alpha", repo_root=tmp_path)
    assert loaded == plan
    assert "plan_alpha" in list_task_plans(repo_root=tmp_path)


def test_task_run_store_roundtrip(tmp_path) -> None:
    run = {"run_id": "run_alpha", "status": "complete", "metrics": {"duration_s": 12}}
    path = save_task_run(run, repo_root=tmp_path)
    assert path.parent == get_task_runs_dir(tmp_path)
    loaded = load_task_run("run_alpha", repo_root=tmp_path)
    assert loaded == run
    assert "run_alpha" in list_task_runs(repo_root=tmp_path)


def test_plan_task_selects_matching_folder(tmp_path: Path) -> None:
    alpha = tmp_path / "alpha-project"
    beta = tmp_path / "beta-project"
    alpha.mkdir()
    beta.mkdir()
    reg = ApprovalRegistry(
        approved_paths=[
            _approved_path(str(alpha), ["read", "write"]),
            _approved_path(str(beta), ["read", "write"]),
        ],
    )
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Summarize beta project", repo_root=tmp_path)
    assert plan["status"] == "planned"
    assert plan["approved_scope"]["path"] == str(beta)


def test_plan_task_unsupported_without_approved_paths(tmp_path: Path) -> None:
    plan = plan_task("Summarize folder", repo_root=tmp_path)
    assert plan["status"] == "unsupported"
    assert plan["reason"] == "no_approved_folders"
    assert plan["steps"] == []
    assert plan["approved_scope"] == {}
    assert plan.get("supported_workflow_patterns") == list(WORKFLOW_PATTERNS)
    loaded = load_task_plan(plan["plan_id"], repo_root=tmp_path)
    assert loaded == plan


def test_plan_task_falls_back_to_first_active_entry(tmp_path: Path) -> None:
    beta = tmp_path / "beta-project"
    alpha = tmp_path / "alpha-project"
    beta.mkdir()
    alpha.mkdir()
    reg = ApprovalRegistry(
        approved_paths=[
            _approved_path(str(beta), ["read", "write"]),
            _approved_path(str(alpha), ["read", "write"]),
        ],
    )
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Summarize gamma project", repo_root=tmp_path)
    assert plan["status"] == "planned"
    assert plan["approved_scope"]["path"] == str(alpha)


def test_plan_task_steps_structure(tmp_path: Path) -> None:
    alpha = tmp_path / "alpha-project"
    alpha.mkdir()
    reg = ApprovalRegistry(
        approved_paths=[
            _approved_path(str(alpha), ["read", "write"]),
        ],
    )
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Summarize alpha project", repo_root=tmp_path)
    assert plan["status"] == "planned"
    assert plan["workflow_pattern"] in WORKFLOW_PATTERNS
    steps = plan["steps"]
    assert [step["step_id"] for step in steps] == [
        "list_directory",
        "infer_project_context",
        "summarize_notes",
        "write_artifact",
    ]
    assert steps[0]["params"]["path"] == str(alpha)
    assert steps[2]["params"]["path"] == "<auto>"
    assert steps[2]["optional"] is True
    assert steps[3]["params"]["path"] == "<auto>"
    assert steps[3]["params"]["content"] == "<auto>"


def test_plan_includes_workflow_pattern(tmp_path: Path) -> None:
    alpha = tmp_path / "alpha"
    alpha.mkdir()
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(alpha), ["read", "write"])])
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Summarize alpha project", repo_root=tmp_path)
    assert plan["status"] == "planned"
    assert plan.get("workflow_pattern") in WORKFLOW_PATTERNS


def test_infer_workflow_pattern() -> None:
    assert _infer_workflow_pattern("summarize folder") == "inspect_status_report"
    assert _infer_workflow_pattern("summarize alpha project") == "inspect_project_brief"
    assert _infer_workflow_pattern("create a status report") == "inspect_status_report"
    assert _infer_workflow_pattern("structured status report") == "inspect_status_report"
    assert _infer_workflow_pattern("open folder in Finder") == "inspect_finder_report"
    assert _infer_workflow_pattern("show folder in finder") == "inspect_finder_report"
    assert _infer_workflow_pattern("send an email to customer") is None


def test_plan_finder_report_includes_open_step(tmp_path: Path) -> None:
    alpha = tmp_path / "alpha"
    alpha.mkdir()
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(alpha), ["read", "write"])])
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Open folder in Finder and create report", repo_root=tmp_path)
    assert plan["status"] == "planned"
    assert plan["workflow_pattern"] == "inspect_finder_report"
    step_ids = [s["step_id"] for s in plan["steps"]]
    assert "open_finder" in step_ids
    assert step_ids.index("open_finder") < step_ids.index("summarize_notes")


def test_plan_task_unsupported_without_write_scope(tmp_path: Path) -> None:
    alpha = tmp_path / "alpha-project"
    alpha.mkdir()
    reg = ApprovalRegistry(
        approved_paths=[
            _approved_path(str(alpha), ["read"]),
        ],
    )
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Summarize alpha project", repo_root=tmp_path)
    assert plan["status"] == "unsupported"
    assert plan["reason"] == "no_write_scope"
    assert plan["steps"] == []
    assert plan["approved_scope"] == {}
    loaded = load_task_plan(plan["plan_id"], repo_root=tmp_path)
    assert loaded == plan


def test_plan_task_unsupported_for_unknown_intent(tmp_path: Path) -> None:
    alpha = tmp_path / "alpha-project"
    alpha.mkdir()
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(alpha), ["read", "write"])])
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Send an email to investors", repo_root=tmp_path)
    assert plan["status"] == "unsupported"
    assert plan["reason"] == "unsupported_prompt_intent"
    assert plan["steps"] == []
    assert plan.get("user_hint")
    assert plan.get("supported_workflow_patterns") == list(WORKFLOW_PATTERNS)


def test_unsupported_plans_include_actionable_hints(tmp_path: Path) -> None:
    plan_no_folders = plan_task("Inspect folder", repo_root=tmp_path)
    assert plan_no_folders["reason"] == "no_approved_folders"
    assert "approved" in (plan_no_folders.get("user_hint") or "").lower()

    alpha = tmp_path / "alpha-project"
    alpha.mkdir()
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(alpha), ["read"])])
    save_approval_registry(reg, tmp_path)
    plan_no_write = plan_task("Inspect folder", repo_root=tmp_path)
    assert plan_no_write["reason"] == "no_write_scope"
    assert "write" in (plan_no_write.get("user_hint") or "").lower()


def test_run_execute_write_file_with_approval(tmp_path: Path) -> None:
    target_path = tmp_path / "approved" / "output.txt"
    registry = ApprovalRegistry(
        approved_paths=[_approved_path(str(tmp_path), ["write"])],
    )
    save_approval_registry(registry, tmp_path)

    result = run_execute(
        "file_ops",
        "write_file",
        {"path": str(target_path), "content": "hello world"},
        repo_root=tmp_path,
    )

    assert result.success is True
    assert result.message == "ok"
    assert target_path.exists()
    assert target_path.read_text(encoding="utf-8") == "hello world"


def test_run_execute_write_file_blocked_without_write_scope(tmp_path: Path) -> None:
    target_path = tmp_path / "approved" / "output.txt"
    registry = ApprovalRegistry(
        approved_paths=[_approved_path(str(tmp_path), ["read"])],
    )
    save_approval_registry(registry, tmp_path)

    result = run_execute(
        "file_ops",
        "write_file",
        {"path": str(target_path), "content": "blocked"},
        repo_root=tmp_path,
    )

    assert result.success is False
    assert "not approved" in result.message
    assert target_path.exists() is False


def test_approve_unsupported_plan_returns_error(tmp_path: Path) -> None:
    plan = plan_task("Summarize project", repo_root=tmp_path)
    assert plan["status"] == "unsupported"

    result = approve_task_plan(plan["plan_id"], repo_root=tmp_path)

    assert result["error"] == "plan_not_executable"


def test_run_unsupported_plan_returns_failure(tmp_path: Path) -> None:
    plan = plan_task("Summarize project", repo_root=tmp_path)
    assert plan["status"] == "unsupported"

    result = run_task_plan(plan["plan_id"], approved=True, repo_root=tmp_path)

    assert result["status"] in {"failed", "blocked"}
    assert result["reason"] == "plan_not_executable"
    assert not result.get("artifact_path")


def test_run_requires_approval(tmp_path: Path) -> None:
    folder = tmp_path / "project"
    folder.mkdir()
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(folder), ["read", "write"])])
    save_approval_registry(reg, tmp_path)

    plan = plan_task("Summarize project", repo_root=tmp_path)
    result = run_task_plan(plan["plan_id"], approved=True, repo_root=tmp_path)

    assert result["status"] == "blocked"


def test_run_persists_summary(tmp_path: Path) -> None:
    folder = tmp_path / "project"
    folder.mkdir()
    (folder / "README.md").write_text("Hello world", encoding="utf-8")
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(folder), ["read", "write"])])
    save_approval_registry(reg, tmp_path)

    plan = plan_task("Summarize project", repo_root=tmp_path)
    approve_task_plan(plan["plan_id"], repo_root=tmp_path)
    result = run_task_plan(plan["plan_id"], approved=True, repo_root=tmp_path)

    assert result["status"] == "completed"
    assert result.get("workflow_pattern") in WORKFLOW_PATTERNS
    assert len(result["steps"]) >= 3
    for i, step in enumerate(result["steps"], 1):
        assert step.get("step_index") == i
        assert step.get("step_status") in ("completed", "failed")
        assert "completed_at" in step
        assert step.get("step_id") in (
            "list_directory",
            "identify_relevant_files",
            "infer_project_context",
            "summarize_notes",
            "open_finder",
            "write_artifact",
        )
    assert Path(result["artifact_path"]).exists()
    artifact_content = Path(result["artifact_path"]).read_text(encoding="utf-8")
    assert plan["prompt"] in artifact_content
    assert str(folder) in artifact_content
    assert "Task Run Artifact" in artifact_content
    assert "Workflow Pattern" in artifact_content
    assert "Per-Step Summary" in artifact_content
    assert "Key Files Considered" in artifact_content
    assert "Structured Result Sections" in artifact_content
    assert "Open Questions" in artifact_content
    assert "Suggested Next Steps" in artifact_content
    assert "Provenance / Evidence" in artifact_content
    assert "Generated At" in artifact_content
    summary = build_operator_state_summary(tmp_path)
    assert summary.get("last_task_run")
    assert summary["last_task_run"]["artifact_path"] == result["artifact_path"]
    assert summary["last_task_run"].get("workflow_pattern") in WORKFLOW_PATTERNS
    assert summary["last_task_run"].get("step_count") == len(result["steps"])
    assert summary["last_task_plan_id"] == plan["plan_id"]
    assert summary["last_task_run_id"] == result["run_id"]
    tr = summary.get("task_runs") or {}
    assert tr.get("total_stored", 0) >= 1
    assert isinstance(tr.get("recent"), list)
    assert any(r.get("run_id") == result["run_id"] for r in (tr.get("recent") or []))


def test_list_recent_task_run_summaries_respects_limit(tmp_path: Path) -> None:
    for i in range(3):
        save_task_run(
            {
                "run_id": f"run_test_{i}",
                "status": "completed",
                "reason": "",
                "workflow_pattern": "inspect_status_report",
                "plan_id": f"plan_{i}",
                "artifact_path": f"/tmp/a{i}.md",
                "completed_at": f"2026-03-19T0{i}:00:00Z",
                "created_at": f"2026-03-19T0{i}:00:00Z",
                "prompt": f"prompt {i}",
                "steps": [
                    {"step_index": 1, "step_id": "list_directory", "success": True, "step_status": "completed"},
                ],
            },
            repo_root=tmp_path,
        )
    recent = list_recent_task_run_summaries(tmp_path, limit=2)
    assert len(recent) == 2
    assert recent[0].get("completed_at", "") >= recent[1].get("completed_at", "")
    assert recent[0].get("steps_preview")
    assert recent[0]["steps_preview"][0].get("step_id") == "list_directory"


def test_compact_steps_preview_fallback_status() -> None:
    prev = compact_steps_preview(
        [
            {"step_index": 1, "step_id": "a", "success": True},
            {"step_index": 2, "step_id": "b", "success": False},
        ],
        max_steps=10,
    )
    assert prev[0]["step_status"] == "completed"
    assert prev[1]["step_status"] == "failed"


def test_run_persists_step_outcomes_with_index(tmp_path: Path) -> None:
    folder = tmp_path / "project"
    folder.mkdir()
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(folder), ["read", "write"])])
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Summarize project", repo_root=tmp_path)
    approve_task_plan(plan["plan_id"], repo_root=tmp_path)
    result = run_task_plan(plan["plan_id"], approved=True, repo_root=tmp_path)
    assert result["status"] == "completed"
    for i, step in enumerate(result["steps"], 1):
        assert step["step_index"] == i
        assert "completed_at" in step and step["completed_at"]
        assert "step_id" in step and "success" in step


def test_artifact_includes_workflow_and_per_step(tmp_path: Path) -> None:
    folder = tmp_path / "project"
    folder.mkdir()
    (folder / "notes.txt").write_text("Notes", encoding="utf-8")
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(folder), ["read", "write"])])
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Create a structured status report", repo_root=tmp_path)
    approve_task_plan(plan["plan_id"], repo_root=tmp_path)
    result = run_task_plan(plan["plan_id"], approved=True, repo_root=tmp_path)
    assert result["status"] == "completed"
    content = Path(result["artifact_path"]).read_text(encoding="utf-8")
    assert "Workflow Pattern" in content
    assert "inspect_status_report" in content
    assert "Per-Step Summary" in content
    assert "Key Files Considered" in content
    assert "Structured Result Sections" in content
    assert "list_directory:" in content
    assert "File list" in content
    assert "Validate the listed files" in content
    assert "Should future runs filter" in content


def test_plan_project_brief_pattern(tmp_path: Path) -> None:
    folder = tmp_path / "project"
    folder.mkdir()
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(folder), ["read", "write"])])
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Inspect project and create a project brief", repo_root=tmp_path)
    assert plan["status"] == "planned"
    assert plan["workflow_pattern"] == "inspect_project_brief"
    assert [s["step_id"] for s in plan["steps"]] == [
        "list_directory",
        "infer_project_context",
        "summarize_notes",
        "write_artifact",
    ]


def test_task_status_shows_step_and_pattern(tmp_path: Path) -> None:
    folder = tmp_path / "project"
    folder.mkdir()
    (folder / "README.md").write_text("Hello", encoding="utf-8")
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(folder), ["read", "write"])])
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Create a status report for project", repo_root=tmp_path)
    approve_task_plan(plan["plan_id"], repo_root=tmp_path)
    run = run_task_plan(plan["plan_id"], approved=True, repo_root=tmp_path)
    if "yaml" not in sys.modules:
        sys.modules["yaml"] = SimpleNamespace(
            safe_load=lambda *args, **kwargs: {},
            safe_dump=lambda *args, **kwargs: "",
        )
    try:
        from workflow_dataset.cli import app
    except Exception:
        pytest.skip("CLI dependencies unavailable in this test environment")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "local",
            "task-status",
            "--run-id",
            run["run_id"],
            "--repo-root",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert "workflow_pattern=inspect_status_report" in result.stdout
    assert "step_count=" in result.stdout
    assert "list_directory" in result.stdout


def test_run_finder_pattern_records_optional_step(tmp_path: Path, monkeypatch) -> None:
    folder = tmp_path / "project"
    folder.mkdir()
    (folder / "README.md").write_text("Hello", encoding="utf-8")
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(folder), ["read", "write"])])
    save_approval_registry(reg, tmp_path)

    plan = plan_task("Open folder in Finder and create report", repo_root=tmp_path)
    approve_task_plan(plan["plan_id"], repo_root=tmp_path)

    def _prov(adapter_id: str, action_id: str, path_or_param: str):
        return SimpleNamespace(
            adapter_id=adapter_id,
            action_id=action_id,
            path_or_param=path_or_param,
            outcome="ok",
        )

    def fake_run_execute(adapter_id, action_id, params, repo_root=None):  # noqa: ANN001
        if adapter_id == "file_ops" and action_id == "list_directory":
            return SimpleNamespace(
                success=True,
                message="ok",
                output={"entries": [{"name": "README.md", "is_file": True, "is_dir": False}]},
                provenance=[_prov(adapter_id, action_id, str(params.get("path") or ""))],
            )
        if adapter_id == "finder_open" and action_id == "open_folder":
            return SimpleNamespace(
                success=True,
                message="ok",
                output={"opened": True},
                provenance=[_prov(adapter_id, action_id, str(params.get("path") or ""))],
            )
        if adapter_id == "notes_document" and action_id == "summarize_text_for_workflow":
            return SimpleNamespace(
                success=True,
                message="ok",
                output={"summary": "summary"},
                provenance=[_prov(adapter_id, action_id, str(params.get("path") or ""))],
            )
        if adapter_id == "file_ops" and action_id == "write_file":
            return SimpleNamespace(
                success=True,
                message="ok",
                output={"bytes_written": len(str(params.get("content") or ""))},
                provenance=[_prov(adapter_id, action_id, str(params.get("path") or ""))],
            )
        return SimpleNamespace(success=False, message="unsupported", output={}, provenance=[])

    monkeypatch.setattr("workflow_dataset.local_operator.task_runs.run_execute", fake_run_execute)
    run = run_task_plan(plan["plan_id"], approved=True, repo_root=tmp_path)
    assert run["status"] == "completed"
    assert run["workflow_pattern"] == "inspect_finder_report"
    assert any(step["step_id"] == "open_finder" for step in run["steps"])
