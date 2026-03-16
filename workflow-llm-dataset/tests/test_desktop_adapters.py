"""M23C-F1/F2/F3: Desktop action adapters — contracts, registry, simulate, execute. F3: browser/app simulate + URL validation + app allowlist."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.desktop_adapters import (
    list_adapters,
    get_adapter,
    check_availability,
    run_simulate,
    run_execute,
    get_sandbox_root,
    validate_local_or_allowed_url,
    resolve_app_display_name,
    APPROVED_APP_NAMES,
    AdapterContract,
)
from workflow_dataset.desktop_adapters.file_runner import (
    run_inspect_path,
    run_list_directory,
    run_snapshot_to_sandbox,
)
from workflow_dataset.desktop_adapters.notes_runner import (
    run_read_text,
    run_summarize_text_for_workflow,
    run_propose_status_from_notes,
)


def test_list_adapters_at_least_four():
    items = list_adapters()
    assert len(items) >= 4
    ids = {a.adapter_id for a in items}
    assert "file_ops" in ids
    assert "notes_document" in ids
    assert "browser_open" in ids
    assert "app_launch" in ids


def test_get_adapter_file_ops():
    a = get_adapter("file_ops")
    assert a is not None
    assert isinstance(a, AdapterContract)
    assert a.adapter_id == "file_ops"
    assert "read_file" in [x.action_id for x in a.supported_actions]


def test_get_adapter_browser_open():
    a = get_adapter("browser_open")
    assert a is not None
    assert a.adapter_id == "browser_open"
    assert any(x.action_id == "open_url" for x in a.supported_actions)


def test_get_adapter_unknown_returns_none():
    assert get_adapter("unknown_adapter_xyz") is None


def test_check_availability_file_ops():
    out = check_availability("file_ops")
    assert out["available"] is True
    assert out["adapter_id"] == "file_ops"
    assert out["supports_simulate"] is True
    # F2: file_ops supports real execution for inspect_path, list_directory, snapshot_to_sandbox
    assert out["supports_real_execution"] is True


def test_check_availability_unknown():
    out = check_availability("unknown_xyz")
    assert out["available"] is False
    assert "not found" in out.get("message", "").lower()


def test_run_simulate_browser_open_url_success():
    result = run_simulate("browser_open", "open_url", {"url": "https://example.com"})
    assert result.success is True
    assert result.adapter_id == "browser_open"
    assert result.action_id == "open_url"
    assert "Would open URL" in result.preview or "Simulate" in result.preview
    assert result.real_execution_supported is False


def test_run_simulate_file_ops_read_file():
    result = run_simulate("file_ops", "read_file", {"path": "/tmp/foo.txt"})
    assert result.success is True
    assert "Target path" in result.preview or "Simulate" in result.preview


def test_run_simulate_unknown_adapter_fails():
    result = run_simulate("unknown_adapter", "open_url", {})
    assert result.success is False
    assert "not found" in result.message.lower()


def test_run_simulate_unknown_action_fails():
    result = run_simulate("browser_open", "nonexistent_action", {})
    assert result.success is False
    assert "not found" in result.message.lower() or "Supported" in result.message


# ----- F2: file runner -----
def test_run_inspect_path_file(tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("hello")
    res = run_inspect_path(f)
    assert res.exists is True
    assert res.is_file is True
    assert res.is_dir is False
    assert res.size_bytes == 5
    assert res.error is None


def test_run_inspect_path_dir(tmp_path):
    (tmp_path / "sub").mkdir()
    res = run_inspect_path(tmp_path)
    assert res.exists is True
    assert res.is_dir is True
    assert res.is_file is False
    assert res.error is None


def test_run_inspect_path_missing():
    res = run_inspect_path("/nonexistent/path/xyz")
    assert res.exists is False
    assert res.error == "path_not_found"


def test_run_list_directory(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b").mkdir()
    res = run_list_directory(tmp_path)
    assert res.error is None
    names = {e["name"] for e in res.entries}
    assert "a.txt" in names
    assert "b" in names
    assert any(e["is_file"] for e in res.entries if e["name"] == "a.txt")
    assert any(e["is_dir"] for e in res.entries if e["name"] == "b")


def test_run_snapshot_to_sandbox_file(tmp_path):
    src = tmp_path / "orig"
    src.mkdir()
    (src / "f.txt").write_text("content")
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    res = run_snapshot_to_sandbox(src, sandbox, subdir="snap")
    assert res.error is None
    assert res.copied_count >= 1
    dest = sandbox / "snap" / "orig"
    assert dest.exists()
    assert (dest / "f.txt").read_text() == "content"
    # Original unchanged
    assert (src / "f.txt").read_text() == "content"


# ----- F2: notes runner -----
def test_run_read_text(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("line one\nline two")
    res = run_read_text(f)
    assert res.error is None
    assert "line one" in res.content
    assert "line two" in res.content


def test_run_summarize_text_for_workflow(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("first line\nsecond\nthird")
    res = run_summarize_text_for_workflow(f)
    assert res.error is None
    assert "Lines: 3" in res.summary or "3" in res.summary
    assert "first" in res.summary or "First" in res.summary


def test_run_propose_status_from_notes(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("Done: task A\nDone: task B\nNext: task C")
    res = run_propose_status_from_notes(f)
    assert res.error is None
    assert len(res.suggested_lines) >= 1
    assert any("task" in ln for ln in res.suggested_lines)


# ----- F2: run_execute -----
def test_run_execute_inspect_path(tmp_path):
    (tmp_path / "f.txt").write_text("x")
    result = run_execute("file_ops", "inspect_path", {"path": str(tmp_path / "f.txt")})
    assert result.success is True
    assert result.output.get("exists") is True
    assert result.output.get("is_file") is True
    assert len(result.provenance) == 1
    assert result.provenance[0].outcome == "ok"


def test_run_execute_list_directory(tmp_path):
    (tmp_path / "a").mkdir()
    result = run_execute("file_ops", "list_directory", {"path": str(tmp_path)})
    assert result.success is True
    assert "entries" in result.output
    assert any(e.get("name") == "a" for e in result.output["entries"])


def test_run_execute_snapshot_to_sandbox(tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "f.txt").write_text("data")
    sandbox = tmp_path / "sb"
    sandbox.mkdir()
    result = run_execute(
        "file_ops", "snapshot_to_sandbox",
        {"path": str(src)},
        sandbox_root=sandbox,
    )
    assert result.success is True
    assert result.output.get("copied_count") >= 1
    assert "sandbox_path" in result.output
    assert (Path(result.output["sandbox_path"]) / "f.txt").read_text() == "data"
    assert (src / "f.txt").read_text() == "data"


def test_run_execute_read_text(tmp_path):
    (tmp_path / "n.txt").write_text("hello notes")
    result = run_execute("notes_document", "read_text", {"path": str(tmp_path / "n.txt")})
    assert result.success is True
    assert result.output.get("content") == "hello notes"


def test_run_execute_propose_status_from_notes(tmp_path):
    (tmp_path / "n.txt").write_text("Completed X\nNext Y")
    result = run_execute("notes_document", "propose_status_from_notes", {"path": str(tmp_path / "n.txt")})
    assert result.success is True
    assert "suggested_lines" in result.output
    assert len(result.output["suggested_lines"]) >= 1


def test_run_execute_unknown_adapter():
    result = run_execute("unknown", "inspect_path", {"path": "/tmp"})
    assert result.success is False
    assert "not found" in result.message.lower()


def test_run_execute_unsupported_action():
    result = run_execute("browser_open", "open_url", {"url": "https://x.com"})
    assert result.success is False
    assert "not supported" in result.message.lower() or "not implemented" in result.message.lower()


# ----- M23H: Approval-gated execution -----
def test_run_execute_allowed_when_registry_missing(tmp_path):
    """When no approval registry file exists, execution is allowed (backward compatible)."""
    (tmp_path / "f.txt").write_text("x")
    result = run_execute(
        "file_ops", "inspect_path", {"path": str(tmp_path / "f.txt")}, repo_root=tmp_path
    )
    assert result.success is True


def test_run_execute_refused_when_action_not_in_approved_scopes(tmp_path):
    """When registry exists and approved_action_scopes is non-empty, action must be listed with executable=true."""
    from workflow_dataset.capability_discovery import save_approval_registry, ApprovalRegistry

    reg = ApprovalRegistry(
        approved_paths=[],
        approved_apps=[],
        approved_action_scopes=[
            {"adapter_id": "notes_document", "action_id": "read_text", "executable": True},
        ],
    )
    save_approval_registry(reg, tmp_path)
    (tmp_path / "f.txt").write_text("x")
    result = run_execute(
        "file_ops", "inspect_path", {"path": str(tmp_path / "f.txt")}, repo_root=tmp_path
    )
    assert result.success is False
    assert "approved_action_scopes" in result.message
    assert "not in" in result.message or "missing" in result.message.lower()


def test_run_execute_allowed_when_action_in_approved_scopes(tmp_path):
    """When action is in approved_action_scopes with executable=true, execution is allowed."""
    from workflow_dataset.capability_discovery import save_approval_registry, ApprovalRegistry

    reg = ApprovalRegistry(
        approved_paths=[],
        approved_apps=[],
        approved_action_scopes=[
            {"adapter_id": "notes_document", "action_id": "read_text", "executable": True},
        ],
    )
    save_approval_registry(reg, tmp_path)
    (tmp_path / "n.txt").write_text("hello")
    result = run_execute(
        "notes_document", "read_text", {"path": str(tmp_path / "n.txt")}, repo_root=tmp_path
    )
    assert result.success is True
    assert result.output.get("content") == "hello"


def test_run_execute_refused_when_path_not_in_approved_paths(tmp_path):
    """When approved_paths is non-empty, path-using actions must be under an approved path."""
    from workflow_dataset.capability_discovery import save_approval_registry, ApprovalRegistry

    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    (allowed_dir / "f.txt").write_text("ok")
    (other_dir / "f.txt").write_text("no")

    reg = ApprovalRegistry(
        approved_paths=[str(allowed_dir)],
        approved_apps=[],
        approved_action_scopes=[
            {"adapter_id": "file_ops", "action_id": "inspect_path", "executable": True},
        ],
    )
    save_approval_registry(reg, tmp_path)

    result_other = run_execute(
        "file_ops", "inspect_path", {"path": str(other_dir / "f.txt")}, repo_root=tmp_path
    )
    assert result_other.success is False
    assert "approved_paths" in result_other.message or "Path not in" in result_other.message

    result_allowed = run_execute(
        "file_ops", "inspect_path", {"path": str(allowed_dir / "f.txt")}, repo_root=tmp_path
    )
    assert result_allowed.success is True


# ----- F3: URL validation -----
def test_validate_url_http():
    v = validate_local_or_allowed_url("https://example.com")
    assert v.valid is True
    assert v.category in ("https", "http")


def test_validate_url_file():
    v = validate_local_or_allowed_url("file:///tmp/foo")
    assert v.valid is True
    assert v.category == "file"


def test_validate_url_localhost():
    v = validate_local_or_allowed_url("http://localhost:8080/path")
    assert v.valid is True
    assert v.category == "localhost"


def test_validate_url_invalid_scheme():
    v = validate_local_or_allowed_url("javascript:alert(1)")
    assert v.valid is False
    assert "scheme" in v.reason or "not_allowed" in v.reason


def test_validate_url_empty():
    v = validate_local_or_allowed_url("")
    assert v.valid is False


# ----- F3: app allowlist -----
def test_resolve_app_approved():
    assert resolve_app_display_name("Notes") == "Notes"
    assert resolve_app_display_name("notes") == "Notes"
    assert resolve_app_display_name("Terminal") == "Terminal"


def test_resolve_app_unapproved():
    assert resolve_app_display_name("RandomApp") is None
    assert resolve_app_display_name("/usr/bin/foo") is None


# ----- F3: simulate browser_open / app_launch -----
def test_simulate_open_url_valid():
    result = run_simulate("browser_open", "open_url", {"url": "https://example.com"})
    assert result.success is True
    assert "Validation: ok" in result.preview or "category=" in result.preview
    assert "simulate only" in result.preview.lower() or "Would open" in result.preview


def test_simulate_open_url_invalid():
    result = run_simulate("browser_open", "open_url", {"url": "javascript:void(0)"})
    assert result.success is True
    assert "invalid" in result.preview.lower()


def test_simulate_launch_app_approved():
    result = run_simulate("app_launch", "launch_app", {"app_name_or_path": "Safari"})
    assert result.success is True
    assert "Resolved (approved)" in result.preview
    assert "Safari" in result.preview
    assert "simulate only" in result.preview.lower()


def test_simulate_launch_app_unapproved():
    result = run_simulate("app_launch", "launch_app", {"app_name_or_path": "SomeUnknownApp"})
    assert result.success is True
    assert "not in approved list" in result.preview or "App:" in result.preview


# ----- F3: availability (simulate-only adapters) -----
def test_check_availability_browser_open():
    out = check_availability("browser_open")
    assert out["available"] is True
    assert out["supports_simulate"] is True
    assert out["supports_real_execution"] is False


def test_check_availability_app_launch():
    out = check_availability("app_launch")
    assert out["available"] is True
    assert out["supports_simulate"] is True
    assert out["supports_real_execution"] is False
