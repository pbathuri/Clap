"""
Task plan and task run storage for local operator workflows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TASK_PLANS_DIR = Path("data/local/operator/task_plans")
TASK_RUNS_DIR = Path("data/local/operator/task_runs")


def compact_steps_preview(steps: Any, *, max_steps: int = 12) -> list[dict[str, Any]]:
    """Compact timeline for summaries / state (step id + status only)."""
    if not isinstance(steps, list):
        return []
    out: list[dict[str, Any]] = []
    for s in steps[: max(1, int(max_steps))]:
        if not isinstance(s, dict):
            continue
        success = s.get("success")
        out.append(
            {
                "step_index": s.get("step_index"),
                "step_id": s.get("step_id"),
                "step_status": s.get("step_status") or ("completed" if success else "failed"),
                "success": success,
            }
        )
    return out


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_id(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in (value or "").strip())


def _require_id(raw_id: str, label: str) -> str:
    safe_id = _safe_id(raw_id)
    if not safe_id:
        raise ValueError(f"{label} must be a non-empty string")
    return safe_id


def get_task_plans_dir(repo_root: Path | str | None = None) -> Path:
    return _ensure_dir(_repo_root(repo_root) / TASK_PLANS_DIR)


def get_task_runs_dir(repo_root: Path | str | None = None) -> Path:
    return _ensure_dir(_repo_root(repo_root) / TASK_RUNS_DIR)


def _plan_path(plan_id: str, repo_root: Path | str | None) -> Path:
    safe_id = _require_id(plan_id, "plan_id")
    return get_task_plans_dir(repo_root) / f"{safe_id}.json"


def _run_path(run_id: str, repo_root: Path | str | None) -> Path:
    safe_id = _require_id(run_id, "run_id")
    return get_task_runs_dir(repo_root) / f"{safe_id}.json"


def list_task_plans(repo_root: Path | str | None = None) -> list[str]:
    root = get_task_plans_dir(repo_root)
    return sorted([item.stem for item in root.iterdir() if item.is_file() and item.suffix == ".json"])


def list_task_runs(repo_root: Path | str | None = None) -> list[str]:
    root = get_task_runs_dir(repo_root)
    return sorted([item.stem for item in root.iterdir() if item.is_file() and item.suffix == ".json"])


def list_recent_task_run_summaries(
    repo_root: Path | str | None = None,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Lightweight run history for summaries / shell: newest first by completed_at (fallback created_at).
    Reads a bounded window of newest files by mtime to avoid scanning huge stores.
    """
    root = get_task_runs_dir(repo_root)
    if not root.is_dir():
        return []
    cap = max(int(limit) * 4, 40)
    paths = sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:cap]
    summaries: list[dict[str, Any]] = []
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rid = str(data.get("run_id") or path.stem).strip()
        steps = data.get("steps") or []
        summaries.append(
            {
                "run_id": rid,
                "status": data.get("status"),
                "reason": data.get("reason"),
                "workflow_pattern": data.get("workflow_pattern") or "",
                "plan_id": data.get("plan_id"),
                "artifact_path": data.get("artifact_path") or "",
                "completed_at": data.get("completed_at") or "",
                "created_at": data.get("created_at") or "",
                "prompt_preview": (str(data.get("prompt") or ""))[:160],
                "step_count": len(steps) if isinstance(steps, list) else 0,
                "steps_preview": compact_steps_preview(steps, max_steps=8),
            }
        )
    summaries.sort(
        key=lambda x: (x.get("completed_at") or x.get("created_at") or ""),
        reverse=True,
    )
    return summaries[: max(1, int(limit))]


def save_task_plan(plan: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    plan_id = str(plan.get("plan_id", "")).strip()
    path = _plan_path(plan_id, repo_root)
    path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return path


def load_task_plan(plan_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    path = _plan_path(plan_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def save_task_run(run: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    run_id = str(run.get("run_id", "")).strip()
    path = _run_path(run_id, repo_root)
    path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    return path


def load_task_run(run_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    path = _run_path(run_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
