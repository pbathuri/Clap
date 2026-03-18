"""
M44H.1: Review packs — bundle forgetting/compression actions for operator review in one go.
"""

from __future__ import annotations

from workflow_dataset.memory_curation.models import (
    ReviewPack,
    ReviewPackItem,
    ForgettingCandidate,
    CompressionCandidate,
    ReviewRequiredDeletionCandidate,
)
from workflow_dataset.memory_curation.store import (
    load_review_required,
    load_forgetting_candidates,
    load_compression_candidates,
    load_review_packs,
    save_review_packs,
    save_review_required,
    save_forgetting_candidates,
)
from workflow_dataset.memory_curation.explanations import (
    build_review_required_explanation,
    build_compressible_explanation,
)

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def create_review_pack(
    repo_root=None,
    *,
    label: str = "",
    include_pending_review_required: bool = True,
    include_unapplied_compression: bool = False,
    max_forgetting: int = 50,
    max_compression: int = 20,
) -> ReviewPack | None:
    """
    Build a new review pack from pending review-required deletions and optionally unapplied compression candidates.
    Persists the pack and returns it. Returns None if no items to review.
    """
    review_list = load_review_required(repo_root)
    forget_list = load_forgetting_candidates(repo_root)
    comp_list = load_compression_candidates(repo_root) if include_unapplied_compression else []
    forget_by_id = {c.candidate_id: c for c in forget_list}

    items: list[ReviewPackItem] = []
    # Pending review-required (forgetting that needs approval)
    for r in review_list:
        if r.reviewed:
            continue
        if len(items) >= max_forgetting + max_compression:
            break
        fc = forget_by_id.get(r.forgetting_candidate_id)
        expl = r.operator_explanation or build_review_required_explanation(r.reason, r.high_value_hint)
        items.append(ReviewPackItem(
            item_id=stable_id("item", r.candidate_id, prefix="rpi_"),
            kind="forgetting",
            candidate_id=r.forgetting_candidate_id,
            unit_ids=list(r.unit_ids),
            reason=r.reason,
            operator_explanation=expl,
            approved=None,
        ))

    # Unapplied compression (optional)
    if include_unapplied_compression:
        for c in comp_list:
            if c.applied:
                continue
            if len(items) >= max_forgetting + max_compression:
                break
            expl = c.operator_explanation or build_compressible_explanation(c.reason, c.item_count)
            items.append(ReviewPackItem(
                item_id=stable_id("item", c.candidate_id, prefix="rpi_"),
                kind="compression",
                candidate_id=c.candidate_id,
                unit_ids=list(c.unit_ids),
                reason=c.reason,
                operator_explanation=expl,
                approved=None,
            ))

    if not items:
        return None

    pack_id = stable_id("pack", utc_now_iso(), prefix="pack_")
    pack = ReviewPack(
        pack_id=pack_id,
        label=label or f"Review pack {pack_id}",
        items=items,
        created_at_utc=utc_now_iso(),
        reviewed_at_utc="",
        status="pending",
    )
    packs = load_review_packs(repo_root)
    packs.append(pack)
    save_review_packs(packs, repo_root)
    return pack


def get_review_pack(pack_id: str, repo_root=None) -> ReviewPack | None:
    """Return review pack by id or None."""
    for p in load_review_packs(repo_root):
        if p.pack_id == pack_id:
            return p
    return None


def list_review_packs(repo_root=None, *, status_filter: str = "") -> list[ReviewPack]:
    """List review packs, optionally filtered by status (pending | reviewed)."""
    packs = load_review_packs(repo_root)
    if status_filter:
        packs = [p for p in packs if p.status == status_filter]
    return packs


def record_review_decision(
    pack_id: str,
    item_id: str,
    approved: bool,
    repo_root=None,
) -> bool:
    """
    Record operator decision for one item in a pack. Updates the pack and, for forgetting items,
    updates review_required and forgetting candidate applied state. Returns True if found and updated.
    """
    packs = load_review_packs(repo_root)
    pack = None
    idx = -1
    for i, p in enumerate(packs):
        if p.pack_id == pack_id:
            pack = p
            idx = i
            break
    if not pack:
        return False

    for it in pack.items:
        if it.item_id != item_id:
            continue
        it.approved = approved
        if it.kind == "forgetting" and approved:
            review_list = load_review_required(repo_root)
            forget_list = load_forgetting_candidates(repo_root)
            for r in review_list:
                if r.forgetting_candidate_id == it.candidate_id:
                    r.reviewed = True
                    r.approved_for_forget = True
                    save_review_required(review_list, repo_root)
                    break
            for fc in forget_list:
                if fc.candidate_id == it.candidate_id:
                    fc.applied = True
                    save_forgetting_candidates(forget_list, repo_root)
                    break
        break
    else:
        return False

    # Mark pack reviewed if all items decided
    all_decided = all(it.approved is not None for it in pack.items)
    if all_decided:
        pack.status = "reviewed"
        pack.reviewed_at_utc = utc_now_iso()

    packs[idx] = pack
    save_review_packs(packs, repo_root)
    return True
