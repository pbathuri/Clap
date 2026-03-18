"""
M34A–M34D: Trigger evaluation and matching to workflow definitions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.automations.models import (
    TriggerDefinition,
    TriggerKind,
    TriggerMatchResult,
    TriggerEvaluationSummary,
    RecurringWorkflowDefinition,
    GuardrailProfile,
    SuppressionRule,
)
from workflow_dataset.automations.store import (
    list_trigger_ids,
    get_trigger,
    list_workflow_ids,
    get_workflow,
    get_active_guardrail_profile,
)
from workflow_dataset.utils.dates import utc_now_iso


def _parse_utc(s: str) -> float:
    if not s:
        return 0.0
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return 0.0


def _apply_guardrail(
    trigger: TriggerDefinition,
    result: TriggerMatchResult,
    profile: GuardrailProfile | None,
    work_state: Any,
) -> None:
    """Apply active guardrail profile: allowed kinds and suppression rules. Mutates result."""
    if not profile or not result.matched:
        return
    if profile.allowed_trigger_kinds and trigger.kind.value not in profile.allowed_trigger_kinds:
        result.suppressed = True
        result.suppressed_reason = "Guardrail: trigger kind not in allowed list."
        result.matched = False
        return
    for rule in profile.suppression_rules or []:
        if rule.trigger_kind_filter and trigger.kind.value != rule.trigger_kind_filter:
            continue
        applied = False
        if rule.condition_type == "disabled":
            result.suppressed = True
            result.suppressed_reason = rule.reason or "Guardrail rule: disabled."
            result.matched = False
            applied = True
        elif rule.condition_type == "no_approval":
            if work_state and not getattr(work_state, "approvals_file_exists", False):
                if rule.action == "block":
                    result.blocked = True
                    result.blocked_reason = rule.reason or "Guardrail: approval required."
                else:
                    result.suppressed = True
                    result.suppressed_reason = rule.reason or "Guardrail: approval required."
                result.matched = False
                applied = True
        elif rule.condition_type == "exceeds_daily_cap":
            max_per_day = rule.params.get("max_per_day") or profile.max_recurring_per_day or 0
            if max_per_day and trigger.match_count >= max_per_day:
                result.suppressed = True
                result.suppressed_reason = rule.reason or f"Guardrail: daily cap ({max_per_day}) reached."
                result.matched = False
                applied = True
        if applied:
            return


def _evaluate_one_trigger(
    trigger: TriggerDefinition,
    work_state: Any,
    now_utc: str,
    repo_root: Path | str | None,
    guardrail_profile: GuardrailProfile | None = None,
) -> TriggerMatchResult:
    """Evaluate a single trigger; return match result with reason and blocked/suppressed."""
    now_ts = _parse_utc(now_utc)
    result = TriggerMatchResult(
        trigger_id=trigger.trigger_id,
        matched=False,
        reason="",
        blocked=False,
        suppressed=False,
        evaluated_at_utc=now_utc,
    )

    if not trigger.enabled:
        result.suppressed = True
        result.suppressed_reason = "Trigger is disabled."
        return result

    # Debounce: last_matched_utc + debounce_seconds
    if trigger.debounce_seconds > 0 and trigger.last_matched_utc:
        last_ts = _parse_utc(trigger.last_matched_utc)
        if now_ts - last_ts < trigger.debounce_seconds:
            result.suppressed = True
            result.suppressed_reason = f"Debounce: {trigger.debounce_seconds}s since last match."
            return result

    # Repeat limit per day (simplified: check match_count and reset at midnight not implemented; we allow)
    cond = trigger.condition or {}

    if trigger.kind == TriggerKind.TIME_BASED:
        # cron_expression or time_window (e.g. "09:00" or "morning")
        cron = cond.get("cron_expression", "")
        time_window = cond.get("time_window", "")
        if cron or time_window:
            result.matched = True
            result.reason = f"Time-based trigger (cron={cron or '—'} time_window={time_window or '—'})."
        else:
            result.reason = "Time-based trigger has no cron_expression or time_window; not matched."
    elif trigger.kind == TriggerKind.EVENT_BASED:
        event_type = cond.get("event_type", "manual")
        result.matched = event_type == "manual"
        result.reason = f"Event-based trigger (event_type={event_type}); matched for manual evaluation."
    elif trigger.kind == TriggerKind.PROJECT_STATE:
        want_project = cond.get("project_id", "")
        current = ""
        if work_state and hasattr(work_state, "current_project_id"):
            current = getattr(work_state, "current_project_id", "") or ""
        if want_project and current and want_project == current:
            result.matched = True
            result.reason = f"Project state match: project_id={want_project}."
        else:
            result.reason = f"Project state: want={want_project} current={current}; no match."
    elif trigger.kind == TriggerKind.IDLE_RESUME:
        idle_seconds = cond.get("idle_seconds", 0)
        if idle_seconds > 0:
            result.matched = True
            result.reason = f"Idle/resume trigger (idle_seconds>={idle_seconds}); consider matched when resume detected."
        else:
            result.reason = "Idle/resume trigger has no idle_seconds; not matched."
    elif trigger.kind == TriggerKind.APPROVAL_AVAILABLE:
        if work_state and getattr(work_state, "approvals_file_exists", False):
            result.matched = True
            result.reason = "Approval registry exists; approval_available matched."
        else:
            result.reason = "Approval registry not present; not matched."
    elif trigger.kind == TriggerKind.ARTIFACT_UPDATED:
        pattern = cond.get("artifact_pattern", "")
        if pattern:
            result.matched = True
            result.reason = f"Artifact-updated trigger (pattern={pattern}); matched when artifact path matches (evaluation is heuristic)."
        else:
            result.reason = "Artifact-updated trigger has no artifact_pattern; not matched."
    elif trigger.kind == TriggerKind.RECURRING_DIGEST:
        # e.g. daily at 08:00
        time_window = cond.get("time_window", "morning")
        result.matched = True
        result.reason = f"Recurring digest trigger (time_window={time_window}); matched for digest generation."
    else:
        result.reason = f"Trigger kind {trigger.kind} not evaluated; not matched."

    # Policy/trust: if required_policy_trust is approval_required and work_state says approval_blocked, set blocked
    if result.matched and trigger.required_policy_trust == "approval_required":
        if work_state and getattr(work_state, "approvals_file_exists", True) is False:
            result.blocked = True
            result.blocked_reason = "Trigger requires approval_required but approval registry missing."
            result.matched = False

    # M34D.1: Apply guardrail profile suppression rules (clearer trigger suppression)
    _apply_guardrail(trigger, result, guardrail_profile, work_state)

    return result


def evaluate_active_triggers(
    repo_root: Path | str | None = None,
    work_state: Any = None,
    now_utc: str | None = None,
) -> tuple[list[TriggerMatchResult], TriggerEvaluationSummary]:
    """
    Evaluate all defined triggers; return list of match results and summary.
    Does not persist last_matched_utc; caller may do that after confirming run.
    """
    now = now_utc or utc_now_iso()
    root = Path(repo_root).resolve() if repo_root else None
    profile = get_active_guardrail_profile(repo_root=root)
    trigger_ids = list_trigger_ids(repo_root=root)
    matches: list[TriggerMatchResult] = []
    active: list[str] = []
    suppressed: list[str] = []
    blocked: list[str] = []
    last_matched_id = ""
    last_matched_utc = ""

    for tid in trigger_ids:
        trigger = get_trigger(tid, repo_root=root)
        if not trigger:
            continue
        result = _evaluate_one_trigger(trigger, work_state, now, root, guardrail_profile=profile)
        result.workflow_id = _workflow_for_trigger(tid, root)
        matches.append(result)
        if result.matched and not result.blocked:
            active.append(tid)
            if trigger.last_matched_utc and (not last_matched_utc or trigger.last_matched_utc > last_matched_utc):
                last_matched_utc = trigger.last_matched_utc
                last_matched_id = tid
        elif result.suppressed:
            suppressed.append(tid)
        elif result.blocked:
            blocked.append(tid)

    next_wid = ""
    next_utc = ""
    for wid in list_workflow_ids(repo_root=root):
        w = get_workflow(wid, repo_root=root)
        if w and w.trigger_ids and w.enabled:
            for tid in w.trigger_ids:
                if tid in active:
                    next_wid = wid
                    next_utc = now
                    break
            if next_wid:
                break

    summary = TriggerEvaluationSummary(
        active_trigger_ids=active,
        suppressed_trigger_ids=suppressed,
        blocked_trigger_ids=blocked,
        last_matched_trigger_id=last_matched_id,
        last_matched_utc=last_matched_utc,
        next_scheduled_workflow_id=next_wid,
        next_scheduled_utc=next_utc,
        awaiting_review_workflow_ids=[],
        matches=matches,
    )
    return matches, summary


def _workflow_for_trigger(trigger_id: str, repo_root: Path | None) -> str:
    for wid in list_workflow_ids(repo_root=repo_root):
        w = get_workflow(wid, repo_root=repo_root)
        if w and trigger_id in (w.trigger_ids or []):
            return wid
    return ""


def explain_trigger_match(
    trigger_id: str,
    repo_root: Path | str | None = None,
    work_state: Any = None,
    now_utc: str | None = None,
) -> dict[str, Any]:
    """Explain why a trigger did or did not match. Operator-facing."""
    root = Path(repo_root).resolve() if repo_root else None
    trigger = get_trigger(trigger_id, repo_root=root)
    if not trigger:
        return {"trigger_id": trigger_id, "error": "trigger_not_found"}
    now = now_utc or utc_now_iso()
    profile = get_active_guardrail_profile(repo_root=root)
    result = _evaluate_one_trigger(trigger, work_state, now, root, guardrail_profile=profile)
    result.workflow_id = _workflow_for_trigger(trigger_id, root)
    return {
        "trigger_id": trigger_id,
        "label": trigger.label,
        "kind": trigger.kind.value,
        "enabled": trigger.enabled,
        "matched": result.matched,
        "reason": result.reason,
        "blocked": result.blocked,
        "blocked_reason": result.blocked_reason,
        "suppressed": result.suppressed,
        "suppressed_reason": result.suppressed_reason,
        "workflow_id": result.workflow_id,
        "evaluated_at_utc": result.evaluated_at_utc,
    }


def list_blocked_suppressed_triggers(
    repo_root: Path | str | None = None,
    work_state: Any = None,
) -> dict[str, list[dict[str, Any]]]:
    """List triggers that are blocked or suppressed with reasons."""
    _, summary = evaluate_active_triggers(repo_root=repo_root, work_state=work_state)
    blocked: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    root = Path(repo_root).resolve() if repo_root else None
    for m in summary.matches:
        if m.blocked:
            blocked.append({"trigger_id": m.trigger_id, "reason": m.blocked_reason})
        if m.suppressed:
            suppressed.append({"trigger_id": m.trigger_id, "reason": m.suppressed_reason})
    return {"blocked": blocked, "suppressed": suppressed}


def match_triggers_to_workflows(
    matched_trigger_ids: list[str],
    repo_root: Path | str | None = None,
) -> list[tuple[str, str]]:
    """Return list of (trigger_id, workflow_id) for matched triggers that are tied to a workflow."""
    root = Path(repo_root).resolve() if repo_root else None
    out: list[tuple[str, str]] = []
    for tid in matched_trigger_ids:
        wid = _workflow_for_trigger(tid, root)
        if wid:
            out.append((tid, wid))
    return out
