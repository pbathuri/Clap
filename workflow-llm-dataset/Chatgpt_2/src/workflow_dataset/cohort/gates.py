"""
M38D.1: Readiness gates per cohort — explicit criteria that must pass for a cohort to be considered ready.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.cohort.models import (
    GATE_SOURCE_RELEASE_READINESS,
    GATE_SOURCE_TRIAGE,
    GATE_SOURCE_RELIABILITY,
    ReadinessGate,
)
from workflow_dataset.cohort.profiles import (
    COHORT_CAREFUL_FIRST_USER,
    COHORT_BOUNDED_OPERATOR_PILOT,
    COHORT_DEVELOPER_ASSIST_PILOT,
    get_cohort_profile,
)

# Built-in gates (applies to cohorts that require readiness)
GATE_RELEASE_NOT_BLOCKED = ReadinessGate(
    gate_id="release_not_blocked",
    label="Release not blocked",
    description="Release readiness status is not blocked.",
    check_source=GATE_SOURCE_RELEASE_READINESS,
    required_value="ready_or_degraded",
    cohort_ids=[],
)
GATE_NO_CRITICAL_TRIAGE = ReadinessGate(
    gate_id="no_critical_triage",
    label="No critical triage issues",
    description="No critical-severity open triage issues for cohort.",
    check_source=GATE_SOURCE_TRIAGE,
    required_value="no_critical",
    cohort_ids=[],
)
GATE_NO_DOWNGRADE_RECOMMENDED = ReadinessGate(
    gate_id="no_downgrade_recommended",
    label="Triage does not recommend downgrade",
    description="Cohort health does not recommend downgrade.",
    check_source=GATE_SOURCE_TRIAGE,
    required_value="no_downgrade",
    cohort_ids=[],
)
GATE_RELIABILITY_PASS_OR_NA = ReadinessGate(
    gate_id="reliability_pass_or_na",
    label="Reliability not blocked",
    description="Golden path reliability is pass or degraded (not blocked).",
    check_source=GATE_SOURCE_RELIABILITY,
    required_value="pass_or_degraded",
    cohort_ids=[],
)

BUILTIN_GATES: list[ReadinessGate] = [
    GATE_RELEASE_NOT_BLOCKED,
    GATE_NO_CRITICAL_TRIAGE,
    GATE_NO_DOWNGRADE_RECOMMENDED,
    GATE_RELIABILITY_PASS_OR_NA,
]


def get_gates_for_cohort(cohort_id: str) -> list[ReadinessGate]:
    """Return gates that apply to this cohort (all built-in if cohort has required_readiness)."""
    profile = get_cohort_profile(cohort_id)
    if not profile:
        return []
    if profile.required_readiness == "any":
        return []
    return list(BUILTIN_GATES)


def evaluate_gates(
    cohort_id: str,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """
    Evaluate readiness gates for this cohort. Returns list of { gate_id, passed, message }.
    """
    gates = get_gates_for_cohort(cohort_id)
    root = Path(repo_root).resolve() if repo_root else None
    if not root:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()

    results: list[dict[str, Any]] = []
    for g in gates:
        passed = False
        message = ""
        try:
            if g.check_source == GATE_SOURCE_RELEASE_READINESS:
                from workflow_dataset.release_readiness import build_release_readiness
                from workflow_dataset.release_readiness.models import READINESS_BLOCKED
                status = build_release_readiness(root)
                if g.required_value == "ready_or_degraded":
                    passed = status.status != READINESS_BLOCKED
                    message = f"Release readiness status={status.status}"
                else:
                    passed = status.status != READINESS_BLOCKED
                    message = status.status
            elif g.check_source == GATE_SOURCE_TRIAGE:
                from workflow_dataset.triage.health import build_cohort_health_summary
                health = build_cohort_health_summary(repo_root=root, cohort_id=cohort_id or "")
                if g.required_value == "no_critical":
                    passed = health.get("highest_severity") != "critical"
                    message = f"Highest severity={health.get('highest_severity', 'none')}"
                elif g.required_value == "no_downgrade":
                    passed = not health.get("recommended_downgrade", False)
                    message = "recommended_downgrade=" + str(health.get("recommended_downgrade", False))
                else:
                    passed = not health.get("recommended_downgrade", False)
                    message = str(health.get("recommended_mitigation", ""))[:80]
            elif g.check_source == GATE_SOURCE_RELIABILITY:
                # Optional: integrate reliability store if available; default pass if not run
                passed = True
                message = "Reliability check not run (pass by default)"
                try:
                    from workflow_dataset.reliability.store import list_runs
                    summaries = list_runs(root, limit=1)
                    if summaries and summaries[0].get("outcome") == "blocked":
                        passed = False
                        message = "Latest reliability run outcome=blocked"
                    elif summaries:
                        message = f"Latest outcome={summaries[0].get('outcome', 'unknown')}"
                except Exception:
                    pass
            else:
                message = f"Unknown check_source={g.check_source}"
        except Exception as e:
            message = str(e)[:100]
        results.append({"gate_id": g.gate_id, "label": g.label, "passed": passed, "message": message})
    return results
