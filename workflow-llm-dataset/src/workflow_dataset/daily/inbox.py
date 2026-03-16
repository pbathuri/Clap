"""
M23V / M23O: Daily inbox digest — work state summary, what changed, relevant jobs/routines,
blocked items (with reason/trust/mode/blockers/outcome), reminders, approvals, trust regressions,
recent runs, top next action. Local-only; no auto-execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


@dataclass
class DailyDigest:
    """Daily start-here digest for operator. M23O: adds created_at, what_changed, inbox_items, top_next."""
    created_at: str = ""
    work_state_snapshot_id: str = ""
    # What changed since last snapshot (M23O)
    what_changed: list[str] = field(default_factory=list)
    # Relevant work
    relevant_job_ids: list[str] = field(default_factory=list)
    relevant_routine_ids: list[str] = field(default_factory=list)
    # Inbox items with reason, trust, mode, blockers, expected outcome (M23O)
    inbox_items: list[dict[str, Any]] = field(default_factory=list)
    # Blocked
    blocked_items: list[dict[str, Any]] = field(default_factory=list)  # [{id, kind: job|routine, reason}]
    # Reminders
    reminders_due: list[dict[str, Any]] = field(default_factory=list)
    # Approvals
    approvals_needing_refresh: list[str] = field(default_factory=list)
    # Trust
    trust_regressions: list[str] = field(default_factory=list)
    # Recent success
    recent_successful_runs: list[dict[str, Any]] = field(default_factory=list)
    # Next action
    recommended_next_action: str = ""
    recommended_next_detail: str = ""
    # Top single next recommended action with explanation (M23O)
    top_next_recommended: dict[str, Any] = field(default_factory=dict)  # {label, reason, command, item_id, kind}
    # Optional domain-pack suggestions
    domain_pack_suggestions: list[str] = field(default_factory=list)
    # Unresolved corrections
    unresolved_corrections_count: int = 0
    corrections_review_recommended: list[str] = field(default_factory=list)
    # Errors from sources
    errors: list[str] = field(default_factory=list)


def _get_domain_pack_suggestions(repo_root: Path | None) -> list[str]:
    """Optional: return domain-pack-aware suggestions. Abstract interface; no hard dependency on Pane 2."""
    try:
        # If a provider is available (e.g. from registry), call it. Otherwise return [].
        from workflow_dataset.packs.pack_registry import get_installed_packs
        packs = get_installed_packs(repo_root or Path.cwd())
        if not packs:
            return []
        # Placeholder: could ask a specialization recipe interface for "suggested_next"
        return []
    except Exception:
        return []


def build_daily_digest(
    repo_root: Path | str | None = None,
    include_drift: bool = True,
) -> DailyDigest:
    """
    Build daily digest from local sources: copilot, work_context, corrections, desktop_bench, job_packs.
    M23O: adds created_at, what_changed (from context drift), inbox_items (reason/trust/mode/blockers/outcome), top_next_recommended.
    No network; read-only.
    """
    root = Path(repo_root).resolve() if repo_root else None
    digest = DailyDigest(created_at=utc_now_iso())

    # Optional: refresh work-state snapshot and compute drift (what changed)
    if include_drift and root:
        try:
            from workflow_dataset.context.work_state import build_work_state
            from workflow_dataset.context.snapshot import save_snapshot, load_snapshot
            from workflow_dataset.context.drift import compare_snapshots
            current_ws = build_work_state(root)
            digest.work_state_snapshot_id = getattr(current_ws, "snapshot_id", "") or (current_ws.created_at or "").replace(":", "")[:14]
            save_snapshot(current_ws, root)
            prev_ws = load_snapshot("previous", root)
            if prev_ws and current_ws:
                drift = compare_snapshots(prev_ws, current_ws)
                digest.what_changed = list(drift.summary)[:15]
        except Exception as e:
            digest.errors.append(f"drift: {e}")

    # Copilot: recommended jobs and routines; build inbox_items with reason, trust, mode, blockers, expected_outcome
    try:
        from workflow_dataset.copilot.recommendations import recommend_jobs
        from workflow_dataset.copilot.routines import list_routines
        from workflow_dataset.job_packs import get_job_pack
        recs = recommend_jobs(root, limit=20)
        routines = list_routines(root)
        digest.relevant_job_ids = [r["job_pack_id"] for r in recs if r.get("job_pack_id")][:15]
        digest.relevant_routine_ids = list(routines)[:10]
        for r in recs:
            job_id = r.get("job_pack_id", "")
            job = get_job_pack(job_id, root) if job_id else None
            expected_outcome = "Run job"
            if job:
                expected_outcome = (getattr(job, "title", "") or getattr(job, "description", "") or "Run job").strip() or "Run job"
                outs = getattr(job, "expected_outputs", None) or []
                if outs:
                    expected_outcome = (getattr(job, "title", "") or "Job") + ": " + ", ".join(str(o) for o in outs[:3])
            digest.inbox_items.append({
                "id": job_id,
                "kind": "job",
                "reason": r.get("reason", ""),
                "trust_level": r.get("trust_level", ""),
                "mode_available": r.get("mode_allowed", ""),
                "blockers": list(r.get("blocking_issues") or []),
                "expected_outcome": expected_outcome,
                "recommended_timing_context": r.get("recommended_timing_context", ""),
            })
            if r.get("blocking_issues"):
                digest.blocked_items.append({
                    "id": job_id,
                    "kind": "job",
                    "reason": "; ".join(r["blocking_issues"]) if isinstance(r["blocking_issues"], list) else str(r["blocking_issues"]),
                })
        for rid in digest.relevant_routine_ids[:10]:
            digest.inbox_items.append({
                "id": rid,
                "kind": "routine",
                "reason": "routine_available",
                "trust_level": "",
                "mode_available": "simulate",
                "blockers": [],
                "expected_outcome": f"Run routine {rid}",
                "recommended_timing_context": "any",
            })
    except Exception as e:
        digest.errors.append(f"copilot: {e}")

    # Reminders due
    try:
        from workflow_dataset.copilot.reminders import reminders_due
        digest.reminders_due = reminders_due(root, limit=20)
    except Exception as e:
        digest.errors.append(f"reminders: {e}")

    # Approvals needing refresh (approval-blocked jobs)
    try:
        from workflow_dataset.job_packs import job_packs_report
        report = job_packs_report(root)
        digest.approvals_needing_refresh = list(report.get("approval_blocked_jobs", []))[:20]
    except Exception as e:
        digest.errors.append(f"job_packs: {e}")

    # Trust regressions (desktop benchmark)
    try:
        from workflow_dataset.desktop_bench.board import board_report
        br = board_report(limit_runs=5, root=root)
        digest.trust_regressions = list(br.get("regressions", []))
    except Exception as e:
        digest.errors.append(f"desktop_bench: {e}")

    # Recent successful runs (plan runs + job recent_successful)
    try:
        from workflow_dataset.copilot.run import list_plan_runs
        from workflow_dataset.job_packs import job_packs_report
        runs = list_plan_runs(limit=5, repo_root=root)
        for r in runs:
            if r.get("executed") and not r.get("errors"):
                digest.recent_successful_runs.append({
                    "plan_run_id": r.get("plan_run_id"),
                    "mode": r.get("mode"),
                    "executed_count": r.get("executed_count", 0),
                    "timestamp": r.get("timestamp"),
                })
        report = job_packs_report(root)
        for rec in report.get("recent_successful", [])[:5]:
            if rec.get("job_pack_id") and not any(
                x.get("job_pack_id") == rec.get("job_pack_id") for x in digest.recent_successful_runs
            ):
                digest.recent_successful_runs.append({
                    "job_pack_id": rec.get("job_pack_id"),
                    "run_id": rec.get("run_id"),
                    "timestamp": rec.get("timestamp"),
                })
    except Exception as e:
        digest.errors.append(f"recent_runs: {e}")

    # Corrections: proposed / review recommended (before recommended_next_action)
    try:
        from workflow_dataset.corrections.eval_bridge import advisory_review_for_corrections
        from workflow_dataset.corrections.propose import propose_updates
        advisories = advisory_review_for_corrections(root, limit=20, min_count=2)
        proposed = propose_updates(root)
        digest.corrections_review_recommended = [a.get("job_or_routine_id") for a in advisories if a.get("job_or_routine_id")][:10]
        digest.unresolved_corrections_count = len(proposed) + len(digest.corrections_review_recommended)
    except Exception as e:
        digest.errors.append(f"corrections: {e}")

    # Recommended next action (reminders > blocked > corrections > copilot)
    if digest.reminders_due:
        digest.recommended_next_action = "Review reminders and run a routine or job"
        digest.recommended_next_detail = "copilot reminders due"
        r0 = digest.reminders_due[0]
        digest.top_next_recommended = {
            "label": r0.get("title") or r0.get("routine_id") or r0.get("job_pack_id") or "Reminder",
            "reason": "Reminder due",
            "command": "workflow-dataset copilot reminders (then run routine or job)",
            "item_id": r0.get("reminder_id", ""),
            "kind": "reminder",
        }
    elif digest.blocked_items:
        digest.recommended_next_action = "Resolve blocked jobs (approvals or policy)"
        digest.recommended_next_detail = "copilot recommend then jobs run or approvals"
        b0 = digest.blocked_items[0]
        digest.top_next_recommended = {
            "label": b0.get("id", ""),
            "reason": b0.get("reason", "Blocked"),
            "command": "workflow-dataset onboard approve or workflow-dataset jobs run --id " + str(b0.get("id", "")),
            "item_id": b0.get("id", ""),
            "kind": b0.get("kind", "job"),
        }
    elif digest.unresolved_corrections_count or digest.corrections_review_recommended:
        digest.recommended_next_action = "Review corrections and propose-updates"
        digest.recommended_next_detail = "corrections report"
        digest.top_next_recommended = {
            "label": "Corrections review",
            "reason": "Unresolved corrections or advisory review recommended",
            "command": "workflow-dataset corrections report",
            "item_id": "",
            "kind": "corrections",
        }
    elif digest.relevant_job_ids or digest.relevant_routine_ids:
        digest.recommended_next_action = "Run a recommended job or routine"
        digest.recommended_next_detail = "copilot recommend then copilot run --routine <id> or jobs run --id <id>"
        first_item = next((x for x in digest.inbox_items if not x.get("blockers")), None)
        if first_item:
            digest.top_next_recommended = {
                "label": first_item.get("id", ""),
                "reason": first_item.get("reason", ""),
                "command": f"workflow-dataset jobs run {first_item.get('id', '')} --mode simulate" if first_item.get("kind") == "job" else f"workflow-dataset copilot run --routine {first_item.get('id', '')}",
                "item_id": first_item.get("id", ""),
                "kind": first_item.get("kind", "job"),
            }
        else:
            digest.top_next_recommended = {"label": "Run recommended", "reason": "Jobs/routines available", "command": "workflow-dataset copilot recommend", "item_id": "", "kind": ""}
    else:
        digest.recommended_next_action = "Run setup or copilot recommend"
        digest.recommended_next_detail = "setup run or jobs seed then copilot recommend"
        digest.top_next_recommended = {"label": "Setup or recommend", "reason": "No recommendations yet", "command": "workflow-dataset onboard bootstrap; workflow-dataset copilot recommend", "item_id": "", "kind": ""}

    # Optional domain-pack suggestions
    digest.domain_pack_suggestions = _get_domain_pack_suggestions(root)

    return digest
