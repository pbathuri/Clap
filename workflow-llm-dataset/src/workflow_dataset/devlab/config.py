"""
M21W: Devlab paths and config. All under a single sandbox root; no writes outside.
"""

from __future__ import annotations

from pathlib import Path

# Sandbox root — relative to CWD when running CLI (typically repo root)
DEVLAB_ROOT = Path("data/local/devlab")


def get_devlab_root(root: Path | str | None = None) -> Path:
    """Return devlab sandbox root; ensure parent exists."""
    base = Path(root) if root else DEVLAB_ROOT
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_repos_dir(root: Path | str | None = None) -> Path:
    """Cloned repos live here; never mixed with product code."""
    d = get_devlab_root(root) / "repos"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_reports_dir(root: Path | str | None = None) -> Path:
    """Per-repo intake reports and devlab_report.md."""
    d = get_devlab_root(root) / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_model_compare_dir(root: Path | str | None = None) -> Path:
    """Model comparison outputs."""
    d = get_devlab_root(root) / "model_compare"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_registry_path(root: Path | str | None = None) -> Path:
    """Devlab repo registry (candidate URLs, label, category, priority)."""
    get_devlab_root(root)
    return get_devlab_root(root) / "registry.json"


def get_loop_artifact_path(name: str, root: Path | str | None = None) -> Path:
    """Loop artifacts: devlab_report.md, next_patch_plan.md, loop_status.json."""
    return get_devlab_root(root) / name


def get_experiments_dir(root: Path | str | None = None) -> Path:
    """Experiment definitions (JSON)."""
    d = get_devlab_root(root) / "experiments"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_experiment_runs_dir(root: Path | str | None = None) -> Path:
    """Experiment run outputs (links to eval runs or local copy)."""
    d = get_devlab_root(root) / "experiment_runs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_proposals_dir(root: Path | str | None = None) -> Path:
    """Patch proposals (experiment_report.md, patch_proposal.md, devlab_proposal.md, etc.)."""
    d = get_devlab_root(root) / "proposals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_experiment_queue_path(root: Path | str | None = None) -> Path:
    """Queue of experiment runs: pending, running, done, failed."""
    return get_devlab_root(root) / "experiment_queue.json"
