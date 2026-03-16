"""
M23J: Job packs paths. data/local/job_packs.
"""

from __future__ import annotations

from pathlib import Path

JOB_PACKS_ROOT = "data/local/job_packs"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_job_packs_root(repo_root: Path | str | None = None) -> Path:
    """Return job packs root (data/local/job_packs)."""
    base = _repo_root(repo_root)
    out = base / JOB_PACKS_ROOT
    out.mkdir(parents=True, exist_ok=True)
    return out


def get_job_pack_path(job_pack_id: str, repo_root: Path | str | None = None) -> Path:
    """Path to job pack file: job_packs/<safe_id>.yaml."""
    root = get_job_packs_root(repo_root)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in job_pack_id.strip())
    return root / f"{safe_id}.yaml"


def get_specialization_path(job_pack_id: str, repo_root: Path | str | None = None) -> Path:
    """Path to specialization file: job_packs/<safe_id>/specialization.yaml."""
    root = get_job_packs_root(repo_root)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in job_pack_id.strip())
    return root / safe_id / "specialization.yaml"


def get_job_runs_dir(repo_root: Path | str | None = None) -> Path:
    """Directory for job run manifests index (optional)."""
    d = get_job_packs_root(repo_root) / "runs"
    d.mkdir(parents=True, exist_ok=True)
    return d
