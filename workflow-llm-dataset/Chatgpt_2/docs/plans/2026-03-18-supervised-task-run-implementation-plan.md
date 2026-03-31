# Supervised Task Run Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a supervised, bounded task-run flow to the local operator: prompt → plan → approve → execute → artifact → status.

**Architecture:** Implement a minimal task plan/run pipeline inside `local_operator` using existing approval registry + desktop adapters. Plans/runs persist under `data/local/operator/`, and the operator state tracks only the latest plan/run summary for snapshot surfaces.

**Tech Stack:** Python 3, Typer CLI, pytest, existing local_operator + desktop_adapters modules.

---

### Task 1: Add task plan/run storage helpers

**Files:**
- Create: `src/workflow_dataset/local_operator/task_store.py`
- Test: `tests/test_local_operator_task_run.py`

**Step 1: Write the failing tests (storage roundtrip)**

```python
from pathlib import Path

from workflow_dataset.local_operator.task_store import (
    save_task_plan,
    load_task_plan,
    list_task_plans,
    save_task_run,
    load_task_run,
    list_task_runs,
)


def test_task_plan_store_roundtrip(tmp_path: Path) -> None:
    plan = {"plan_id": "plan-1", "prompt": "Summarize folder", "status": "planned"}
    save_task_plan(plan, tmp_path)
    loaded = load_task_plan("plan-1", tmp_path)
    assert loaded is not None
    assert loaded["prompt"] == "Summarize folder"
    assert "plan-1" in list_task_plans(tmp_path)


def test_task_run_store_roundtrip(tmp_path: Path) -> None:
    run = {"run_id": "run-1", "plan_id": "plan-1", "status": "completed"}
    save_task_run(run, tmp_path)
    loaded = load_task_run("run-1", tmp_path)
    assert loaded is not None
    assert loaded["status"] == "completed"
    assert "run-1" in list_task_runs(tmp_path)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_local_operator_task_run.py::test_task_plan_store_roundtrip -v`  
Expected: FAIL with import errors (task_store missing).

**Step 3: Write minimal implementation**

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TASK_PLANS_DIR = Path("data/local/operator/task_plans")
TASK_RUNS_DIR = Path("data/local/operator/task_runs")


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _ensure_dir(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_task_plans_dir(repo_root: Path | str | None = None) -> Path:
    return _ensure_dir(_repo_root(repo_root) / TASK_PLANS_DIR)


def get_task_runs_dir(repo_root: Path | str | None = None) -> Path:
    return _ensure_dir(_repo_root(repo_root) / TASK_RUNS_DIR)


def _plan_path(plan_id: str, repo_root: Path | str | None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in plan_id.strip())
    return get_task_plans_dir(repo_root) / f"{safe}.json"


def _run_path(run_id: str, repo_root: Path | str | None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in run_id.strip())
    return get_task_runs_dir(repo_root) / f"{safe}.json"


def list_task_plans(repo_root: Path | str | None = None) -> list[str]:
    return sorted([p.stem for p in get_task_plans_dir(repo_root).glob("*.json")])


def list_task_runs(repo_root: Path | str | None = None) -> list[str]:
    return sorted([p.stem for p in get_task_runs_dir(repo_root).glob("*.json")])


def save_task_plan(plan: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    path = _plan_path(str(plan.get("plan_id", "plan")), repo_root)
    path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return path


def load_task_plan(plan_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    path = _plan_path(plan_id, repo_root)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_task_run(run: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    path = _run_path(str(run.get("run_id", "run")), repo_root)
    path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    return path


def load_task_run(run_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    path = _run_path(run_id, repo_root)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_local_operator_task_run.py::test_task_plan_store_roundtrip -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/workflow_dataset/local_operator/task_store.py tests/test_local_operator_task_run.py
git commit -m "feat: add task plan/run storage helpers"
```

---

### Task 2: Add prompt → plan generation

**Files:**
- Create: `src/workflow_dataset/local_operator/task_planning.py`
- Modify: `tests/test_local_operator_task_run.py`

**Step 1: Write the failing tests (prompt -> plan + unsupported)**

```python
from workflow_dataset.capability_discovery.approval_registry import ApprovalRegistry, save_approval_registry
from workflow_dataset.local_operator.task_planning import plan_task


def _approved_path(path: str, ops: list[str]) -> dict:
    return {
        "path": path,
        "allowed_operations": ops,
        "recursive": True,
        "inherit_mode": "inherit",
        "sensitivity_tag": "unspecified",
        "approval_source": "explicit_user",
        "revocation_state": "active",
        "approved_at": "",
        "reviewed_at": "",
        "expires_at": "",
    }


def test_plan_task_selects_matching_folder(tmp_path: Path) -> None:
    alpha = tmp_path / "alpha-project"
    beta = tmp_path / "beta-project"
    alpha.mkdir()
    beta.mkdir()
    reg = ApprovalRegistry(
        approved_paths=[_approved_path(str(alpha), ["read", "write"]), _approved_path(str(beta), ["read", "write"])]
    )
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Summarize beta project", repo_root=tmp_path)
    assert plan["status"] == "planned"
    assert plan["approved_scope"]["path"] == str(beta)


def test_plan_task_unsupported_without_approved_paths(tmp_path: Path) -> None:
    plan = plan_task("Summarize folder", repo_root=tmp_path)
    assert plan["status"] == "unsupported"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_local_operator_task_run.py::test_plan_task_selects_matching_folder -v`  
Expected: FAIL with import errors.

**Step 3: Write minimal implementation**

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.local_operator.approved_folders import list_approved_folders
from workflow_dataset.local_operator.task_store import save_task_plan
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _choose_scope(prompt: str, entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not entries:
        return None
    prompt_l = prompt.lower()
    for e in entries:
        path = str(e.get("path") or "")
        name = Path(path).name.lower()
        if name and name in prompt_l:
            return e
        if path and path.lower() in prompt_l:
            return e
    return entries[0]


def plan_task(prompt: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    entries = [e for e in list_approved_folders(repo_root) if e.get("revocation_state") == "active"]
    ts = utc_now_iso()
    scope = _choose_scope(prompt, entries)
    plan_id = stable_id("plan", prompt, ts, prefix="plan")
    if not scope:
        plan = {
            "plan_id": plan_id,
            "prompt": prompt,
            "status": "unsupported",
            "reason": "no_approved_folders",
            "approved": False,
            "created_at": ts,
            "approved_scope": {},
            "steps": [],
        }
        save_task_plan(plan, repo_root)
        return plan
    path = str(scope.get("path") or "")
    plan = {
        "plan_id": plan_id,
        "prompt": prompt,
        "status": "planned",
        "reason": "",
        "approved": False,
        "created_at": ts,
        "approved_scope": {"path": path},
        "steps": [
            {
                "step_id": "list_directory",
                "adapter_id": "file_ops",
                "action_id": "list_directory",
                "params": {"path": path},
            },
            {
                "step_id": "summarize_notes",
                "adapter_id": "notes_document",
                "action_id": "summarize_text_for_workflow",
                "params": {"path": "<auto>"},
                "optional": True,
            },
            {
                "step_id": "write_artifact",
                "adapter_id": "file_ops",
                "action_id": "write_file",
                "params": {"path": "<auto>", "content": "<auto>"},
            },
        ],
    }
    save_task_plan(plan, repo_root)
    return plan
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_local_operator_task_run.py::test_plan_task_selects_matching_folder -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/workflow_dataset/local_operator/task_planning.py tests/test_local_operator_task_run.py
git commit -m "feat: add prompt-based task planning"
```

---

### Task 3: Enable real file write + approval enforcement

**Files:**
- Modify: `src/workflow_dataset/desktop_adapters/file_runner.py`
- Modify: `src/workflow_dataset/desktop_adapters/execute.py`
- Modify: `src/workflow_dataset/desktop_adapters/contracts.py`
- Modify: `src/workflow_dataset/capability_discovery/approval_check.py`

**Step 1: Write failing tests (artifact generation requires write)**

```python
from workflow_dataset.local_operator.task_planning import plan_task
from workflow_dataset.local_operator.task_runs import approve_task_plan, run_task_plan


def test_run_task_creates_artifact(tmp_path: Path) -> None:
    folder = tmp_path / "project"
    folder.mkdir()
    (folder / "README.md").write_text("Hello world")
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(folder), ["read", "write"])])
    save_approval_registry(reg, tmp_path)

    plan = plan_task("Summarize project", repo_root=tmp_path)
    approve_task_plan(plan["plan_id"], repo_root=tmp_path)
    result = run_task_plan(plan["plan_id"], approved=True, repo_root=tmp_path)
    assert result["status"] == "completed"
    assert Path(result["artifact_path"]).exists()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_local_operator_task_run.py::test_run_task_creates_artifact -v`  
Expected: FAIL (write_file not implemented for real execution).

**Step 3: Write minimal implementation**

```python
def run_write_file(path: str | Path, content: str) -> InspectResult:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return InspectResult(exists=True, is_file=True, is_dir=False)
```

```python
if action_id == "write_file":
    content = params.get("content", "")
    res = run_write_file(path, content)
    if res.error:
        return ExecuteResult(...)
    return ExecuteResult(success=True, ...)
```

```python
ActionSpec("write_file", "Write content to file", [...], ["path"], True, True)
```

```python
path_using_actions = { ..., "write_file" }
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_local_operator_task_run.py::test_run_task_creates_artifact -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/workflow_dataset/desktop_adapters/file_runner.py \
        src/workflow_dataset/desktop_adapters/execute.py \
        src/workflow_dataset/desktop_adapters/contracts.py \
        src/workflow_dataset/capability_discovery/approval_check.py \
        tests/test_local_operator_task_run.py
git commit -m "feat: allow approved write_file execution"
```

---

### Task 4: Implement task runs + artifact generation

**Files:**
- Create: `src/workflow_dataset/local_operator/task_runs.py`
- Modify: `src/workflow_dataset/local_operator/state_store.py`
- Modify: `tests/test_local_operator_task_run.py`

**Step 1: Write failing tests (approval gating + run status)**

```python
from workflow_dataset.local_operator.task_runs import approve_task_plan, run_task_plan


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
    (folder / "README.md").write_text("Hello world")
    reg = ApprovalRegistry(approved_paths=[_approved_path(str(folder), ["read", "write"])])
    save_approval_registry(reg, tmp_path)
    plan = plan_task("Summarize project", repo_root=tmp_path)
    approve_task_plan(plan["plan_id"], repo_root=tmp_path)
    result = run_task_plan(plan["plan_id"], approved=True, repo_root=tmp_path)
    assert result["status"] == "completed"
    from workflow_dataset.local_operator.summary import build_operator_state_summary
    summary = build_operator_state_summary(tmp_path)
    assert summary.get("last_task_run")
    assert summary["last_task_run"]["artifact_path"] == result["artifact_path"]
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_local_operator_task_run.py::test_run_requires_approval -v`  
Expected: FAIL (task_runs missing).

**Step 3: Write minimal implementation**

```python
def approve_task_plan(plan_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    plan = load_task_plan(plan_id, repo_root)
    if not plan:
        return {"error": "plan_not_found"}
    plan["approved"] = True
    plan["approved_at"] = utc_now_iso()
    save_task_plan(plan, repo_root)
    return plan


def run_task_plan(plan_id: str, *, approved: bool, repo_root: Path | str | None = None) -> dict[str, Any]:
    # enforce approved flag + plan approval
    # run list_directory, optional summarize, write artifact
    # update operator state last_task_run
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_local_operator_task_run.py::test_run_requires_approval -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/workflow_dataset/local_operator/task_runs.py \
        src/workflow_dataset/local_operator/state_store.py \
        tests/test_local_operator_task_run.py
git commit -m "feat: add supervised task run execution"
```

---

### Task 5: Add CLI command surface

**Files:**
- Modify: `src/workflow_dataset/cli.py`

**Step 1: Write a minimal manual test script**

```
workflow-dataset local plan-task --prompt "Summarize the approved folder"
workflow-dataset local approve-task --plan-id <id>
workflow-dataset local run-task --plan-id <id> --approved
workflow-dataset local task-status --run-id <id>
```

**Step 2: Implement commands**

```python
@local_group.command("plan-task")
def local_plan_task(...):
    ...

@local_group.command("approve-task")
def local_approve_task(...):
    ...

@local_group.command("run-task")
def local_run_task(...):
    ...

@local_group.command("task-status")
def local_task_status(...):
    ...
```

**Step 3: Manual smoke**

Run: commands above  
Expected: plan id printed, approval recorded, run completes with artifact path.

**Step 4: Commit**

```bash
git add src/workflow_dataset/cli.py
git commit -m "feat: add local task-run CLI commands"
```

---

### Task 6: Snapshot/summary shaping

**Files:**
- Modify: `src/workflow_dataset/local_operator/summary.py`
- Modify: `tests/test_local_operator_task_run.py`

**Step 1: Add failing test**

```python
def test_summary_includes_last_task_run(tmp_path: Path) -> None:
    summary = build_operator_state_summary(tmp_path)
    assert "last_task_run" in summary
```

**Step 2: Implement**

```python
"last_task_run": state.get("last_task_run"),
```

**Step 3: Run tests**

Run: `pytest tests/test_local_operator_task_run.py::test_summary_includes_last_task_run -v`  
Expected: PASS

**Step 4: Commit**

```bash
git add src/workflow_dataset/local_operator/summary.py tests/test_local_operator_task_run.py
git commit -m "feat: expose latest task run in summary"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-03-18-supervised-task-run-implementation-plan.md`.

Two execution options:

1. **Subagent-Driven (this session)** — I dispatch a fresh subagent per task, review between tasks.
2. **Parallel Session (separate)** — Open a new session with `superpowers:executing-plans` and follow the plan sequentially.

Which approach?
