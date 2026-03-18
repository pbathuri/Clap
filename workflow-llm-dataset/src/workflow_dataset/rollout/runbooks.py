"""
M24I.1: Operator runbooks — list and resolve runbook docs for rollout/recovery/escalation.
Runbooks live under docs/rollout/ (repo-relative). No cloud; read-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

RUNBOOKS_DIR = "docs/rollout"
RUNBOOK_FILES = {
    "operator_runbooks": "OPERATOR_RUNBOOKS.md",
    "recovery_escalation": "RECOVERY_ESCALATION.md",
}


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_runbooks_dir(repo_root: Path | str | None = None) -> Path:
    """Return path to docs/rollout (runbooks directory)."""
    return _repo_root(repo_root) / RUNBOOKS_DIR


def list_runbooks() -> list[str]:
    """Return list of runbook IDs (e.g. operator_runbooks, recovery_escalation)."""
    return list(RUNBOOK_FILES.keys())


def get_runbook_path(runbook_id: str, repo_root: Path | str | None = None) -> Path | None:
    """Return path to runbook file for runbook_id, or None if not found."""
    fname = RUNBOOK_FILES.get(runbook_id)
    if not fname:
        return None
    path = get_runbooks_dir(repo_root) / fname
    return path if path.exists() else None


def get_runbook_content(runbook_id: str, repo_root: Path | str | None = None) -> str | None:
    """Return runbook file content as string, or None if not found."""
    path = get_runbook_path(runbook_id, repo_root)
    if not path:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def get_runbook_info(runbook_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Return {id, path, exists, content_preview} for runbook_id."""
    path = get_runbook_path(runbook_id, repo_root)
    exists = path is not None and path.exists()
    content = get_runbook_content(runbook_id, repo_root) if exists else None
    preview = (content[:500] + "…") if content and len(content) > 500 else (content or "")
    return {
        "id": runbook_id,
        "path": str(path) if path else None,
        "exists": exists,
        "content_preview": preview,
    }
