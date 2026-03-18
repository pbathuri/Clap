"""
M37E–M37H: Signal quality scoring.
Phase B: urgency vs usefulness separation, repeat/noise detection,
focus-safe suppression, stale-important resurfacing, role/mode calmness rules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.signal_quality.models import (
    SignalQualityScore,
    RepeatNoiseMarker,
    SuppressedQueueItem,
    ALWAYS_SHOW_PRIORITY,
    NEVER_SUPPRESS_SOURCES,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def score_queue_item(
    item: Any,
    context: dict[str, Any] | None = None,
) -> SignalQualityScore:
    """
    Score one unified queue item: urgency (never suppress if urgent tier),
    usefulness, noise (0 unless we have repeat data), interruption cost.
    """
    context = context or {}
    priority = getattr(item, "priority", "medium") or "medium"
    urgency_score = getattr(item, "urgency_score", 0.5)
    value_score = getattr(item, "value_score", 0.5)
    source = getattr(item, "source_subsystem", None)
    source_val = source.value if hasattr(source, "value") else str(source or "")
    actionability = getattr(item, "actionability_class", None)
    action_val = actionability.value if hasattr(actionability, "value") else str(actionability or "")

    is_urgent_tier = (
        (priority or "").lower() == "urgent"
        or action_val == "blocked"
        or source_val in NEVER_SUPPRESS_SOURCES
        or (action_val == "needs_approval")
    )
    urgency = 1.0 if is_urgent_tier else urgency_score
    usefulness = value_score
    noise = 0.0
    interruption_cost = 0.5
    if context.get("focus_mode_active"):
        interruption_cost = min(1.0, 0.3 + (1.0 - usefulness) * 0.7)
    reason = "urgent_tier" if is_urgent_tier else "ranked"
    return SignalQualityScore(
        urgency=urgency,
        usefulness=usefulness,
        noise_score=noise,
        interruption_cost=interruption_cost,
        is_urgent_tier=is_urgent_tier,
        reason=reason,
    )


def score_assist_suggestion(
    suggestion: Any,
    context: dict[str, Any] | None = None,
) -> SignalQualityScore:
    """Score one assist suggestion: urgency from type/confidence, usefulness, interruptiveness as cost."""
    context = context or {}
    usefulness = getattr(suggestion, "usefulness_score", 0.5)
    interruptiveness = getattr(suggestion, "interruptiveness_score", 0.5)
    confidence = getattr(suggestion, "confidence", 0.5)
    suggestion_type = getattr(suggestion, "suggestion_type", "") or ""

    is_urgent_tier = suggestion_type in ("blocked_review",) and confidence >= 0.8
    urgency = 0.9 if is_urgent_tier else (0.4 + confidence * 0.3)
    noise = 0.0
    reason = "blocked_review_high_confidence" if is_urgent_tier else "ranked"
    return SignalQualityScore(
        urgency=urgency,
        usefulness=usefulness,
        noise_score=noise,
        interruption_cost=interruptiveness,
        is_urgent_tier=is_urgent_tier,
        reason=reason,
    )


def is_repeat_noise(
    item_id: str,
    source: str,
    pattern_key: str,
    dismissed_patterns: list[dict[str, Any]],
    window_hours: int = 24,
) -> bool:
    """True if this pattern was recently dismissed (repeat)."""
    from datetime import datetime, timezone, timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).isoformat()
    recent = [d for d in dismissed_patterns if (d.get("dismissed_utc") or "") >= cutoff]
    keys = {(d.get("suggestion_type", ""), (d.get("reason_title") or "")[:60]) for d in recent}
    if pattern_key:
        return pattern_key in keys or any(pattern_key in str(k) for k in keys)
    return False


def eligible_resurfacing(
    item: Any,
    stale_rules: list[Any],
    now_utc: str = "",
) -> bool:
    """True if item qualifies for stale-but-important resurfacing."""
    if not now_utc:
        try:
            from workflow_dataset.utils.dates import utc_now_iso
            now_utc = utc_now_iso()
        except Exception:
            from datetime import datetime, timezone
            now_utc = datetime.now(timezone.utc).isoformat()
    created = getattr(item, "created_at", "") or getattr(item, "created_utc", "")
    if not created:
        return False
    try:
        from datetime import datetime, timezone
        ct = datetime.fromisoformat(created.replace("Z", "+00:00"))
        if ct.tzinfo is None:
            ct = ct.replace(tzinfo=timezone.utc)
        now = datetime.fromisoformat(now_utc.replace("Z", "+00:00"))
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        age_hours = (now - ct).total_seconds() / 3600
    except Exception:
        return False
    section = getattr(item, "section_id", "") or ""
    urgency_score = getattr(item, "urgency_score", 0)
    for rule in stale_rules:
        min_age = getattr(rule, "min_age_hours", 72)
        required = getattr(rule, "required_section_or_kind", ["blocked"])
        min_u = getattr(rule, "min_urgency_score", 0.5)
        if age_hours >= min_age and section in required and urgency_score >= min_u:
            return True
    return False


def rank_by_high_signal(
    items: list[Any],
    score_fn: Any,
    context: dict[str, Any] | None = None,
) -> list[Any]:
    """Sort items by signal quality: urgent first, then usefulness - noise - interruption_cost."""
    context = context or {}
    scored: list[tuple[float, Any]] = []
    for item in items:
        s = score_fn(item, context)
        composite = s.urgency * 2.0 - s.noise_score - s.interruption_cost * 0.5 + s.usefulness * 0.5
        if s.is_urgent_tier:
            composite += 10.0
        scored.append((composite, item))
    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored]
