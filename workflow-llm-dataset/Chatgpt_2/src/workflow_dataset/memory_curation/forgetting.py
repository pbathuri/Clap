"""
M44E–M44H Phase C: Forgetting candidate generation — from retention state, age, size; review-required tagging.
Does NOT apply forgetting; only produces candidates for review or policy-based application.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from workflow_dataset.memory_curation.models import ForgettingCandidate, ReviewRequiredDeletionCandidate
from workflow_dataset.memory_curation.explanations import (
    build_forgettable_explanation,
    build_review_required_explanation,
)
from workflow_dataset.memory_curation.retention import (
    get_default_policies,
    get_policy_by_id,
    retention_tier_requires_review,
    RETENTION_SHORT,
    RETENTION_MEDIUM,
    RETENTION_LONG,
    RETENTION_PROTECTED,
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
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _days_ago(ts: str) -> int | None:
    dt = _parse_iso(ts)
    if not dt:
        return None
    delta = datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)
    return max(0, delta.days)


def generate_forgetting_candidates(
    unit_entries: list[dict],
    *,
    created_at_key: str = "created_at_utc",
    unit_id_key: str = "unit_id",
    retention_tier_key: str = "retention_tier",
    source_key: str = "source",
    repo_root=None,
) -> tuple[list[ForgettingCandidate], list[ReviewRequiredDeletionCandidate]]:
    """
    From a list of unit-like dicts (with created_at_utc, unit_id, optional retention_tier/source),
    produce forgetting candidates and review-required deletion candidates.
    - Short-lived over 7 days -> safe forgetting candidate (review_required=False if policy says so).
    - Medium-term over 30 days or over cap -> forgetting candidate; review_required=True for long/protected.
    - Protected/long-term -> only ReviewRequiredDeletionCandidate, never auto-applied.
    """
    policies = {p.policy_id: p for p in get_default_policies()}
    short_policy = get_policy_by_id("short_lived")
    medium_policy = get_policy_by_id("medium_term")
    candidates: list[ForgettingCandidate] = []
    review_required: list[ReviewRequiredDeletionCandidate] = []

    for e in unit_entries:
        uid = e.get(unit_id_key) or ""
        created = e.get(created_at_key) or ""
        tier = e.get(retention_tier_key) or RETENTION_MEDIUM
        source = e.get(source_key) or "default"
        days = _days_ago(created)
        if days is None:
            continue

        if tier == RETENTION_PROTECTED:
            # Never auto-forget; only as review-required deletion candidate if operator explicitly asks
            continue

        if tier == RETENTION_SHORT and short_policy and days >= short_policy.max_age_days:
            cid = stable_id("forget", uid, created, prefix="forget_")
            reason = "expired_short_lived"
            fc = ForgettingCandidate(
                candidate_id=cid,
                unit_ids=[uid],
                reason=reason,
                created_at_utc=utc_now_iso(),
                review_required=False,
                applied=False,
                operator_explanation=build_forgettable_explanation(reason, tier, short_policy.label if short_policy else ""),
            )
            candidates.append(fc)

        elif tier == RETENTION_MEDIUM and medium_policy:
            if days >= medium_policy.max_age_days:
                cid = stable_id("forget", uid, created, prefix="forget_")
                reason = "policy_medium_term"
                fc = ForgettingCandidate(
                    candidate_id=cid,
                    unit_ids=[uid],
                    reason=reason,
                    created_at_utc=utc_now_iso(),
                    review_required=True,
                    applied=False,
                    operator_explanation=build_forgettable_explanation(reason, tier, medium_policy.label),
                )
                candidates.append(fc)
                review_required.append(ReviewRequiredDeletionCandidate(
                    candidate_id=stable_id("review", cid, prefix="review_"),
                    forgetting_candidate_id=cid,
                    unit_ids=[uid],
                    reason=reason,
                    high_value_hint=False,
                    created_at_utc=utc_now_iso(),
                    reviewed=False,
                    approved_for_forget=False,
                    operator_explanation=build_review_required_explanation(reason, False),
                ))

        elif tier == RETENTION_LONG:
            # Long-term: only propose as review-required if we ever want to suggest archival/forget
            pass

    # Cap by source (medium_term max_units_per_source): group by source, take oldest over cap
    if medium_policy and medium_policy.max_units_per_source > 0:
        by_source: dict[str, list[dict]] = {}
        for e in unit_entries:
            if e.get(retention_tier_key) not in (RETENTION_PROTECTED, RETENTION_LONG):
                src = e.get(source_key) or "default"
                by_source.setdefault(src, []).append(e)
        for src, entries in by_source.items():
            if len(entries) <= medium_policy.max_units_per_source:
                continue
            sorted_entries = sorted(entries, key=lambda x: x.get(created_at_key) or "")
            to_forget = sorted_entries[: len(sorted_entries) - medium_policy.max_units_per_source]
            for e in to_forget:
                uid = e.get(unit_id_key) or ""
                created = e.get(created_at_key) or ""
                cid = stable_id("forget", "cap", src, uid, prefix="forget_")
                if not any(c.unit_ids == [uid] for c in candidates):
                    reason = "max_units_per_source"
                    fc = ForgettingCandidate(
                        candidate_id=cid,
                        unit_ids=[uid],
                        reason=reason,
                        created_at_utc=utc_now_iso(),
                        review_required=True,
                        applied=False,
                        operator_explanation=build_forgettable_explanation(reason),
                    )
                    candidates.append(fc)
                    review_required.append(ReviewRequiredDeletionCandidate(
                        candidate_id=stable_id("review", cid, prefix="review_"),
                        forgetting_candidate_id=cid,
                        unit_ids=[uid],
                        reason=reason,
                        high_value_hint=False,
                        created_at_utc=utc_now_iso(),
                        reviewed=False,
                        approved_for_forget=False,
                        operator_explanation=build_review_required_explanation(reason, False),
                    ))

    return candidates, review_required
