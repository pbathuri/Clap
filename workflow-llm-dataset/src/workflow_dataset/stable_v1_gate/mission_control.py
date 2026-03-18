"""
M50I–M50L: Mission-control slice — current stable-v1 recommendation, top blocker, narrow condition, evidence for/against, next action.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.stable_v1_gate.report import build_stable_v1_report
from workflow_dataset.stable_v1_gate.models import StableV1Report


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_stable_v1_gate_state(
    repo_root: Path | str | None = None,
    *,
    report: StableV1Report | None = None,
) -> dict[str, Any]:
    """
    Build mission-control slice for stable-v1 gate:
    - current_stable_v1_recommendation
    - top_final_blocker
    - narrow_v1_condition
    - strongest_evidence_for
    - strongest_evidence_against
    - next_required_final_action
    Optional report for testing to avoid full aggregation.
    """
    try:
        if report is None:
            root = _root(repo_root)
            report = build_stable_v1_report(root)
        gate = report.gate
        decision = report.decision

        top_blocker = ""
        if gate.blockers:
            top_blocker = gate.blockers[0].summary[:200]

        return {
            "current_stable_v1_recommendation": decision.recommendation,
            "current_stable_v1_recommendation_label": decision.recommendation_label,
            "top_final_blocker": top_blocker,
            "narrow_v1_condition": (decision.narrow_condition or "")[:200],
            "strongest_evidence_for": (decision.confidence_summary.strongest_evidence_for or "")[:200],
            "strongest_evidence_against": (decision.confidence_summary.strongest_evidence_against or "")[:200],
            "next_required_final_action": (decision.next_required_action or "")[:200],
            "gate_passed": gate.passed,
            "blocker_count": len(gate.blockers),
            "warning_count": len(gate.warnings),
        }
    except Exception as e:
        return {
            "error": str(e),
            "current_stable_v1_recommendation": "",
            "top_final_blocker": "",
            "narrow_v1_condition": "",
            "strongest_evidence_for": "",
            "strongest_evidence_against": "",
            "next_required_final_action": "workflow-dataset stable-v1 report",
        }
