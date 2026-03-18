"""
M41A–M41D: Persist improvement experiments and learning lab state. data/local/learning_lab/
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.learning_lab.models import ImprovementExperiment, LocalLearningSlice, ExperimentEvidenceBundle, RollbackableChangeSet


DIR_NAME = "data/local/learning_lab"
EXPERIMENTS_FILE = "experiments.jsonl"
ACTIVE_EXPERIMENT_FILE = "active_experiment_id.txt"
CURRENT_PROFILE_FILE = "current_profile_id.txt"  # M41D.1


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _dir(repo_root: Path | str | None = None) -> Path:
    return _root(repo_root) / DIR_NAME


def _experiments_path(repo_root: Path | str | None = None) -> Path:
    return _dir(repo_root) / EXPERIMENTS_FILE


def _dict_to_experiment(d: dict[str, Any]) -> ImprovementExperiment:
    ls = None
    if d.get("local_slice"):
        sl = d["local_slice"]
        ls = LocalLearningSlice(
            slice_id=sl.get("slice_id", ""),
            description=sl.get("description", ""),
            evidence_ids=sl.get("evidence_ids", []),
            correction_ids=sl.get("correction_ids", []),
            issue_ids=sl.get("issue_ids", []),
            run_ids=sl.get("run_ids", []),
            memory_slice_id=sl.get("memory_slice_id", ""),
        )
    eb = None
    if d.get("evidence_bundle"):
        b = d["evidence_bundle"]
        eb = ExperimentEvidenceBundle(
            evidence_ids=b.get("evidence_ids", []),
            correction_ids=b.get("correction_ids", []),
            session_ids=b.get("session_ids", []),
            summary=b.get("summary", ""),
        )
    rollback = [RollbackableChangeSet(
        change_set_id=c.get("change_set_id", ""),
        description=c.get("description", ""),
        target_type=c.get("target_type", ""),
        target_id=c.get("target_id", ""),
        applied_at_utc=c.get("applied_at_utc", ""),
        revertible=c.get("revertible", True),
    ) for c in d.get("rollbackable_changes", [])]
    return ImprovementExperiment(
        experiment_id=d.get("experiment_id", ""),
        source_type=d.get("source_type", ""),
        source_ref=d.get("source_ref", ""),
        label=d.get("label", ""),
        created_at_utc=d.get("created_at_utc", ""),
        status=d.get("status", "pending"),
        status_reason=d.get("status_reason", ""),
        local_slice=ls,
        evidence_bundle=eb,
        comparison_summary=d.get("comparison_summary", ""),
        rollbackable_changes=rollback,
        approved_scope_id=d.get("approved_scope_id", ""),
        profile_id=d.get("profile_id", ""),
        template_id=d.get("template_id", ""),
    )


def save_experiment(exp: ImprovementExperiment, repo_root: Path | str | None = None) -> Path:
    """Append experiment to experiments.jsonl; create dir if needed."""
    path = _experiments_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(exp.to_dict()) + "\n")
    return path


def list_experiments(
    limit: int = 50,
    status: str | None = None,
    repo_root: Path | str | None = None,
) -> list[ImprovementExperiment]:
    """Load experiments from experiments.jsonl (newest last in file = last N)."""
    path = _experiments_path(repo_root)
    if not path.exists():
        return []
    experiments: list[ImprovementExperiment] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                experiments.append(_dict_to_experiment(d))
            except Exception:
                continue
    if status:
        experiments = [e for e in experiments if e.status == status]
    return experiments[-limit:] if limit else experiments


def get_experiment(experiment_id: str, repo_root: Path | str | None = None) -> ImprovementExperiment | None:
    """Get one experiment by id (latest when multiple lines same id)."""
    matches = [e for e in list_experiments(limit=500, repo_root=repo_root) if e.experiment_id == experiment_id]
    return matches[-1] if matches else None


def set_active_experiment_id(experiment_id: str, repo_root: Path | str | None = None) -> Path:
    path = _dir(repo_root) / ACTIVE_EXPERIMENT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(experiment_id.strip(), encoding="utf-8")
    return path


def get_active_experiment_id(repo_root: Path | str | None = None) -> str:
    path = _dir(repo_root) / ACTIVE_EXPERIMENT_FILE
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def set_current_profile_id(profile_id: str, repo_root: Path | str | None = None) -> Path:
    """M41D.1: Persist current learning profile id."""
    path = _dir(repo_root) / CURRENT_PROFILE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile_id.strip(), encoding="utf-8")
    return path


def get_current_profile_id(repo_root: Path | str | None = None) -> str:
    """M41D.1: Read current learning profile id; default to balanced if missing."""
    path = _dir(repo_root) / CURRENT_PROFILE_FILE
    if not path.exists():
        return "balanced"
    return path.read_text(encoding="utf-8").strip() or "balanced"
