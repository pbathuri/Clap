"""
M43I–M43L: Memory-backed slices for learning lab — list memory slices, create experiment from memory slice.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_substrate.slices import list_memory_slices, get_memory_slice_refs
from workflow_dataset.memory_substrate.models import MemorySliceSummary


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def list_memory_slices_for_learning(
    repo_root: Path | str | None = None,
    scope: str = "",
    limit: int = 30,
) -> list[MemorySliceSummary]:
    """List memory slices usable for learning-lab experiments (delegate to memory substrate)."""
    return list_memory_slices(repo_root=repo_root, scope=scope, limit=limit)


def create_experiment_from_memory_slice(
    memory_slice_id: str,
    profile_id: str = "",
    template_id: str = "",
    label: str = "",
    repo_root: Path | str | None = None,
):
    """Create a learning-lab experiment from a memory-backed slice (resolves refs via memory substrate)."""
    root = _root(repo_root)
    from workflow_dataset.memory_substrate.slices import get_memory_slice_refs
    from workflow_dataset.learning_lab.models import (
        ImprovementExperiment,
        LocalLearningSlice,
        ExperimentEvidenceBundle,
        OUTCOME_PENDING,
    )
    from workflow_dataset.learning_lab.store import save_experiment, set_active_experiment_id
    from workflow_dataset.learning_lab.experiments import _apply_profile_and_template
    try:
        from workflow_dataset.utils.dates import utc_now_iso
    except Exception:
        from datetime import datetime, timezone
        def utc_now_iso() -> str:
            return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        from workflow_dataset.utils.hashes import stable_id
    except Exception:
        def stable_id(*parts: str, prefix: str = "") -> str:
            import hashlib
            return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]

    refs = get_memory_slice_refs(memory_slice_id, repo_root=root)
    if not refs:
        return None
    exp_id = stable_id("exp", "memory_slice", memory_slice_id, utc_now_iso(), prefix="exp_")
    now = utc_now_iso()
    local_slice = LocalLearningSlice(
        slice_id=stable_id("slice", memory_slice_id, prefix="slice_"),
        description=f"Memory-backed: {memory_slice_id}",
        evidence_ids=list(refs.evidence_ids),
        correction_ids=list(refs.correction_ids),
        issue_ids=list(refs.issue_ids),
        memory_slice_id=memory_slice_id,
    )
    evidence_bundle = ExperimentEvidenceBundle(
        evidence_ids=list(refs.evidence_ids)[:30],
        correction_ids=list(refs.correction_ids),
        session_ids=list(refs.session_ids),
        summary=f"From memory slice {memory_slice_id}; {refs.evidence_ids and len(refs.evidence_ids) or 0} evidence, {len(refs.correction_ids)} corrections",
    )
    exp = ImprovementExperiment(
        experiment_id=exp_id,
        source_type="memory_slice",
        source_ref=memory_slice_id,
        label=label or f"Experiment from memory slice {memory_slice_id}",
        created_at_utc=now,
        status=OUTCOME_PENDING,
        local_slice=local_slice,
        evidence_bundle=evidence_bundle,
        comparison_summary="",
    )
    _apply_profile_and_template(exp, profile_id, template_id, root)
    save_experiment(exp, root)
    set_active_experiment_id(exp_id, root)
    return exp
