"""
M23I: Desktop benchmark paths. All under data/local/desktop_bench.
"""

from __future__ import annotations

from pathlib import Path

DESKTOP_BENCH_ROOT = "data/local/desktop_bench"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_desktop_bench_root(repo_root: Path | str | None = None) -> Path:
    """Return desktop benchmark root (data/local/desktop_bench under repo root)."""
    base = _repo_root(repo_root)
    out = base / DESKTOP_BENCH_ROOT
    out.mkdir(parents=True, exist_ok=True)
    return out


def get_cases_dir(repo_root: Path | str | None = None) -> Path:
    """Cases directory (benchmark case YAML/JSON files)."""
    d = get_desktop_bench_root(repo_root) / "cases"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_runs_dir(repo_root: Path | str | None = None) -> Path:
    """Runs directory (one dir per run_id)."""
    d = get_desktop_bench_root(repo_root) / "runs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_suites_dir(repo_root: Path | str | None = None) -> Path:
    """Suites directory (suite YAML/JSON: list of case_ids)."""
    d = get_desktop_bench_root(repo_root) / "suites"
    d.mkdir(parents=True, exist_ok=True)
    return d
