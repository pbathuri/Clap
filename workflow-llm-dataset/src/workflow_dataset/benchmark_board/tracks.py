"""
M42L.1: Promotion tracks — experimental-only, limited cohort, production-candidate.
"""

from __future__ import annotations

from workflow_dataset.benchmark_board.models import PromotionTrack

BUILTIN_PROMOTION_TRACKS: list[PromotionTrack] = [
    PromotionTrack(
        track_id="experimental_only",
        name="Experimental only",
        description="Candidate runs in experimental surfaces only; no production traffic.",
        order_index=0,
        required_previous_track_id="",
        gates_description="Benchmark compare pass or hold; no revert.",
    ),
    PromotionTrack(
        track_id="limited_cohort",
        name="Limited cohort",
        description="Candidate eligible for limited cohort rollout after shadow and gates.",
        order_index=1,
        required_previous_track_id="experimental_only",
        gates_description="Shadow-mode evaluation acceptable; scorecard recommend promote or hold; council optional.",
    ),
    PromotionTrack(
        track_id="production_candidate",
        name="Production candidate",
        description="Candidate eligible for production-safe route after limited cohort and gates.",
        order_index=2,
        required_previous_track_id="limited_cohort",
        gates_description="Sustained shadow comparison favorable; no regressions; operator approval.",
    ),
]


def get_track(track_id: str) -> PromotionTrack | None:
    for t in BUILTIN_PROMOTION_TRACKS:
        if t.track_id == track_id:
            return t
    return None


def list_track_ids() -> list[str]:
    return [t.track_id for t in sorted(BUILTIN_PROMOTION_TRACKS, key=lambda x: x.order_index)]


def scope_to_track_id(scope: str) -> str:
    """Map pipeline scope to track_id."""
    if scope == "experimental_only":
        return "experimental_only"
    if scope == "limited_cohort":
        return "limited_cohort"
    if scope == "production_safe":
        return "production_candidate"
    return "experimental_only"
