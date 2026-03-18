"""
M29I–M29L: Build unified intervention inbox from approval queue, blocked runs, replan, skills, policy, stalled.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]

from workflow_dataset.review_studio.models import (
    InterventionItem,
    ITEM_APPROVAL_QUEUE,
    ITEM_BLOCKED_RUN,
    ITEM_REPLAN_RECOMMENDATION,
    ITEM_SKILL_CANDIDATE,
    ITEM_POLICY_EXCEPTION,
    ITEM_STALLED_INTERVENTION,
    ITEM_GRAPH_ROUTINE_CONFIRMATION,
    ITEM_GRAPH_PATTERN_REVIEW,
)
from workflow_dataset.review_studio.store import save_inbox_snapshot, load_operator_notes


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _items_from_approval_queue(root: Path) -> list[InterventionItem]:
    items: list[InterventionItem] = []
    try:
        from workflow_dataset.supervised_loop.store import load_queue
        queue = load_queue(root)
        for q in queue:
            if q.status != "pending":
                continue
            items.append(InterventionItem(
                item_id=stable_id("inbox", ITEM_APPROVAL_QUEUE, q.queue_id, prefix="inbox_"),
                kind=ITEM_APPROVAL_QUEUE,
                status="pending",
                summary=q.action.label[:80] if q.action.label else q.queue_id,
                created_at=q.action.created_at or utc_now_iso(),
                priority="high" if (q.action.risk_level or "").lower() == "high" else "medium",
                entity_refs={"queue_id": q.queue_id, "plan_ref": q.action.plan_ref},
                source_ref=q.queue_id,
            ))
    except Exception:
        pass
    return items


def _items_from_blocked_runs(root: Path) -> list[InterventionItem]:
    items: list[InterventionItem] = []
    try:
        from workflow_dataset.executor.hub import list_runs
        runs = list_runs(limit=30, repo_root=root)
        for r in runs:
            if r.get("status") != "blocked":
                continue
            run_id = r.get("run_id", "")
            items.append(InterventionItem(
                item_id=stable_id("inbox", ITEM_BLOCKED_RUN, run_id, prefix="inbox_"),
                kind=ITEM_BLOCKED_RUN,
                status="pending",
                summary=f"Run blocked: {run_id}",
                created_at=r.get("timestamp_start", "") or utc_now_iso(),
                priority="high",
                entity_refs={"run_id": run_id},
                source_ref=run_id,
            ))
    except Exception:
        pass
    return items


def _items_from_replan(root: Path) -> list[InterventionItem]:
    items: list[InterventionItem] = []
    try:
        from workflow_dataset.progress.board import build_progress_board
        board = build_progress_board(repo_root=root)
        replan_needed = board.get("replan_needed_projects") or []
        if not replan_needed:
            return items
        project_id = replan_needed[0]
        items.append(InterventionItem(
            item_id=stable_id("inbox", ITEM_REPLAN_RECOMMENDATION, project_id, utc_now_iso()[:10], prefix="inbox_"),
            kind=ITEM_REPLAN_RECOMMENDATION,
            status="pending",
            summary=f"Replan recommended: {project_id}",
            created_at=utc_now_iso(),
            priority="medium",
            entity_refs={"project_id": project_id},
            source_ref=project_id,
        ))
    except Exception:
        pass
    return items


def _items_from_skill_candidates(root: Path) -> list[InterventionItem]:
    items: list[InterventionItem] = []
    try:
        from workflow_dataset.teaching.review import list_candidate_skills
        skills = list_candidate_skills(status="draft", repo_root=root, limit=20)
        for s in skills:
            items.append(InterventionItem(
                item_id=stable_id("inbox", ITEM_SKILL_CANDIDATE, s.skill_id, prefix="inbox_"),
                kind=ITEM_SKILL_CANDIDATE,
                status="pending",
                summary=f"Skill draft: {s.skill_id}",
                created_at=s.created_at or utc_now_iso(),
                priority="low",
                entity_refs={"skill_id": s.skill_id},
                source_ref=s.skill_id,
            ))
    except Exception:
        pass
    return items


def _items_from_policy_overrides(root: Path) -> list[InterventionItem]:
    items: list[InterventionItem] = []
    try:
        from workflow_dataset.human_policy.board import list_overrides
        overrides = list_overrides(active_only=True, repo_root=root)
        for ov in overrides[:10]:
            items.append(InterventionItem(
                item_id=stable_id("inbox", ITEM_POLICY_EXCEPTION, ov.override_id, prefix="inbox_"),
                kind=ITEM_POLICY_EXCEPTION,
                status="pending",
                summary=f"Policy override: {ov.rule_key}={ov.rule_value} ({ov.scope}:{ov.scope_id})",
                created_at=ov.created_at or utc_now_iso(),
                priority="medium",
                entity_refs={"override_id": ov.override_id},
                source_ref=ov.override_id,
            ))
    except Exception:
        pass
    return items


def _items_from_stalled(root: Path) -> list[InterventionItem]:
    items: list[InterventionItem] = []
    try:
        from workflow_dataset.progress.board import build_progress_board
        board = build_progress_board(repo_root=root)
        candidate = board.get("next_intervention_candidate", "").strip()
        stalled = board.get("stalled_projects", [])
        if not candidate and stalled:
            candidate = stalled[0] if stalled else ""
        if not candidate:
            return items
        items.append(InterventionItem(
            item_id=stable_id("inbox", ITEM_STALLED_INTERVENTION, candidate, prefix="inbox_"),
            kind=ITEM_STALLED_INTERVENTION,
            status="pending",
            summary=f"Stalled project needs intervention: {candidate}",
            created_at=utc_now_iso(),
            priority="high",
            entity_refs={"project_id": candidate},
            source_ref=candidate,
        ))
    except Exception:
        pass
    return items


def _items_from_graph_review(root: Path) -> list[InterventionItem]:
    """M31H.1: Graph review inbox — suggested routines and uncertain patterns awaiting confirmation."""
    items: list[InterventionItem] = []
    try:
        from workflow_dataset.personal.graph_review_inbox import build_graph_review_inbox_items
        items = build_graph_review_inbox_items(repo_root=root, status="pending", limit=50)
    except Exception:
        pass
    return items


def build_inbox(
    repo_root: Path | str | None = None,
    status: str = "pending",
    limit: int = 100,
) -> list[InterventionItem]:
    """
    Build unified intervention inbox from approval queue, blocked runs, replan, skills, policy overrides, stalled.
    status='pending' returns only pending; status='' returns all. Sorted by priority (urgent/high first) then created_at.
    """
    root = _repo_root(repo_root)
    all_items: list[InterventionItem] = []
    all_items.extend(_items_from_approval_queue(root))
    all_items.extend(_items_from_blocked_runs(root))
    all_items.extend(_items_from_replan(root))
    all_items.extend(_items_from_skill_candidates(root))
    all_items.extend(_items_from_policy_overrides(root))
    all_items.extend(_items_from_stalled(root))
    all_items.extend(_items_from_graph_review(root))

    if status:
        all_items = [i for i in all_items if i.status == status]

    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    all_items.sort(key=lambda i: (priority_order.get(i.priority, 2), i.created_at or ""))
    out = all_items[:limit]

    notes = load_operator_notes(root)
    for i in out:
        if i.item_id in notes:
            i.operator_notes = notes[i.item_id]

    pending = [i for i in out if i.status == "pending"]
    oldest_id = pending[0].item_id if pending else ""
    next_id = oldest_id
    save_inbox_snapshot(len(pending), oldest_id, next_id, root)
    return out
