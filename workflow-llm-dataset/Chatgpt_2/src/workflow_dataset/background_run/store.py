"""
M34E–M34H: Persist background queue, runs, and history. Local only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.background_run.models import (
    BackgroundRun,
    QueuedRecurringJob,
    RetryPolicy,
)

ROOT_DIR = "data/local/background_run"
QUEUE_FILE = "queue.json"
HISTORY_FILE = "history.json"
RETRY_POLICIES_FILE = "retry_policies.json"
RUNS_SUBDIR = "runs"
RUN_STATE_FILE = "run_state.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_background_root(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / ROOT_DIR


def get_runs_dir(repo_root: Path | str | None = None) -> Path:
    p = get_background_root(repo_root) / RUNS_SUBDIR
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_queue(repo_root: Path | str | None = None) -> list[QueuedRecurringJob]:
    path = get_background_root(repo_root) / QUEUE_FILE
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [QueuedRecurringJob.from_dict(d) for d in raw.get("jobs", [])]
    except Exception:
        return []


def save_queue(jobs: list[QueuedRecurringJob], repo_root: Path | str | None = None) -> Path:
    root = get_background_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / QUEUE_FILE
    path.write_text(
        json.dumps({"jobs": [j.to_dict() for j in jobs]}, indent=2),
        encoding="utf-8",
    )
    return path


def save_run(run: BackgroundRun, repo_root: Path | str | None = None) -> Path:
    root = get_runs_dir(repo_root)
    run_dir = root / run.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run.run_path = str(run_dir)
    path = run_dir / RUN_STATE_FILE
    path.write_text(json.dumps(run.to_dict(), indent=2), encoding="utf-8")
    return path


def load_run(run_id: str, repo_root: Path | str | None = None) -> BackgroundRun | None:
    path = get_runs_dir(repo_root) / run_id / RUN_STATE_FILE
    if not path.exists():
        return None
    try:
        return BackgroundRun.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def list_runs(
    limit: int = 50,
    status_filter: str | None = None,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    root = get_runs_dir(repo_root)
    if not root.exists():
        return []
    out: list[dict[str, Any]] = []
    for d in sorted(root.iterdir(), key=lambda x: x.stat().st_mtime if x.is_dir() else 0, reverse=True):
        if not d.is_dir():
            continue
        f = d / RUN_STATE_FILE
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if status_filter and data.get("status") != status_filter:
                continue
            out.append({
                "run_id": data.get("run_id", d.name),
                "automation_id": data.get("automation_id", ""),
                "status": data.get("status", ""),
                "plan_ref": data.get("plan_ref", ""),
                "execution_mode": data.get("execution_mode", ""),
                "timestamp_start": data.get("timestamp_start", ""),
                "timestamp_end": data.get("timestamp_end", ""),
                "outcome_summary": data.get("outcome_summary", ""),
            })
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out


def append_history_entry(entry: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    root = get_background_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / HISTORY_FILE
    entries: list[dict[str, Any]] = []
    if path.exists():
        try:
            entries = json.loads(path.read_text(encoding="utf-8")).get("entries", [])
        except Exception:
            pass
    entries.insert(0, entry)
    path.write_text(json.dumps({"entries": entries[:500]}, indent=2), encoding="utf-8")
    return path


def load_history(limit: int = 50, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    path = get_background_root(repo_root) / HISTORY_FILE
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("entries", [])[:limit]
    except Exception:
        return []


def load_retry_policies(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Load retry policies: { default: RetryPolicy, by_automation: { automation_id: RetryPolicy } }."""
    path = get_background_root(repo_root) / RETRY_POLICIES_FILE
    if not path.exists():
        return {"default": None, "by_automation": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        default = raw.get("default")
        out: dict[str, Any] = {
            "default": RetryPolicy.from_dict(default) if isinstance(default, dict) else None,
            "by_automation": {},
        }
        for aid, p in (raw.get("by_automation") or {}).items():
            if isinstance(p, dict):
                out["by_automation"][aid] = RetryPolicy.from_dict(p)
        return out
    except Exception:
        return {"default": None, "by_automation": {}}


def save_retry_policies(
    default: RetryPolicy | None = None,
    by_automation: dict[str, RetryPolicy] | None = None,
    repo_root: Path | str | None = None,
) -> Path:
    """Save retry policies."""
    root = get_background_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / RETRY_POLICIES_FILE
    payload = {
        "default": default.to_dict() if default else None,
        "by_automation": {aid: p.to_dict() for aid, p in (by_automation or {}).items()},
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
