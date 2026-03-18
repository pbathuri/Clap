"""
M44L.1: Memory-grounded vertical playbooks — prior successful cases + 'this worked before' operator guidance.
Extends M44I–M44L; does not replace vertical_packs playbooks.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.memory_intelligence.models import (
    MemoryGroundedPlaybook,
    RetrievedPriorCase,
    ThisWorkedBeforeEntry,
)
from workflow_dataset.memory_intelligence.retrieval import retrieve_for_context, CONFIDENCE_THRESHOLD_WEAK
from workflow_dataset.memory_intelligence.store import save_memory_grounded_playbook
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_memory_grounded_playbook(
    curated_pack_id: str,
    repo_root: Path | str | None = None,
    limit_cases: int = 10,
    persist: bool = True,
) -> MemoryGroundedPlaybook:
    """
    Build a memory-grounded playbook for the vertical: base playbook (if any) + prior successful cases
    + 'this worked before in similar situations' operator guidance. Reviewable by default.
    """
    root = _repo_root(repo_root)
    label = f"Memory-grounded playbook for {curated_pack_id}"
    description = "Operator guidance backed by prior successful cases for this vertical."
    base_playbook_id = ""
    try:
        from workflow_dataset.vertical_packs.playbooks import get_playbook_for_vertical
        base = get_playbook_for_vertical(curated_pack_id)
        if base:
            base_playbook_id = getattr(base, "playbook_id", "") or ""
            label = getattr(base, "label", label) + " (memory-grounded)"
            description = (getattr(base, "description", "") or description) + " Enriched with prior successful cases."
    except Exception:
        pass

    prior = retrieve_for_context(
        project_id="",
        session_id=None,
        query=f"vertical {curated_pack_id} success recovery first-value",
        limit=limit_cases,
        repo_root=root,
    )
    prior_successful = [p for p in prior if p.confidence >= CONFIDENCE_THRESHOLD_WEAK]
    this_worked_before: list[ThisWorkedBeforeEntry] = []
    for i, p in enumerate(prior_successful[:5]):
        this_worked_before.append(ThisWorkedBeforeEntry(
            guidance_id=stable_id("twb", curated_pack_id, p.unit_id, str(i), prefix="twb_"),
            situation_summary=f"Prior case from {p.source or 'memory'}",
            what_worked=p.relevance_summary[:200] or p.snippet[:200],
            prior_case_unit_id=p.unit_id,
            prior_case_snippet=p.snippet[:400],
            confidence=p.confidence,
            reviewable=True,
        ))
    operator_guidance_from_memory = ""
    if this_worked_before:
        operator_guidance_from_memory = (
            "This worked before in similar situations: "
            + "; ".join(t.what_worked[:80] for t in this_worked_before[:3])
        )
    else:
        operator_guidance_from_memory = "No prior successful cases in memory for this vertical yet. Use base playbook."

    playbook_id = stable_id("mgp", curated_pack_id, utc_now_iso()[:16], prefix="mgp_")
    pb = MemoryGroundedPlaybook(
        playbook_id=playbook_id,
        curated_pack_id=curated_pack_id,
        label=label,
        description=description,
        base_playbook_id=base_playbook_id,
        prior_successful_cases=prior_successful[:limit_cases],
        this_worked_before=this_worked_before,
        operator_guidance_from_memory=operator_guidance_from_memory,
        reviewable=True,
        created_at_utc=utc_now_iso(),
    )
    if persist:
        save_memory_grounded_playbook(pb, repo_root=root)
    return pb
