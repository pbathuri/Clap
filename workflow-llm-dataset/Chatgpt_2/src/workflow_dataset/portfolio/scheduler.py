"""
M28: Project scheduler — rank active projects, select next recommended, explain why.
Uses project_case (active projects, blockers), progress board (stalled, replan), loop (current), trust/readiness.
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

from workflow_dataset.portfolio.models import (
    Portfolio,
    PortfolioEntry,
    PortfolioHealth,
    ProjectPriority,
    UrgencyScore,
    ValueScore,
    BlockerSeverity,
    AttentionRecommendation,
    DeferRevisitState,
    PRIORITY_TIERS,
    BLOCKER_SEVERITY_LEVELS,
    PORTFOLIO_HEALTH_LABELS,
)
from workflow_dataset.portfolio.store import load_priority_hints, load_defer_revisit, get_deferred_project_ids


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _get_active_projects(repo_root: Path | str | None) -> list[dict[str, Any]]:
    """Active projects from project_case (source of truth)."""
    try:
        from workflow_dataset.project_case.store import list_projects
        return list_projects(repo_root=repo_root, state_filter="active", limit=50)
    except Exception:
        return []


def _get_project_summary(project_id: str, repo_root: Path | str | None) -> dict[str, Any] | None:
    try:
        from workflow_dataset.project_case.graph import get_project_summary
        return get_project_summary(project_id, repo_root)
    except Exception:
        return None


def _get_progress_board(repo_root: Path | str | None) -> dict[str, Any]:
    try:
        from workflow_dataset.progress.board import build_progress_board
        return build_progress_board(repo_root=repo_root)
    except Exception:
        return {
            "stalled_projects": [],
            "replan_needed_projects": [],
            "advancing_projects": [],
            "next_intervention_candidate": "",
            "project_health": {},
        }


def _get_current_project_id(repo_root: Path | str | None) -> str | None:
    try:
        from workflow_dataset.project_case.store import get_current_project_id
        return get_current_project_id(repo_root)
    except Exception:
        return None


def _get_cycle_project_slug(repo_root: Path | str | None) -> str | None:
    try:
        from workflow_dataset.supervised_loop.store import load_cycle
        cycle = load_cycle(repo_root)
        return cycle.project_slug if cycle else None
    except Exception:
        return None


def _compute_urgency(project_id: str, summary: dict[str, Any] | None, _board: dict) -> UrgencyScore:
    """Urgency: no deadline in project model yet; use updated_at recency or leave baseline."""
    # Placeholder: no deadline field in Project yet; could add later. Use 0.5 if replan_needed.
    reason = ""
    score = 0.3
    if summary:
        updated = summary.get("updated_at") or summary.get("project_state", {}).get("updated_at", "")
        if updated:
            reason = "Recently updated"
            score = 0.4
    return UrgencyScore(score=score, reason=reason or "No deadline set")


def _compute_value(
    project_id: str,
    summary: dict[str, Any] | None,
    board: dict,
    priority_hints: dict[str, str],
) -> ValueScore:
    """Value: operator hint + advancing/replan signal."""
    hint = priority_hints.get(project_id, "").lower()
    reason_parts = []
    score = 0.5
    if hint == "high":
        score = 0.9
        reason_parts.append("operator priority: high")
    elif hint == "medium":
        score = 0.6
        reason_parts.append("operator priority: medium")
    elif hint == "low":
        score = 0.3
        reason_parts.append("operator priority: low")
    if project_id in (board.get("advancing_projects") or []):
        score = min(1.0, score + 0.15)
        reason_parts.append("advancing")
    if project_id in (board.get("replan_needed_projects") or []):
        score = min(1.0, score + 0.1)
        reason_parts.append("replan needed")
    return ValueScore(
        score=score,
        operator_hint=hint or "",
        reason="; ".join(reason_parts) if reason_parts else "No hint",
    )


def _compute_blocker(project_id: str, summary: dict[str, Any] | None, board: dict) -> BlockerSeverity:
    """Blocked vs partial vs unblocked from project summary and progress."""
    blocked_goals_count = 0
    blocked_reason_summary = ""
    can_advance = True
    if summary and not summary.get("error"):
        state = summary.get("project_state") or {}
        blocked_goals_count = state.get("blocked_goals_count", 0)
        active = state.get("active_goals_count", 0)
        blocked_list = summary.get("blocked_goals", [])
        if blocked_list:
            blocked_reason_summary = "; ".join(
                (b.get("reason") or b.get("goal_id", ""))[:40] for b in blocked_list[:3]
            )
        can_advance = active > 0 and (active > blocked_goals_count or blocked_goals_count == 0)
    stalled = project_id in (board.get("stalled_projects") or [])
    if stalled:
        blocked_reason_summary = (blocked_reason_summary + "; stalled").strip("; ")
    if blocked_goals_count > 0 and not can_advance:
        level = "blocked"
    elif blocked_goals_count > 0 or stalled:
        level = "partial"
    elif can_advance:
        level = "unblocked"
    else:
        level = "unknown"
    return BlockerSeverity(
        level=level,
        blocked_goals_count=blocked_goals_count,
        blocked_reason_summary=blocked_reason_summary[:200],
        can_advance=can_advance,
    )


def _composite_score(priority: ProjectPriority, deferred_ids: set[str]) -> float:
    """Single number for ordering: urgency + value - blocker penalty. Deferred get large penalty."""
    if priority.project_id in deferred_ids:
        return -10.0
    u = priority.urgency.score
    v = priority.value.score
    b = priority.blocker
    blocker_penalty = 0.0
    if b.level == "blocked" and not b.can_advance:
        blocker_penalty = 0.5
    elif b.level == "partial":
        blocker_penalty = 0.2
    tier_boost = {"critical": 0.3, "high": 0.2, "medium": 0.0, "low": -0.1, "deferred": -0.5}.get(
        priority.tier, 0.0
    )
    return u + v - blocker_penalty + tier_boost


def rank_active_projects(repo_root: Path | str | None = None) -> list[ProjectPriority]:
    """
    Rank active projects by urgency, value, blockers, defer state.
    Returns list of ProjectPriority sorted by composite (best first).
    """
    root = _root(repo_root)
    active = _get_active_projects(root)
    if not active:
        return []
    board = _get_progress_board(root)
    priority_hints = load_priority_hints(root)
    deferred_ids = get_deferred_project_ids(root)
    current_id = _get_current_project_id(root)

    priorities: list[ProjectPriority] = []
    for p in active:
        project_id = p.get("project_id", "")
        if not project_id:
            continue
        summary = _get_project_summary(project_id, root)
        urgency = _compute_urgency(project_id, summary, board)
        value = _compute_value(project_id, summary, board, priority_hints)
        blocker = _compute_blocker(project_id, summary, board)
        tier = "high" if value.operator_hint == "high" else ("low" if value.operator_hint == "low" else "medium")
        if project_id in (board.get("stalled_projects") or []):
            tier = "high"  # intervention
        if project_id == current_id:
            tier = "high"
        pr = ProjectPriority(
            project_id=project_id,
            tier=tier,
            urgency=urgency,
            value=value,
            blocker=blocker,
            rank_index=0,
            composite_score=0.0,
        )
        pr.composite_score = _composite_score(pr, deferred_ids)
        priorities.append(pr)

    priorities.sort(key=lambda x: -x.composite_score)
    for i, pr in enumerate(priorities):
        pr.rank_index = i + 1
    return priorities


def get_next_recommended_project(repo_root: Path | str | None = None) -> AttentionRecommendation | None:
    """
    Best project to advance now: top of rank that is not fully blocked and is ready to execute
    or needs intervention. Prefer can_advance and ready; else top intervention.
    """
    root = _root(repo_root)
    ranked = rank_active_projects(root)
    board = _get_progress_board(root)
    intervention = (board.get("next_intervention_candidate") or "").strip()
    deferred_ids = get_deferred_project_ids(root)

    # First: best ranked that can_advance and is "ready" (unblocked or partial with work to do)
    for pr in ranked:
        if pr.project_id in deferred_ids:
            continue
        if pr.blocker.can_advance:
            return AttentionRecommendation(
                project_id=pr.project_id,
                reason=f"Rank #{pr.rank_index}; {pr.value.reason}; {pr.blocker.level}",
                action_hint="advance",
                priority_tier=pr.tier,
            )
    # Second: top intervention candidate if in ranked list
    if intervention:
        for pr in ranked:
            if pr.project_id == intervention and pr.project_id not in deferred_ids:
                return AttentionRecommendation(
                    project_id=pr.project_id,
                    reason=f"Intervention candidate; {pr.blocker.blocked_reason_summary or pr.value.reason}",
                    action_hint="intervene",
                    priority_tier=pr.tier,
                )
    # Third: just top of rank
    for pr in ranked:
        if pr.project_id not in deferred_ids:
            return AttentionRecommendation(
                project_id=pr.project_id,
                reason=f"Rank #{pr.rank_index}; {pr.urgency.reason}; {pr.value.reason}",
                action_hint="revisit" if pr.blocker.level == "blocked" else "advance",
                priority_tier=pr.tier,
            )
    return None


def explain_priority(project_id: str, repo_root: Path | str | None = None) -> str:
    """Human-readable explanation of why this project has its priority and rank."""
    root = _root(repo_root)
    ranked = rank_active_projects(root)
    pr = next((p for p in ranked if p.project_id == project_id), None)
    if not pr:
        return f"Project '{project_id}' not found in active portfolio or not ranked."
    lines = [
        f"Project: {project_id}",
        f"Rank: #{pr.rank_index} of {len(ranked)}",
        f"Tier: {pr.tier}",
        f"Composite score: {pr.composite_score:.2f}",
        "",
        "Urgency:",
        f"  score={pr.urgency.score:.2f}  {pr.urgency.reason or '—'}",
        "",
        "Value:",
        f"  score={pr.value.score:.2f}  {pr.value.reason or '—'}",
        "",
        "Blocker:",
        f"  level={pr.blocker.level}  can_advance={pr.blocker.can_advance}",
        f"  blocked_goals={pr.blocker.blocked_goals_count}",
    ]
    if pr.blocker.blocked_reason_summary:
        lines.append(f"  summary: {pr.blocker.blocked_reason_summary[:120]}")
    return "\n".join(lines)


def build_portfolio(repo_root: Path | str | None = None) -> Portfolio:
    """
    Build full portfolio: entries (ranked), health, next recommended, top intervention,
    most blocked, most valuable ready.
    """
    root = _root(repo_root)
    ranked = rank_active_projects(root)
    board = _get_progress_board(root)
    current_id = _get_current_project_id(root)
    deferred_list = load_defer_revisit(root)
    deferred_by_id = {d.project_id: d for d in deferred_list}

    stalled_set = set(board.get("stalled_projects") or [])
    replan_set = set(board.get("replan_needed_projects") or [])
    advancing_set = set(board.get("advancing_projects") or [])
    intervention = (board.get("next_intervention_candidate") or "").strip()
    health_per_project = board.get("project_health") or {}

    entries: list[PortfolioEntry] = []
    for pr in ranked:
        summary = _get_project_summary(pr.project_id, root)
        title = (summary.get("title") or pr.project_id) if summary else pr.project_id
        health_label = health_per_project.get(pr.project_id, "unknown")
        if health_label not in PORTFOLIO_HEALTH_LABELS:
            health_label = "stalled" if pr.project_id in stalled_set else ("blocked" if pr.blocker.level == "blocked" else "unknown")
        is_stalled = pr.project_id in stalled_set
        is_blocked = pr.blocker.level == "blocked" and not pr.blocker.can_advance
        is_ready = pr.blocker.can_advance and pr.blocker.level != "blocked"
        needs_intervention = pr.project_id == intervention or (is_stalled or (is_blocked and pr.blocker.blocked_goals_count > 0))
        deferred = deferred_by_id.get(pr.project_id)
        entry = PortfolioEntry(
            project_id=pr.project_id,
            title=title,
            state="active",
            priority=pr,
            health_label=health_label,
            is_current=(pr.project_id == current_id),
            is_stalled=is_stalled,
            is_blocked=is_blocked,
            is_ready_for_execution=is_ready,
            needs_intervention=needs_intervention,
            deferred=deferred,
        )
        entries.append(entry)

    # Health summary
    stalled_count = sum(1 for e in entries if e.is_stalled)
    blocked_count = sum(1 for e in entries if e.is_blocked)
    advancing_count = sum(1 for e in entries if e.project_id in advancing_set)
    ready_count = sum(1 for e in entries if e.is_ready_for_execution)
    intervention_count = sum(1 for e in entries if e.needs_intervention)
    labels = []
    if stalled_count:
        labels.append(f"{stalled_count} stalled")
    if blocked_count:
        labels.append(f"{blocked_count} blocked")
    if advancing_count:
        labels.append(f"{advancing_count} advancing")
    if ready_count:
        labels.append(f"{ready_count} ready")
    health = PortfolioHealth(
        total_active=len(entries),
        stalled_count=stalled_count,
        blocked_count=blocked_count,
        advancing_count=advancing_count,
        needs_intervention_count=intervention_count,
        ready_for_execution_count=ready_count,
        labels=labels,
    )

    next_rec = get_next_recommended_project(root)
    top_intervention = None
    if intervention:
        top_intervention = AttentionRecommendation(
            project_id=intervention,
            reason=next_rec.reason if next_rec and next_rec.project_id == intervention else "From progress board",
            action_hint="intervene",
            priority_tier="high",
        )
    most_blocked = ""
    for e in entries:
        if e.is_blocked and e.priority.blocker.blocked_goals_count > 0:
            most_blocked = e.project_id
            break
    most_valuable_ready = ""
    for e in entries:
        if e.is_ready_for_execution and e.priority.value.score >= 0.5:
            most_valuable_ready = e.project_id
            break

    return Portfolio(
        entries=entries,
        health=health,
        next_recommended_project=next_rec,
        top_intervention=top_intervention,
        most_blocked_project_id=most_blocked,
        most_valuable_ready_project_id=most_valuable_ready,
        updated_at_iso=utc_now_iso(),
    )
