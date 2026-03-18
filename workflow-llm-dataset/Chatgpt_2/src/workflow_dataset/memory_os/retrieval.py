"""
M44B–M44C: Memory OS retrieval — single entry point with retrieval_id and explanation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_os.models import (
    RetrievalIntentOS,
    RetrievalScope,
    MemoryEvidenceBundle,
    MemoryEvidenceItem,
    RetrievalExplanation,
)
from workflow_dataset.memory_os.surfaces import retrieve_via_surface, get_surface
from workflow_dataset.memory_os.profiles import get_profile, get_profile_reason, apply_profile_filters

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]


def retrieve(
    surface_id: str,
    scope: RetrievalScope,
    intent: RetrievalIntentOS,
    repo_root: Path | str | None = None,
    profile_id: str | None = None,
) -> tuple[list[dict[str, Any]], str, RetrievalExplanation]:
    """
    Retrieve memory for surface + scope + intent. Optional profile_id applies filters and sets profile_used/profile_reason.
    Returns (items, retrieval_id, explanation).
    """
    root = Path(repo_root).resolve() if repo_root else None
    if not root:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()

    profile = get_profile(profile_id) if profile_id else None
    if profile and profile.max_items > 0 and profile.max_items < intent.top_k:
        intent = RetrievalIntentOS(intent=intent.intent, query=intent.query, top_k=profile.max_items)

    retrieval_id = stable_id("memret", surface_id, scope.entity_id or scope.session_id or scope.project_id, intent.intent, prefix="memret_")
    items, weak = retrieve_via_surface(surface_id, scope, intent, repo_root=root)
    items = apply_profile_filters(items, profile)

    evidence_items = [
        MemoryEvidenceItem(
            memory_id=it.get("memory_id", ""),
            source=it.get("source", "substrate"),
            score=it.get("confidence", 0.0),
            provenance_ref=it.get("memory_id", ""),
            snippet=(it.get("text", "") or "")[:300],
        )
        for it in items
    ]
    bundle = MemoryEvidenceBundle(retrieval_id=retrieval_id, items=evidence_items, total_count=len(items))

    weak_warnings = [f"Memory {w.get('memory_id', '')} has low confidence or needs review" for w in weak[:5]]
    profile_used = profile_id or ""
    profile_reason = get_profile_reason(profile_used) if profile_used else ""

    if not items:
        explanation = RetrievalExplanation(
            retrieval_id=retrieval_id,
            reason="No memory found for this scope and intent."
            + (" Profile filters may have excluded all items." if profile else ""),
            evidence_bundle=bundle,
            confidence=0.0,
            weak_memory_warnings=weak_warnings,
            no_match_reason="No links or units for the given scope; try broader scope or add links.",
            profile_used=profile_used,
            profile_reason=profile_reason,
        )
    else:
        avg_conf = sum(it.get("confidence", 0) for it in items) / len(items) if items else 0.0
        explanation = RetrievalExplanation(
            retrieval_id=retrieval_id,
            reason=f"Retrieved {len(items)} item(s) for surface={surface_id}, intent={intent.intent}.",
            evidence_bundle=bundle,
            confidence=avg_conf,
            near_match_ids=[],
            weak_memory_warnings=weak_warnings,
            profile_used=profile_used,
            profile_reason=profile_reason,
        )

    return items, retrieval_id, explanation
