"""
M38D.1: Cohort escalation and downgrade paths — explicit criteria to move from one cohort to another.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.cohort.models import (
    CohortTransition,
    TRANSITION_DOWNGRADE,
    TRANSITION_ESCALATION,
    TRIGGER_RELIABILITY_WORSENED,
    TRIGGER_TRIAGE_RECOMMEND_DOWNGRADE,
    TRIGGER_READINESS_MET,
    TRIGGER_MANUAL,
)
from workflow_dataset.cohort.profiles import (
    COHORT_INTERNAL_DEMO,
    COHORT_CAREFUL_FIRST_USER,
    COHORT_BOUNDED_OPERATOR_PILOT,
    COHORT_DOCUMENT_HEAVY_PILOT,
    COHORT_DEVELOPER_ASSIST_PILOT,
)

# Downgrade paths: when reliability or triage worsens -> move to narrower cohort
DOWNGRADE_TO_CAREFUL = CohortTransition(
    from_cohort_id="*",
    to_cohort_id=COHORT_CAREFUL_FIRST_USER,
    direction=TRANSITION_DOWNGRADE,
    trigger=TRIGGER_TRIAGE_RECOMMEND_DOWNGRADE,
    criteria_hint="Triage cohort health recommends downgrade (critical issue or should_downgrade).",
)
DOWNGRADE_RELIABILITY_TO_CAREFUL = CohortTransition(
    from_cohort_id="*",
    to_cohort_id=COHORT_CAREFUL_FIRST_USER,
    direction=TRANSITION_DOWNGRADE,
    trigger=TRIGGER_RELIABILITY_WORSENED,
    criteria_hint="Release readiness blocked or reliability run outcome blocked.",
)
# Escalation paths: when gates pass, can move to broader cohort
ESCALATE_CAREFUL_TO_BOUNDED = CohortTransition(
    from_cohort_id=COHORT_CAREFUL_FIRST_USER,
    to_cohort_id=COHORT_BOUNDED_OPERATOR_PILOT,
    direction=TRANSITION_ESCALATION,
    trigger=TRIGGER_READINESS_MET,
    criteria_hint="All readiness gates pass; no downgrade recommended; release not blocked.",
)
ESCALATE_CAREFUL_TO_DOCUMENT = CohortTransition(
    from_cohort_id=COHORT_CAREFUL_FIRST_USER,
    to_cohort_id=COHORT_DOCUMENT_HEAVY_PILOT,
    direction=TRANSITION_ESCALATION,
    trigger=TRIGGER_READINESS_MET,
    criteria_hint="All readiness gates pass; document-heavy workflow in scope.",
)
ESCALATE_BOUNDED_TO_DEVELOPER = CohortTransition(
    from_cohort_id=COHORT_BOUNDED_OPERATOR_PILOT,
    to_cohort_id=COHORT_DEVELOPER_ASSIST_PILOT,
    direction=TRANSITION_ESCALATION,
    trigger=TRIGGER_READINESS_MET,
    criteria_hint="All gates pass; operator and trust stable; developer assist in scope.",
)
# Manual transitions (for display only)
MANUAL_ANY_TO_INTERNAL_DEMO = CohortTransition(
    from_cohort_id="*",
    to_cohort_id=COHORT_INTERNAL_DEMO,
    direction=TRANSITION_ESCALATION,
    trigger=TRIGGER_MANUAL,
    criteria_hint="Internal demo only; manual selection.",
)

BUILTIN_TRANSITIONS: list[CohortTransition] = [
    DOWNGRADE_TO_CAREFUL,
    DOWNGRADE_RELIABILITY_TO_CAREFUL,
    ESCALATE_CAREFUL_TO_BOUNDED,
    ESCALATE_CAREFUL_TO_DOCUMENT,
    ESCALATE_BOUNDED_TO_DEVELOPER,
    MANUAL_ANY_TO_INTERNAL_DEMO,
]


def get_transitions_for_cohort(
    cohort_id: str,
    direction: str | None = None,
) -> list[CohortTransition]:
    """Return transitions that apply to this cohort (from or to). * matches any cohort."""
    out = []
    for t in BUILTIN_TRANSITIONS:
        if direction and t.direction != direction:
            continue
        if t.from_cohort_id == cohort_id or t.from_cohort_id == "*":
            out.append(t)
        if t.to_cohort_id == cohort_id and t.from_cohort_id != "*":
            out.append(t)
    return out


def get_recommended_transition(
    active_cohort_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any] | None:
    """
    Recommend a cohort transition based on current state: triage downgrade, release readiness, gates.
    Returns { suggested_cohort_id, direction, reason, trigger } or None if no change recommended.
    """
    if not active_cohort_id:
        return None
    root = Path(repo_root).resolve() if repo_root else None
    if not root:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()

    # 1. Downgrade: triage recommends downgrade -> careful_first_user
    try:
        from workflow_dataset.triage.health import build_cohort_health_summary
        health = build_cohort_health_summary(repo_root=root, cohort_id=active_cohort_id or "")
        if health.get("recommended_downgrade"):
            return {
                "suggested_cohort_id": COHORT_CAREFUL_FIRST_USER,
                "direction": TRANSITION_DOWNGRADE,
                "reason": health.get("recommended_mitigation", "Triage recommends downgrade."),
                "trigger": TRIGGER_TRIAGE_RECOMMEND_DOWNGRADE,
            }
        if health.get("highest_severity") == "critical":
            return {
                "suggested_cohort_id": COHORT_CAREFUL_FIRST_USER,
                "direction": TRANSITION_DOWNGRADE,
                "reason": "Critical triage issue; recommend downgrade to careful_first_user.",
                "trigger": TRIGGER_TRIAGE_RECOMMEND_DOWNGRADE,
            }
    except Exception:
        pass

    # 2. Downgrade: release readiness blocked
    try:
        from workflow_dataset.release_readiness import build_release_readiness
        from workflow_dataset.release_readiness.models import READINESS_BLOCKED
        status = build_release_readiness(root)
        if status.status == READINESS_BLOCKED:
            return {
                "suggested_cohort_id": COHORT_CAREFUL_FIRST_USER,
                "direction": TRANSITION_DOWNGRADE,
                "reason": "Release readiness is blocked; narrow scope to careful_first_user until resolved.",
                "trigger": TRIGGER_RELIABILITY_WORSENED,
            }
    except Exception:
        pass

    # 3. Escalation: if current is careful_first_user and all gates pass -> suggest bounded_operator_pilot
    if active_cohort_id == COHORT_CAREFUL_FIRST_USER:
        try:
            from workflow_dataset.cohort.gates import evaluate_gates
            results = evaluate_gates(active_cohort_id, root)
            if results and all(r.get("passed") for r in results):
                return {
                    "suggested_cohort_id": COHORT_BOUNDED_OPERATOR_PILOT,
                    "direction": TRANSITION_ESCALATION,
                    "reason": "All readiness gates pass; you can escalate to bounded_operator_pilot for operator and trust surfaces.",
                    "trigger": TRIGGER_READINESS_MET,
                }
        except Exception:
            pass

    return None
