"""
M48I–M48L: Persist governed scopes, delegation state, suspension/revocation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.governed_operator.models import (
    DelegatedScope,
    DelegationSafeLoop,
    GovernedOperatorStatus,
)

GOVERNED_OPERATOR_DIR = Path("data/local/governed_operator")
SCOPES_SUBDIR = "scopes"
LOOPS_SUBDIR = "loops"
STATE_FILE = "state.json"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _base_dir(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / GOVERNED_OPERATOR_DIR


def _scopes_dir(repo_root: Path | str | None) -> Path:
    return _base_dir(repo_root) / SCOPES_SUBDIR


def _loops_dir(repo_root: Path | str | None) -> Path:
    return _base_dir(repo_root) / LOOPS_SUBDIR


# ----- Delegated scopes -----


def list_scope_ids(repo_root: Path | str | None = None) -> list[str]:
    d = _scopes_dir(repo_root)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json") if p.stem and not p.stem.startswith("."))


def get_scope(scope_id: str, repo_root: Path | str | None = None) -> DelegatedScope | None:
    path = _scopes_dir(repo_root) / f"{scope_id}.json"
    if not path.exists():
        return None
    try:
        return DelegatedScope(**json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def save_scope(scope: DelegatedScope, repo_root: Path | str | None = None) -> Path:
    d = _scopes_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{scope.scope_id or 'scope'}.json"
    path.write_text(json.dumps(scope.to_dict(), indent=2), encoding="utf-8")
    return path


# ----- Delegation-safe loops -----


def list_loop_ids(repo_root: Path | str | None = None) -> list[str]:
    d = _loops_dir(repo_root)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json") if p.stem and not p.stem.startswith("."))


def get_loop(loop_id: str, repo_root: Path | str | None = None) -> DelegationSafeLoop | None:
    path = _loops_dir(repo_root) / f"{loop_id}.json"
    if not path.exists():
        return None
    try:
        return DelegationSafeLoop(**json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def save_loop(loop: DelegationSafeLoop, repo_root: Path | str | None = None) -> Path:
    d = _loops_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{loop.loop_id or 'loop'}.json"
    path.write_text(json.dumps(loop.to_dict(), indent=2), encoding="utf-8")
    return path


# ----- Governed state (suspended/revoked scope ids) -----


def load_governed_state(repo_root: Path | str | None = None) -> dict[str, Any]:
    path = _base_dir(repo_root) / STATE_FILE
    if not path.exists():
        return {
            "suspended_scope_ids": [],
            "revoked_scope_ids": [],
            "reauthorization_needed_scope_ids": [],
            "updated_utc": "",
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "suspended_scope_ids": [],
            "revoked_scope_ids": [],
            "reauthorization_needed_scope_ids": [],
            "updated_utc": "",
        }


def save_governed_state(state: dict[str, Any], repo_root: Path | str | None = None) -> Path:
    _base_dir(repo_root).mkdir(parents=True, exist_ok=True)
    path = _base_dir(repo_root) / STATE_FILE
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return path
