"""
Persistent store for setup sessions, scan jobs, and checkpoints.

All under a local base path (e.g. data/local/setup/). JSON files for inspectability.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.setup.setup_models import (
    SetupSession,
    SetupStage,
    ScanJob,
    SetupProgress,
    ScanScope,
)
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _ensure_dir(p: Path) -> Path:
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


def session_path(base_dir: Path, session_id: str) -> Path:
    return base_dir / "sessions" / f"{session_id}.json"


def jobs_dir(base_dir: Path, session_id: str) -> Path:
    return _ensure_dir(base_dir / "jobs" / session_id)


def job_path(base_dir: Path, session_id: str, job_id: str) -> Path:
    return jobs_dir(base_dir, session_id) / f"{job_id}.json"


def progress_path(base_dir: Path, session_id: str) -> Path:
    return base_dir / "progress" / f"{session_id}.json"


def save_session(base_dir: Path, session: SetupSession) -> Path:
    base_dir = Path(base_dir)
    _ensure_dir(base_dir / "sessions")
    path = session_path(base_dir, session.session_id)
    data = session.model_dump()
    for k, v in data.items():
        if isinstance(v, type(SetupStage.BOOTSTRAP)):
            data[k] = v.value
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_session(base_dir: Path, session_id: str) -> SetupSession | None:
    path = session_path(Path(base_dir), session_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "current_stage" in data and isinstance(data["current_stage"], str):
        data["current_stage"] = SetupStage(data["current_stage"])
    if "scan_scope" in data and isinstance(data["scan_scope"], dict):
        from pydantic import TypeAdapter
        data["scan_scope"] = TypeAdapter(ScanScope).validate_python(data["scan_scope"])
    return SetupSession.model_validate(data)


def save_job(base_dir: Path, job: ScanJob) -> Path:
    base_dir = Path(base_dir)
    d = jobs_dir(base_dir, job.session_id)
    path = d / f"{job.job_id}.json"
    data = job.model_dump()
    if "stage" in data and hasattr(data["stage"], "value"):
        data["stage"] = data["stage"].value
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_job(base_dir: Path, session_id: str, job_id: str) -> ScanJob | None:
    path = job_path(Path(base_dir), session_id, job_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "stage" in data and isinstance(data["stage"], str):
        data["stage"] = SetupStage(data["stage"])
    return ScanJob.model_validate(data)


def list_jobs(base_dir: Path, session_id: str) -> list[ScanJob]:
    d = jobs_dir(Path(base_dir), session_id)
    if not d.exists():
        return []
    out = []
    for path in d.glob("*.json"):
        job = load_job(base_dir, session_id, path.stem)
        if job:
            out.append(job)
    return out


def save_progress(base_dir: Path, progress: SetupProgress) -> Path:
    base_dir = Path(base_dir)
    _ensure_dir(base_dir / "progress")
    path = progress_path(base_dir, progress.session_id)
    data = progress.model_dump()
    if "current_stage" in data and hasattr(data["current_stage"], "value"):
        data["current_stage"] = data["current_stage"].value
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_progress(base_dir: Path, session_id: str) -> SetupProgress | None:
    path = progress_path(Path(base_dir), session_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "current_stage" in data and isinstance(data["current_stage"], str):
        data["current_stage"] = SetupStage(data["current_stage"])
    return SetupProgress.model_validate(data)


def create_session(
    base_dir: Path,
    scan_roots: list[str],
    exclude_dirs: list[str] | None = None,
    enabled_adapters: list[str] | None = None,
    max_runtime_hours: float = 36.0,
    onboarding_mode: str = "conservative",
    config_snapshot: dict | None = None,
) -> SetupSession:
    """Create and persist a new setup session."""
    session_id = stable_id("setup", utc_now_iso(), *scan_roots[:3], prefix="session")
    ts = utc_now_iso()
    scope = ScanScope(
        root_paths=[str(Path(r).resolve()) for r in scan_roots],
        exclude_dirs=exclude_dirs or [".git", "__pycache__", "node_modules", ".venv"],
    )
    snapshot = dict(config_snapshot or {})
    session = SetupSession(
        session_id=session_id,
        created_utc=ts,
        updated_utc=ts,
        current_stage=SetupStage.BOOTSTRAP,
        onboarding_mode=onboarding_mode,
        scan_scope=scope,
        enabled_adapters=enabled_adapters or ["document", "tabular", "creative", "design", "finance", "ops"],
        max_runtime_hours=max_runtime_hours,
        resume_enabled=True,
        config_snapshot=snapshot,
    )
    save_session(Path(base_dir), session)
    return session
