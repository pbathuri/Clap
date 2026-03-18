"""
M28: Portfolio store — optional priority hints and defer/revisit state. Local JSON.
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

from workflow_dataset.portfolio.models import (
    DeferRevisitState,
    AttentionBudget,
    WorkWindow,
    FocusMode,
)

PORTFOLIO_DIR = "data/local/portfolio"
META_FILE = "portfolio_meta.json"
ATTENTION_CONFIG_FILE = "attention_config.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_portfolio_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / PORTFOLIO_DIR


def _meta_path(repo_root: Path | str | None) -> Path:
    return get_portfolio_dir(repo_root) / META_FILE


def load_priority_hints(repo_root: Path | str | None = None) -> dict[str, str]:
    """Load operator priority hints by project_id: high | medium | low. Default {}."""
    path = _meta_path(repo_root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return dict(data.get("priority_hints", {}))
    except Exception:
        return {}


def save_priority_hints(hints: dict[str, str], repo_root: Path | str | None = None) -> Path:
    """Save priority hints. Merges with existing meta."""
    path = _meta_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"priority_hints": hints, "updated_at": utc_now_iso()}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            data["priority_hints"] = {**existing.get("priority_hints", {}), **hints}
        except Exception:
            pass
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_defer_revisit(repo_root: Path | str | None = None) -> list[DeferRevisitState]:
    """Load active defer/revisit states for projects."""
    path = _meta_path(repo_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data.get("defer_revisit", [])
        return [DeferRevisitState.from_dict(d) for d in raw if d.get("active", True)]
    except Exception:
        return []


def save_defer_revisit(states: list[DeferRevisitState], repo_root: Path | str | None = None) -> Path:
    """Save defer/revisit states (replaces list)."""
    path = _meta_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    data["defer_revisit"] = [s.to_dict() for s in states]
    data["updated_at"] = utc_now_iso()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def get_deferred_project_ids(repo_root: Path | str | None = None) -> set[str]:
    """Set of project_ids currently deferred (for scheduler to filter or down-rank)."""
    return {d.project_id for d in load_defer_revisit(repo_root)}


# ----- M28D.1 Attention budgets + work windows -----


def _attention_config_path(repo_root: Path | str | None) -> Path:
    return get_portfolio_dir(repo_root) / ATTENTION_CONFIG_FILE


def load_attention_budgets(repo_root: Path | str | None = None) -> list[AttentionBudget]:
    """Load attention budgets from attention_config.json."""
    path = _attention_config_path(repo_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data.get("attention_budgets", [])
        return [AttentionBudget.from_dict(d) for d in raw]
    except Exception:
        return []


def load_work_windows(repo_root: Path | str | None = None) -> list[WorkWindow]:
    """Load work windows from attention_config.json."""
    path = _attention_config_path(repo_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data.get("work_windows", [])
        return [WorkWindow.from_dict(d) for d in raw]
    except Exception:
        return []


def load_focus_modes(repo_root: Path | str | None = None) -> list[FocusMode]:
    """Load focus modes from attention_config.json."""
    path = _attention_config_path(repo_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data.get("focus_modes", [])
        return [FocusMode.from_dict(d) for d in raw if d.get("active", True)]
    except Exception:
        return []


def load_attention_config(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Load full attention config (budgets, work_windows, focus_modes, active_focus_mode_id, current_window_started_at)."""
    path = _attention_config_path(repo_root)
    if not path.exists():
        return {
            "attention_budgets": [],
            "work_windows": [],
            "focus_modes": [],
            "active_focus_mode_id": "",
            "current_window_started_at_iso": "",
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "attention_budgets": data.get("attention_budgets", []),
            "work_windows": data.get("work_windows", []),
            "focus_modes": data.get("focus_modes", []),
            "active_focus_mode_id": str(data.get("active_focus_mode_id", "")),
            "current_window_started_at_iso": str(data.get("current_window_started_at_iso", "")),
        }
    except Exception:
        return {
            "attention_budgets": [],
            "work_windows": [],
            "focus_modes": [],
            "active_focus_mode_id": "",
            "current_window_started_at_iso": "",
        }


def save_attention_config(
    attention_budgets: list[AttentionBudget] | None = None,
    work_windows: list[WorkWindow] | None = None,
    focus_modes: list[FocusMode] | None = None,
    active_focus_mode_id: str | None = None,
    current_window_started_at_iso: str | None = None,
    repo_root: Path | str | None = None,
) -> Path:
    """Save attention config. Merges with existing; pass None for a section to keep existing."""
    path = _attention_config_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    if attention_budgets is not None:
        existing["attention_budgets"] = [b.to_dict() for b in attention_budgets]
    if work_windows is not None:
        existing["work_windows"] = [w.to_dict() for w in work_windows]
    if focus_modes is not None:
        existing["focus_modes"] = [f.to_dict() for f in focus_modes]
    if active_focus_mode_id is not None:
        existing["active_focus_mode_id"] = active_focus_mode_id
    if current_window_started_at_iso is not None:
        existing["current_window_started_at_iso"] = current_window_started_at_iso
    existing["updated_at"] = utc_now_iso()
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return path
