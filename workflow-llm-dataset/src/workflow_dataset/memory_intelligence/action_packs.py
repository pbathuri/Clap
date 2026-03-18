"""
M44L.1: Memory-grounded action packs — actions driven by prior successful cases; reviewable defaults.
Extends M44I–M44L.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.memory_intelligence.models import (
    MemoryGroundedActionPack,
    MemoryGroundedAction,
    RetrievedPriorCase,
)
from workflow_dataset.memory_intelligence.retrieval import retrieve_for_context, CONFIDENCE_THRESHOLD_WEAK
from workflow_dataset.memory_intelligence.store import save_memory_grounded_action_pack
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


def build_memory_grounded_action_pack(
    vertical_id: str = "",
    project_id: str = "",
    repo_root: Path | str | None = None,
    limit_cases: int = 10,
    max_actions: int = 5,
    persist: bool = True,
) -> MemoryGroundedActionPack:
    """
    Build an action pack driven by prior successful cases for this vertical/project.
    Each action is backed by prior case(s); reviewable defaults for operator.
    """
    root = _repo_root(repo_root)
    scope = vertical_id or project_id or "default"
    prior = retrieve_for_context(
        project_id=project_id,
        session_id=None,
        query=f"success next step action {vertical_id or project_id}",
        limit=limit_cases,
        repo_root=root,
    )
    prior_successful = [p for p in prior if p.confidence >= CONFIDENCE_THRESHOLD_WEAK]
    actions: list[MemoryGroundedAction] = []
    seen_hints: set[str] = set()
    for i, p in enumerate(prior_successful[:max_actions]):
        hint = (p.relevance_summary or p.snippet or "")[:60]
        if hint in seen_hints:
            continue
        seen_hints.add(hint)
        action_id = stable_id("mga", scope, p.unit_id, str(i), prefix="mga_")
        actions.append(MemoryGroundedAction(
            action_id=action_id,
            label="Memory-backed action",
            command_hint="workflow-dataset memory-intelligence suggest --project " + (project_id or scope),
            what_worked_summary=p.relevance_summary[:200] or p.snippet[:200],
            prior_case_unit_ids=[p.unit_id],
            confidence=p.confidence,
            reviewable=True,
        ))
    if not actions and prior_successful:
        actions.append(MemoryGroundedAction(
            action_id=stable_id("mga", scope, "default", prefix="mga_"),
            label="Continue from prior context",
            command_hint="workflow-dataset memory-intelligence prior-cases --project " + (project_id or scope),
            what_worked_summary=prior_successful[0].relevance_summary[:200],
            prior_case_unit_ids=[prior_successful[0].unit_id],
            confidence=prior_successful[0].confidence,
            reviewable=True,
        ))

    pack_id = stable_id("mgap", scope, utc_now_iso()[:16], prefix="mgap_")
    pack = MemoryGroundedActionPack(
        action_pack_id=pack_id,
        label=f"Memory-grounded actions for {scope}",
        description="Actions driven by prior successful cases; review before applying.",
        vertical_id=vertical_id,
        project_id=project_id,
        actions=actions,
        prior_successful_cases=prior_successful[:limit_cases],
        reviewable=True,
        created_at_utc=utc_now_iso(),
    )
    if persist:
        save_memory_grounded_action_pack(pack, repo_root=root)
    return pack
