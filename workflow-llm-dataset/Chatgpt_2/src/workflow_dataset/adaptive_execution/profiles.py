"""
M45D.1: Execution profiles — conservative, balanced, operator-heavy, review-heavy.
"""

from __future__ import annotations

from workflow_dataset.adaptive_execution.models import ExecutionProfile

PROFILE_CONSERVATIVE = "conservative"
PROFILE_BALANCED = "balanced"
PROFILE_OPERATOR_HEAVY = "operator_heavy"
PROFILE_REVIEW_HEAVY = "review_heavy"

_PROFILES: list[ExecutionProfile] = [
    ExecutionProfile(
        profile_id=PROFILE_CONSERVATIVE,
        label="Conservative",
        description="Low max steps, review before first step, simulate-first. Safest for unknown or high-stakes workflows.",
        max_steps_cap=5,
        review_every_n_steps=1,
        require_review_before_first_step=True,
        trust_mode="simulate_first",
        why_safe="Conservative profile caps steps at 5 and requires review before the first step and after every step; all execution is simulate-first unless explicitly approved.",
        when_blocked="Not blocked by profile; use when you want maximum control and minimal autonomous progression.",
    ),
    ExecutionProfile(
        profile_id=PROFILE_BALANCED,
        label="Balanced",
        description="Moderate max steps, checkpoints from plan only. Default for most workflows.",
        max_steps_cap=20,
        review_every_n_steps=0,
        require_review_before_first_step=False,
        trust_mode="approval_required",
        why_safe="Balanced profile uses the plan's own checkpoints and approval points; max steps are capped so the loop cannot run indefinitely.",
        when_blocked="Blocked if plan has no checkpoints and trust policy requires approval; add checkpoints or use a more permissive profile.",
    ),
    ExecutionProfile(
        profile_id=PROFILE_OPERATOR_HEAVY,
        label="Operator-heavy",
        description="Higher step cap, fewer mandatory reviews. For trusted operator-driven flows.",
        max_steps_cap=50,
        review_every_n_steps=0,
        require_review_before_first_step=False,
        trust_mode="trusted_bounded",
        why_safe="Operator-heavy profile allows more steps between reviews but remains bounded; intended for operators who have already approved the workflow scope.",
        when_blocked="Blocked when trust tier does not allow trusted_bounded or when policy requires more frequent review.",
    ),
    ExecutionProfile(
        profile_id=PROFILE_REVIEW_HEAVY,
        label="Review-heavy",
        description="Low step cap, review every step. For high-stakes or compliance-sensitive workflows.",
        max_steps_cap=10,
        review_every_n_steps=1,
        require_review_before_first_step=True,
        trust_mode="approval_required",
        why_safe="Review-heavy profile requires human review before the first step and after every step; max 10 steps so the loop cannot proceed without explicit operator approval at each step.",
        when_blocked="Not blocked by profile; use when every step must be approved (e.g. compliance, production changes).",
    ),
]


def list_profiles() -> list[ExecutionProfile]:
    """Return all execution profiles."""
    return list(_PROFILES)


def get_profile(profile_id: str) -> ExecutionProfile | None:
    """Return profile by id."""
    for p in _PROFILES:
        if p.profile_id == profile_id:
            return p
    return None


def get_profile_why_safe(profile_id: str) -> str:
    """Operator-facing: why this profile is safe to use."""
    p = get_profile(profile_id)
    if p:
        return p.why_safe or f"Profile {profile_id} applied."
    return f"Unknown profile {profile_id}."


def get_profile_when_blocked(profile_id: str) -> str:
    """Operator-facing: when this profile would be blocked or downgraded."""
    p = get_profile(profile_id)
    if p:
        return p.when_blocked or "See trust and policy settings."
    return "Unknown profile."
