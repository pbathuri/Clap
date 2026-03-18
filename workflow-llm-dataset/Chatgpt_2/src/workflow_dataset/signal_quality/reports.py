"""
M37E–M37H: Signal quality and calmness reports.
Phase D: Quality report, suppressions report, focus protection report, resurfacing report.
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

from workflow_dataset.signal_quality.models import SuppressedQueueItem, ProtectedFocusItem, StaleButImportantRule
from workflow_dataset.signal_quality.attention import get_protected_focus, digest_bundling_recommended


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_quality_report(
    repo_root: Path | str | None = None,
    queue_items: list[Any] | None = None,
    suppressed: list[SuppressedQueueItem] | None = None,
    top_high_signal_id: str = "",
) -> dict[str, Any]:
    """
    Single report: calmness score (0–1, higher = calmer), noise level, top high-signal item,
    suppressed count, focus protected, digest recommended.
    """
    root = _root(repo_root)
    now = utc_now_iso()
    suppressed = suppressed or []
    focus = get_protected_focus(root)
    queue_count = len(queue_items) if queue_items is not None else 0
    digest_rec = digest_bundling_recommended(queue_count)
    # Calmness: lower when many items + many suppressed + not digest recommended
    noise_level = min(1.0, (queue_count / 30.0) + (len(suppressed) / 20.0))
    calmness_score = max(0.0, 1.0 - noise_level * 0.7)
    if digest_rec["recommended"]:
        calmness_score *= 0.9  # slightly lower when overloaded
    return {
        "generated_at_utc": now,
        "calmness_score": round(calmness_score, 2),
        "noise_level": round(noise_level, 2),
        "queue_item_count": queue_count,
        "suppressed_count": len(suppressed),
        "top_high_signal_item_id": top_high_signal_id,
        "focus_protected_active": focus.active,
        "digest_recommended": digest_rec["recommended"],
        "digest_message": digest_rec.get("message", ""),
    }


def build_suppressions_report(
    suppressed: list[SuppressedQueueItem],
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Report of all suppressed items with reason and resurfacing eligibility."""
    now = utc_now_iso()
    by_reason: dict[str, int] = {}
    by_source: dict[str, int] = {}
    resurfacing_eligible: list[dict[str, Any]] = []
    for s in suppressed:
        by_reason[s.reason] = by_reason.get(s.reason, 0) + 1
        by_source[s.source] = by_source.get(s.source, 0) + 1
        if s.resurfacing_eligible:
            resurfacing_eligible.append({
                "item_id": s.item_id,
                "source": s.source,
                "reason": s.reason,
                "suppressed_at_utc": s.suppressed_at_utc,
                "explanation": getattr(s, "explanation", "") or "",
            })
    return {
        "generated_at_utc": now,
        "total_suppressed": len(suppressed),
        "by_reason": by_reason,
        "by_source": by_source,
        "resurfacing_eligible_count": len(resurfacing_eligible),
        "resurfacing_eligible": resurfacing_eligible[:50],
    }


def build_focus_protection_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Current focus protection state and interruption threshold."""
    root = _root(repo_root)
    focus = get_protected_focus(root)
    from workflow_dataset.signal_quality.attention import interruption_threshold_for_mode
    threshold = interruption_threshold_for_mode(focus.work_mode)
    return {
        "active": focus.active,
        "project_id": focus.project_id,
        "work_mode": focus.work_mode,
        "focus_mode_id": focus.focus_mode_id,
        "allow_urgent_only": focus.allow_urgent_only,
        "interruption_threshold": threshold,
        "message": "Focus protected; only urgent-tier items shown." if focus.active else "Focus not active.",
    }


def build_resurfacing_report(
    repo_root: Path | str | None = None,
    queue_items: list[Any] | None = None,
    stale_rules: list[Any] | None = None,
) -> dict[str, Any]:
    """Candidates for resurfacing (stale-but-important) with explanation."""
    from workflow_dataset.signal_quality.scoring import eligible_resurfacing
    from workflow_dataset.signal_quality.explain import explain_resurfaced
    now = utc_now_iso()
    stale_rules = stale_rules or []
    default_rule = StaleButImportantRule(
        rule_id="stale_blocked_3d",
        min_age_hours=72.0,
        required_section_or_kind=["blocked", "approval"],
        min_urgency_score=0.5,
        description="Blocked/approval older than 3 days",
    )
    if not stale_rules:
        stale_rules = [default_rule]
    candidates: list[dict[str, Any]] = []
    for item in (queue_items or []):
        if eligible_resurfacing(item, stale_rules, now):
            item_id = getattr(item, "item_id", "")
            section = getattr(item, "section_id", "")
            created = getattr(item, "created_at", "") or getattr(item, "created_utc", "")
            rule_name = stale_rules[0].rule_id if stale_rules else "default"
            explanation = explain_resurfaced(item_id=item_id, rule_name=rule_name, section_id=section, created_at=created)
            candidates.append({
                "item_id": item_id,
                "section_id": section,
                "created_at": created,
                "explanation": explanation,
            })
    return {
        "generated_at_utc": now,
        "resurfacing_candidates_count": len(candidates),
        "candidates": candidates[:30],
    }
