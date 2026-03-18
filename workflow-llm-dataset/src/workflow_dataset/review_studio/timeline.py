"""
M29I–M29L: Build unified activity timeline from local sources.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.review_studio.models import (
    TimelineEvent,
    EVENT_ACTION_QUEUED,
    EVENT_ACTION_APPROVED,
    EVENT_ACTION_REJECTED,
    EVENT_ACTION_DEFERRED,
    EVENT_EXECUTOR_STARTED,
    EVENT_EXECUTOR_BLOCKED,
    EVENT_EXECUTOR_COMPLETED,
    EVENT_POLICY_OVERRIDE_APPLIED,
    EVENT_POLICY_OVERRIDE_REVOKED,
    EVENT_PROJECT_CREATED,
    EVENT_PROJECT_CHANGED,
    EVENT_SKILL_DRAFTED,
    EVENT_SKILL_ACCEPTED,
    EVENT_SKILL_REJECTED,
    EVENT_PLAN_REPLANNED,
)

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _load_queue_history(repo_root: Path) -> list[dict[str, Any]]:
    try:
        from workflow_dataset.supervised_loop.store import get_loop_dir
        path = get_loop_dir(repo_root) / "queue_history.json"
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("history", []))
    except Exception:
        return []


def _events_from_queue_and_history(root: Path) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    try:
        from workflow_dataset.supervised_loop.store import load_queue
        queue = load_queue(root)
        for q in queue:
            ts = (q.action.created_at or "")[:19]
            if not ts:
                continue
            if q.status == "pending":
                events.append(TimelineEvent(
                    event_id=stable_id("evt", EVENT_ACTION_QUEUED, q.queue_id, ts, prefix="evt_"),
                    kind=EVENT_ACTION_QUEUED,
                    timestamp_utc=ts,
                    summary=f"Action queued: {q.action.label[:60]}",
                    entity_refs={"queue_id": q.queue_id, "plan_ref": q.action.plan_ref},
                    plan_ref=q.action.plan_ref,
                    details={"queue_id": q.queue_id, "action_type": q.action.action_type, "risk_level": q.action.risk_level},
                ))
        history = _load_queue_history(root)
        for h in history:
            status = h.get("status", "")
            ts = (h.get("decided_at") or "")[:19]
            if not ts:
                continue
            kind = EVENT_ACTION_APPROVED if status == "approved" else EVENT_ACTION_REJECTED if status == "rejected" else EVENT_ACTION_DEFERRED
            events.append(TimelineEvent(
                event_id=stable_id("evt", kind, h.get("queue_id", ""), ts, prefix="evt_"),
                kind=kind,
                timestamp_utc=ts,
                summary=f"Action {status}: {h.get('queue_id', '')}",
                entity_refs={"queue_id": h.get("queue_id", "")},
                details={"note": h.get("note", "")},
            ))
    except Exception:
        pass
    return events


def _events_from_handoffs(root: Path) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    try:
        from workflow_dataset.supervised_loop.store import load_handoffs
        handoffs = load_handoffs(root)
        for h in handoffs:
            for ts_key, kind in [("started_at", EVENT_EXECUTOR_STARTED), ("ended_at", EVENT_EXECUTOR_COMPLETED)]:
                ts = (getattr(h, ts_key, "") or "")[:19]
                if not ts:
                    continue
                events.append(TimelineEvent(
                    event_id=stable_id("evt", kind, h.handoff_id, ts, prefix="evt_"),
                    kind=kind,
                    timestamp_utc=ts,
                    summary=f"Executor {kind.replace('executor_', '')}: {h.run_id}",
                    entity_refs={"run_id": h.run_id, "queue_id": h.queue_id},
                    run_id=h.run_id,
                    plan_ref=h.plan_ref,
                    details={"status": h.status, "outcome_summary": h.outcome_summary},
                ))
            if getattr(h, "status", "") == "blocked":
                ts = (getattr(h, "ended_at", "") or getattr(h, "started_at", ""))[:19]
                if ts:
                    events.append(TimelineEvent(
                        event_id=stable_id("evt", EVENT_EXECUTOR_BLOCKED, h.handoff_id, ts, prefix="evt_"),
                        kind=EVENT_EXECUTOR_BLOCKED,
                        timestamp_utc=ts,
                        summary=f"Executor blocked: {h.run_id}",
                        run_id=h.run_id,
                        details={"error": getattr(h, "error", "")},
                    ))
    except Exception:
        pass
    return events


def _events_from_executor_runs(root: Path) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    try:
        from workflow_dataset.executor.hub import list_runs
        runs = list_runs(limit=50, repo_root=root)
        for r in runs:
            ts = (r.get("timestamp_start") or "")[:19]
            if not ts:
                continue
            status = r.get("status", "")
            kind = EVENT_EXECUTOR_BLOCKED if status == "blocked" else EVENT_EXECUTOR_COMPLETED if status == "completed" else EVENT_EXECUTOR_STARTED
            events.append(TimelineEvent(
                event_id=stable_id("evt", kind, r.get("run_id", ""), ts, prefix="evt_"),
                kind=kind,
                timestamp_utc=ts,
                summary=f"Run {status}: {r.get('run_id', '')}",
                run_id=r.get("run_id", ""),
                plan_ref=r.get("plan_ref", ""),
                details={"mode": r.get("mode", "")},
            ))
    except Exception:
        pass
    return events


def _events_from_policy_overrides(root: Path) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    try:
        from workflow_dataset.human_policy.store import load_overrides
        overrides = load_overrides(root)
        for ov in overrides:
            ts = (ov.created_at or "")[:19]
            if ts:
                events.append(TimelineEvent(
                    event_id=stable_id("evt", EVENT_POLICY_OVERRIDE_APPLIED, ov.override_id, ts, prefix="evt_"),
                    kind=EVENT_POLICY_OVERRIDE_APPLIED,
                    timestamp_utc=ts,
                    summary=f"Policy override: {ov.rule_key}={ov.rule_value}",
                    entity_refs={"override_id": ov.override_id},
                    details={"scope": ov.scope, "scope_id": ov.scope_id},
                ))
            if ov.revoked_at:
                rts = (ov.revoked_at or "")[:19]
                if rts:
                    events.append(TimelineEvent(
                        event_id=stable_id("evt", EVENT_POLICY_OVERRIDE_REVOKED, ov.override_id, rts, prefix="evt_"),
                        kind=EVENT_POLICY_OVERRIDE_REVOKED,
                        timestamp_utc=rts,
                        summary=f"Policy override revoked: {ov.override_id}",
                        entity_refs={"override_id": ov.override_id},
                    ))
    except Exception:
        pass
    return events


def _events_from_projects(root: Path) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    try:
        from workflow_dataset.project_case.store import list_projects
        projects = list_projects(root)
        for p in projects:
            created = (getattr(p, "created_at", "") or "")[:19]
            if created:
                events.append(TimelineEvent(
                    event_id=stable_id("evt", EVENT_PROJECT_CREATED, p.project_id, created, prefix="evt_"),
                    kind=EVENT_PROJECT_CREATED,
                    timestamp_utc=created,
                    summary=f"Project created: {p.project_id}",
                    project_id=p.project_id,
                    entity_refs={"project_id": p.project_id},
                ))
            updated = (getattr(p, "updated_at", "") or "")[:19]
            if updated and updated != created:
                events.append(TimelineEvent(
                    event_id=stable_id("evt", EVENT_PROJECT_CHANGED, p.project_id, updated, prefix="evt_"),
                    kind=EVENT_PROJECT_CHANGED,
                    timestamp_utc=updated,
                    summary=f"Project updated: {p.project_id}",
                    project_id=p.project_id,
                ))
    except Exception:
        pass
    return events


def _events_from_skills(root: Path) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    try:
        from workflow_dataset.teaching.skill_store import list_skills
        skills = list_skills(repo_root=root, limit=100)
        for s in skills:
            created = (getattr(s, "created_at", "") or "")[:19]
            if created:
                events.append(TimelineEvent(
                    event_id=stable_id("evt", EVENT_SKILL_DRAFTED, s.skill_id, created, prefix="evt_"),
                    kind=EVENT_SKILL_DRAFTED,
                    timestamp_utc=created,
                    summary=f"Skill drafted: {s.skill_id}",
                    entity_refs={"skill_id": s.skill_id},
                    details={"status": getattr(s, "status", "")},
                ))
            accepted = (getattr(s, "accepted_at", "") or "")[:19]
            if accepted:
                events.append(TimelineEvent(
                    event_id=stable_id("evt", EVENT_SKILL_ACCEPTED, s.skill_id, accepted, prefix="evt_"),
                    kind=EVENT_SKILL_ACCEPTED,
                    timestamp_utc=accepted,
                    summary=f"Skill accepted: {s.skill_id}",
                    entity_refs={"skill_id": s.skill_id},
                ))
            rejected = (getattr(s, "rejected_at", "") or "")[:19]
            if rejected:
                events.append(TimelineEvent(
                    event_id=stable_id("evt", EVENT_SKILL_REJECTED, s.skill_id, rejected, prefix="evt_"),
                    kind=EVENT_SKILL_REJECTED,
                    timestamp_utc=rejected,
                    summary=f"Skill rejected: {s.skill_id}",
                    entity_refs={"skill_id": s.skill_id},
                ))
    except Exception:
        pass
    return events


def _events_from_replan(root: Path) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    try:
        from workflow_dataset.progress.store import load_replan_signals
        signals = load_replan_signals(root, limit=30)
        for sig in signals:
            ts = getattr(sig, "recorded_at", None) or getattr(sig, "timestamp", None) or ""
            if isinstance(ts, str):
                ts = ts[:19]
            else:
                ts = str(ts)[:19]
            if not ts:
                continue
            project_id = getattr(sig, "project_id", "") or ""
            events.append(TimelineEvent(
                event_id=stable_id("evt", EVENT_PLAN_REPLANNED, project_id, ts, prefix="evt_"),
                kind=EVENT_PLAN_REPLANNED,
                timestamp_utc=ts,
                summary=f"Replan signal: {getattr(sig, 'reason', '')[:50]}",
                project_id=project_id,
                entity_refs={"project_id": project_id},
                details={"reason": getattr(sig, "reason", "")},
            ))
    except Exception:
        pass
    return events


def build_timeline(
    repo_root: Path | str | None = None,
    project_id: str = "",
    limit: int = 80,
    since_iso: str = "",
) -> list[TimelineEvent]:
    """
    Build unified timeline from queue, handoffs, executor runs, policy overrides, projects, skills, replan.
    Sorted newest first. Optionally filter by project_id or since_iso.
    """
    import json
    root = _repo_root(repo_root)
    all_events: list[TimelineEvent] = []
    all_events.extend(_events_from_queue_and_history(root))
    all_events.extend(_events_from_handoffs(root))
    all_events.extend(_events_from_executor_runs(root))
    all_events.extend(_events_from_policy_overrides(root))
    all_events.extend(_events_from_projects(root))
    all_events.extend(_events_from_skills(root))
    all_events.extend(_events_from_replan(root))

    if project_id:
        all_events = [e for e in all_events if e.project_id == project_id]
    if since_iso:
        since = since_iso[:19]
        all_events = [e for e in all_events if e.timestamp_utc >= since]

    all_events.sort(key=lambda e: e.timestamp_utc or "", reverse=True)
    return all_events[:limit]


