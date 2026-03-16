"""
M21X: Eval paths. All under data/local/eval when root is repo; or root is the eval root when provided.
"""

from __future__ import annotations

from pathlib import Path

EVAL_ROOT = "data/local/eval"


def get_eval_root(root: Path | str | None = None) -> Path:
    """Return eval root. If root is provided, use it as eval root; else repo_root / data/local/eval."""
    if root is not None:
        p = Path(root)
        p.mkdir(parents=True, exist_ok=True)
        return p
    from workflow_dataset.path_utils import get_repo_root
    base = Path(get_repo_root()) / EVAL_ROOT
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_cases_dir(root: Path | str | None = None) -> Path:
    """Cases directory (case JSON files)."""
    d = get_eval_root(root) / "cases"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_runs_dir(root: Path | str | None = None) -> Path:
    """Runs directory (one dir per run_id)."""
    d = get_eval_root(root) / "runs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_suites_dir(root: Path | str | None = None) -> Path:
    """Suites directory (suite JSON: list of case_ids)."""
    d = get_eval_root(root) / "suites"
    d.mkdir(parents=True, exist_ok=True)
    return d
