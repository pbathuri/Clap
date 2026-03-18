"""
M23A: Chain lab sandbox paths. All under a single local root; no writes outside.
"""

from __future__ import annotations

from pathlib import Path

CHAIN_LAB_ROOT = Path("data/local/chain_lab")
CHAINS_SUBDIR = "chains"
RUNS_SUBDIR = "runs"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd().resolve()


def get_chain_lab_root(repo_root: Path | str | None = None) -> Path:
    """Return chain lab sandbox root; ensure it exists."""
    root = _repo_root(repo_root)
    base = root / CHAIN_LAB_ROOT if not (root / CHAIN_LAB_ROOT).is_absolute() else Path(CHAIN_LAB_ROOT)
    if not base.is_absolute():
        base = root / base
    base = base.resolve()
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_chains_dir(repo_root: Path | str | None = None) -> Path:
    """Chain definition JSON files."""
    d = get_chain_lab_root(repo_root) / CHAINS_SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_runs_dir(repo_root: Path | str | None = None) -> Path:
    """Per-run directories: run_manifest.json + step outputs."""
    d = get_chain_lab_root(repo_root) / RUNS_SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    return d
