"""
M24D: Activation store — persist activation requests and execution history under data/local/activations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.external_capability.activation_models import ActivationRequest

ACTIVATIONS_DIR = "data/local/activations"
REQUESTS_SUBDIR = "requests"
HISTORY_FILENAME = "history.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _activations_root(repo_root: Path | str | None) -> Path:
    return _repo_root(repo_root) / ACTIVATIONS_DIR


def _requests_dir(repo_root: Path | str | None) -> Path:
    return _activations_root(repo_root) / REQUESTS_SUBDIR


def _activation_path(activation_id: str, repo_root: Path | str | None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in activation_id.strip())
    return _requests_dir(repo_root) / f"{safe}.json"


def _utc_now_iso() -> str:
    try:
        from workflow_dataset.utils.dates import utc_now_iso
        return utc_now_iso()
    except Exception:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


def save_request(request: ActivationRequest, repo_root: Path | str | None = None) -> Path:
    """Persist activation request. Returns path to saved file."""
    root = _repo_root(repo_root)
    _requests_dir(root).mkdir(parents=True, exist_ok=True)
    path = _activation_path(request.activation_id, root)
    request.updated_at = request.updated_at or _utc_now_iso()
    path.write_text(json.dumps(request.to_dict(), indent=2), encoding="utf-8")
    return path


def load_request(activation_id: str, repo_root: Path | str | None = None) -> ActivationRequest | None:
    """Load activation request by id. Returns None if not found."""
    path = _activation_path(activation_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ActivationRequest.from_dict(data)
    except Exception:
        return None


def list_requests(repo_root: Path | str | None = None, status: str | None = None) -> list[ActivationRequest]:
    """List all saved requests, optionally filtered by status."""
    req_dir = _requests_dir(repo_root)
    if not req_dir.exists() or not req_dir.is_dir():
        return []
    out: list[ActivationRequest] = []
    for path in sorted(req_dir.iterdir()):
        if not path.is_file() or path.suffix != ".json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            r = ActivationRequest.from_dict(data)
            if status is None or r.status == status:
                out.append(r)
        except Exception:
            continue
    return sorted(out, key=lambda x: (x.created_at or "", x.activation_id))


def _history_path(repo_root: Path | str | None) -> Path:
    return _activations_root(repo_root) / HISTORY_FILENAME


def _load_history_entries(repo_root: Path | str | None) -> list[dict[str, Any]]:
    path = _history_path(repo_root)
    if not path.exists() or not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("entries", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    except Exception:
        return []


def save_execution_result(
    activation_id: str,
    outcome: str,  # executed | failed | instructions_only | blocked
    details: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> None:
    """Append execution result to history."""
    root = _repo_root(repo_root)
    _activations_root(root).mkdir(parents=True, exist_ok=True)
    entries = _load_history_entries(root)
    entries.append({
        "activation_id": activation_id,
        "outcome": outcome,
        "details": details or {},
        "recorded_at": _utc_now_iso(),
    })
    path = _history_path(root)
    path.write_text(json.dumps({"entries": entries[-500:]}, indent=2), encoding="utf-8")


def load_history(repo_root: Path | str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Load recent history entries (newest first)."""
    entries = _load_history_entries(repo_root)
    return list(reversed(entries[-limit:]))
