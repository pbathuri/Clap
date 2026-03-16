"""
M23E-F1: Persist task definitions locally. data/local/task_demonstrations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

from workflow_dataset.task_demos.models import TaskDefinition, TaskStep


TASKS_DIR = Path("data/local/task_demonstrations")


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_tasks_dir(repo_root: Path | str | None = None) -> Path:
    """Return task demonstrations directory; ensure it exists."""
    root = _repo_root(repo_root)
    path = root / TASKS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _task_path(task_id: str, repo_root: Path | str | None) -> Path:
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in task_id.strip())
    return get_tasks_dir(repo_root) / f"{safe_id}.yaml"


def _step_to_dict(s: TaskStep) -> dict[str, Any]:
    d: dict[str, Any] = {"adapter_id": s.adapter_id, "action_id": s.action_id, "params": dict(s.params)}
    if s.notes:
        d["notes"] = s.notes
    return d


def _dict_to_step(d: dict[str, Any]) -> TaskStep:
    return TaskStep(
        adapter_id=str(d.get("adapter_id", "")),
        action_id=str(d.get("action_id", "")),
        params=dict(d.get("params") or {}),
        notes=str(d.get("notes") or ""),
    )


def list_tasks(repo_root: Path | str | None = None) -> list[str]:
    """List task ids (from filenames without .yaml)."""
    dir_path = get_tasks_dir(repo_root)
    ids = []
    for f in dir_path.iterdir():
        if f.suffix in (".yaml", ".yml") and f.stem:
            ids.append(f.stem)
    return sorted(ids)


def get_task(task_id: str, repo_root: Path | str | None = None) -> TaskDefinition | None:
    """Load task by id. Returns None if not found."""
    path = _task_path(task_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    if yaml is None:
        import json
        data = json.loads(raw)
    else:
        data = yaml.safe_load(raw) or {}
    steps = [_dict_to_step(s) for s in data.get("steps") or []]
    return TaskDefinition(
        task_id=str(data.get("task_id", task_id)),
        steps=steps,
        notes=str(data.get("notes") or ""),
    )


def save_task(task: TaskDefinition, repo_root: Path | str | None = None) -> Path:
    """Save task to data/local/task_demonstrations/<task_id>.yaml."""
    path = _task_path(task.task_id, repo_root)
    data = {
        "task_id": task.task_id,
        "notes": task.notes,
        "steps": [_step_to_dict(s) for s in task.steps],
    }
    if yaml is None:
        import json
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    else:
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    return path
