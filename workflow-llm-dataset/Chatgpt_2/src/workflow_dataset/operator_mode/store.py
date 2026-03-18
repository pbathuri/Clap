"""
M35E–M35H: Persist operator mode profiles, responsibilities, state.
M35H.1: Bundles, pause state, revocation history.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.operator_mode.models import (
    OperatorModeProfile,
    DelegatedResponsibility,
    ResponsibilityKind,
    SuspensionRevocationState,
    ResponsibilityBundle,
    PauseState,
    PauseKind,
    RevocationRecord,
)

OPERATOR_MODE_DIR = Path("data/local/operator_mode")
PROFILES_SUBDIR = "profiles"
RESPONSIBILITIES_SUBDIR = "responsibilities"
BUNDLES_SUBDIR = "bundles"
STATE_FILE = "state.json"
REVOCATION_HISTORY_FILE = "revocation_history.json"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _base_dir(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / OPERATOR_MODE_DIR


def _profiles_dir(repo_root: Path | str | None) -> Path:
    return _base_dir(repo_root) / PROFILES_SUBDIR


def _responsibilities_dir(repo_root: Path | str | None) -> Path:
    return _base_dir(repo_root) / RESPONSIBILITIES_SUBDIR


def _bundles_dir(repo_root: Path | str | None) -> Path:
    return _base_dir(repo_root) / BUNDLES_SUBDIR


# ----- Profiles -----


def list_profile_ids(repo_root: Path | str | None = None) -> list[str]:
    d = _profiles_dir(repo_root)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json") if p.stem and not p.stem.startswith("."))


def get_profile(profile_id: str, repo_root: Path | str | None = None) -> OperatorModeProfile | None:
    path = _profiles_dir(repo_root) / f"{profile_id}.json"
    if not path.exists():
        return None
    try:
        return OperatorModeProfile.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def save_profile(profile: OperatorModeProfile, repo_root: Path | str | None = None) -> Path:
    d = _profiles_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{profile.profile_id or 'profile'}.json"
    path.write_text(json.dumps(profile.model_dump(), indent=2), encoding="utf-8")
    return path


# ----- Responsibilities -----


def list_responsibility_ids(repo_root: Path | str | None = None) -> list[str]:
    d = _responsibilities_dir(repo_root)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json") if p.stem and not p.stem.startswith("."))


def get_responsibility(responsibility_id: str, repo_root: Path | str | None = None) -> DelegatedResponsibility | None:
    path = _responsibilities_dir(repo_root) / f"{responsibility_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("kind") and isinstance(data["kind"], str):
            data["kind"] = ResponsibilityKind(data["kind"])
        return DelegatedResponsibility.model_validate(data)
    except Exception:
        return None


def save_responsibility(r: DelegatedResponsibility, repo_root: Path | str | None = None) -> Path:
    d = _responsibilities_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{r.responsibility_id or 'resp'}.json"
    data = r.model_dump()
    data["kind"] = r.kind.value
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


# ----- Suspension / revocation state -----


def load_suspension_revocation_state(repo_root: Path | str | None = None) -> SuspensionRevocationState:
    path = _base_dir(repo_root) / STATE_FILE
    if not path.exists():
        return SuspensionRevocationState()
    try:
        return SuspensionRevocationState.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return SuspensionRevocationState()


def save_suspension_revocation_state(state: SuspensionRevocationState, repo_root: Path | str | None = None) -> Path:
    _base_dir(repo_root).mkdir(parents=True, exist_ok=True)
    path = _base_dir(repo_root) / STATE_FILE
    path.write_text(json.dumps(state.model_dump(), indent=2), encoding="utf-8")
    return path


# ----- M35H.1 Bundles -----


def list_bundle_ids(repo_root: Path | str | None = None) -> list[str]:
    d = _bundles_dir(repo_root)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json") if p.stem and not p.stem.startswith("."))


def get_bundle(bundle_id: str, repo_root: Path | str | None = None) -> ResponsibilityBundle | None:
    path = _bundles_dir(repo_root) / f"{bundle_id}.json"
    if not path.exists():
        return None
    try:
        return ResponsibilityBundle.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def save_bundle(bundle: ResponsibilityBundle, repo_root: Path | str | None = None) -> Path:
    d = _bundles_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{bundle.bundle_id or 'bundle'}.json"
    path.write_text(json.dumps(bundle.model_dump(), indent=2), encoding="utf-8")
    return path


# ----- M35H.1 Pause state -----


def load_pause_state(repo_root: Path | str | None = None) -> PauseState:
    path = _base_dir(repo_root) / "pause_state.json"
    if not path.exists():
        return PauseState()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("kind") and isinstance(data["kind"], str):
            data["kind"] = PauseKind(data["kind"])
        return PauseState.model_validate(data)
    except Exception:
        return PauseState()


def save_pause_state(state: PauseState, repo_root: Path | str | None = None) -> Path:
    _base_dir(repo_root).mkdir(parents=True, exist_ok=True)
    path = _base_dir(repo_root) / "pause_state.json"
    data = state.model_dump()
    data["kind"] = state.kind.value
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


# ----- M35H.1 Revocation history -----


def load_revocation_history(repo_root: Path | str | None = None) -> list[RevocationRecord]:
    path = _base_dir(repo_root) / REVOCATION_HISTORY_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [RevocationRecord.model_validate(r) for r in (data if isinstance(data, list) else data.get("records", []))]
    except Exception:
        return []


def append_revocation_record(record: RevocationRecord, repo_root: Path | str | None = None) -> Path:
    _base_dir(repo_root).mkdir(parents=True, exist_ok=True)
    path = _base_dir(repo_root) / REVOCATION_HISTORY_FILE
    records = load_revocation_history(repo_root)
    records.append(record)
    path.write_text(json.dumps({"records": [r.model_dump() for r in records]}, indent=2), encoding="utf-8")
    return path
