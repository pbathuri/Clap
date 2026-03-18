"""
M43I–M43L: List and resolve memory-backed slices from learning_lab, candidate_model_studio, corrections.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_substrate.models import MemorySliceSummary, MemoryBackedRef, MEMORY_SCOPE_EXPERIMENTAL, MEMORY_SCOPE_PRODUCTION_SAFE

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def list_memory_slices(
    repo_root: Path | str | None = None,
    scope: str = "",
    limit: int = 50,
) -> list[MemorySliceSummary]:
    """
    List logical memory slices from learning_lab experiments, candidate_model_studio slices, and corrections.
    scope: empty = all, production_safe | experimental to filter.
    """
    root = _root(repo_root)
    out: list[MemorySliceSummary] = []

    # 1. From learning_lab experiments (local_slice has evidence/correction ids)
    try:
        from workflow_dataset.learning_lab.store import list_experiments
        experiments = list_experiments(limit=limit, repo_root=root)
        for exp in experiments:
            if not exp.local_slice:
                continue
            ls = exp.local_slice
            n_ev = len(ls.evidence_ids)
            n_corr = len(ls.correction_ids)
            if n_ev == 0 and n_corr == 0:
                continue
            mid = f"mem_exp_{exp.experiment_id}"
            summary = MemorySliceSummary(
                memory_slice_id=mid,
                source_type="learning_lab_experiment",
                source_ref=exp.experiment_id,
                description=ls.description or f"Experiment {exp.experiment_id}",
                evidence_count=n_ev,
                correction_count=n_corr,
                scope=MEMORY_SCOPE_EXPERIMENTAL,
                created_at_utc=exp.created_at_utc,
            )
            if not scope or summary.scope == scope:
                out.append(summary)
    except Exception:
        pass

    # 2. From candidate_model_studio slices
    try:
        from workflow_dataset.candidate_model_studio.store import _studio_root, list_slices_for_candidate
        from workflow_dataset.candidate_model_studio.store import list_candidates
        studio_root = root / "data/local/candidate_model_studio" / "slices"
        if studio_root.exists():
            for p in sorted(studio_root.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
                try:
                    from workflow_dataset.candidate_model_studio.store import load_slice
                    s = load_slice(p.stem, repo_root=root)
                    if not s or (not s.included_evidence_ids and not s.included_correction_ids):
                        continue
                    mid = f"mem_cand_{s.slice_id}"
                    summary = MemorySliceSummary(
                        memory_slice_id=mid,
                        source_type="candidate_studio_slice",
                        source_ref=s.slice_id,
                        description=s.name or s.slice_id,
                        evidence_count=len(s.included_evidence_ids),
                        correction_count=len(s.included_correction_ids),
                        scope=MEMORY_SCOPE_EXPERIMENTAL if s.provenance_source != "production_safe" else MEMORY_SCOPE_PRODUCTION_SAFE,
                        created_at_utc=s.created_at_utc,
                    )
                    if not scope or summary.scope == scope:
                        out.append(summary)
                except Exception:
                    continue
    except Exception:
        pass

    # 3. From corrections (one aggregate "recent corrections" slice)
    try:
        from workflow_dataset.corrections.store import list_corrections
        corrections = list_corrections(limit=100, repo_root=root)
        if corrections:
            cids = [c.correction_id for c in corrections[:50]]
            mid = "mem_corrections_recent"
            summary = MemorySliceSummary(
                memory_slice_id=mid,
                source_type="corrections_set",
                source_ref="recent",
                description="Recent corrections (last 50)",
                evidence_count=0,
                correction_count=len(cids),
                scope=MEMORY_SCOPE_EXPERIMENTAL,
                created_at_utc="",
            )
            if not scope or summary.scope == scope:
                out.append(summary)
    except Exception:
        pass

    return out[:limit]


def get_memory_slice_refs(
    memory_slice_id: str,
    repo_root: Path | str | None = None,
) -> MemoryBackedRef | None:
    """
    Resolve a memory_slice_id to evidence_ids, correction_ids, etc.
    Supports mem_exp_<experiment_id>, mem_cand_<slice_id>, mem_corrections_recent.
    """
    root = _root(repo_root)
    if memory_slice_id.startswith("mem_exp_"):
        exp_id = memory_slice_id.replace("mem_exp_", "", 1)
        try:
            from workflow_dataset.learning_lab.store import get_experiment
            exp = get_experiment(exp_id, repo_root=root)
            if not exp or not exp.local_slice:
                return None
            ls = exp.local_slice
            return MemoryBackedRef(
                memory_slice_id=memory_slice_id,
                evidence_ids=list(ls.evidence_ids),
                correction_ids=list(ls.correction_ids),
                issue_ids=list(ls.issue_ids),
                scope=MEMORY_SCOPE_EXPERIMENTAL,
            )
        except Exception:
            return None
    if memory_slice_id.startswith("mem_cand_"):
        slice_id = memory_slice_id.replace("mem_cand_", "", 1)
        try:
            from workflow_dataset.candidate_model_studio.store import load_slice
            s = load_slice(slice_id, repo_root=root)
            if not s:
                return None
            scope = MEMORY_SCOPE_PRODUCTION_SAFE if s.provenance_source == "production_safe" else MEMORY_SCOPE_EXPERIMENTAL
            return MemoryBackedRef(
                memory_slice_id=memory_slice_id,
                evidence_ids=list(s.included_evidence_ids),
                correction_ids=list(s.included_correction_ids),
                scope=scope,
            )
        except Exception:
            return None
    if memory_slice_id == "mem_corrections_recent":
        try:
            from workflow_dataset.corrections.store import list_corrections
            corrections = list_corrections(limit=50, repo_root=root)
            cids = [c.correction_id for c in corrections]
            return MemoryBackedRef(
                memory_slice_id=memory_slice_id,
                correction_ids=cids,
                scope=MEMORY_SCOPE_EXPERIMENTAL,
            )
        except Exception:
            return None
    return None
