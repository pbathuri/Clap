"""
M27I–M27L: Persist prior plan, replan signals, progress state. data/local/progress/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.progress.models import ReplanSignal

PROGRESS_DIR = Path("data/local/progress")
PRIOR_PLANS_SUBDIR = "prior_plans"
SIGNALS_FILE = "replan_signals.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_progress_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / PROGRESS_DIR


def _prior_plan_path(project_id: str, repo_root: Path | str | None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (project_id or "default").strip())
    return get_progress_dir(repo_root) / PRIOR_PLANS_SUBDIR / f"{safe}.json"


def save_prior_plan(project_id: str, plan_dict: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    root = get_progress_dir(repo_root)
    (root / PRIOR_PLANS_SUBDIR).mkdir(parents=True, exist_ok=True)
    path = _prior_plan_path(project_id, repo_root)
    path.write_text(json.dumps(plan_dict, indent=2), encoding="utf-8")
    return path


def load_prior_plan(project_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    path = _prior_plan_path(project_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _signals_path(repo_root: Path | str | None) -> Path:
    return get_progress_dir(repo_root) / SIGNALS_FILE


def save_replan_signals(signals: list[ReplanSignal], repo_root: Path | str | None = None) -> Path:
    root = get_progress_dir(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = _signals_path(repo_root)
    data = {"signals": [s.to_dict() for s in signals], "updated": utc_now_iso()}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_replan_signals(repo_root: Path | str | None = None, limit: int = 100) -> list[ReplanSignal]:
    path = _signals_path(repo_root)
    if not path.exists() or not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        out = [ReplanSignal.from_dict(d) for d in data.get("signals", [])]
        return out[-limit:]
    except Exception:
        return []


def list_projects(repo_root: Path | str | None = None) -> list[str]:
    """List project ids: from prior_plans dir plus 'default'."""
    root = get_progress_dir(repo_root) / PRIOR_PLANS_SUBDIR
    if not root.exists():
        return ["default"]
    out = []
    for f in root.iterdir():
        if f.is_file() and f.suffix == ".json":
            out.append(f.stem)
    return sorted(set(out)) if out else ["default"]
