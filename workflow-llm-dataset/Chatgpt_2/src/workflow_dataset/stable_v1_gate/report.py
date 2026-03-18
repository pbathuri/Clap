"""
M50I–M50L: Full stable-v1 report — evidence + gate + decision + explain.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.stable_v1_gate.models import (
    FinalEvidenceBundle,
    StableV1ReadinessGate,
    StableV1Decision,
    StableV1Report,
)
from workflow_dataset.stable_v1_gate.evidence import build_final_evidence_bundle
from workflow_dataset.stable_v1_gate.gate import evaluate_stable_v1_gate
from workflow_dataset.stable_v1_gate.decision import build_stable_v1_decision


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_stable_v1_report(
    repo_root: Path | str | None = None,
    *,
    evidence: FinalEvidenceBundle | None = None,
    gate: StableV1ReadinessGate | None = None,
) -> StableV1Report:
    """Build full stable-v1 report: evidence bundle, gate evaluation, final decision, and explain text. Optional evidence/gate for testing."""
    root = _root(repo_root)
    if evidence is None:
        evidence = build_final_evidence_bundle(root)
    if gate is None:
        gate = evaluate_stable_v1_gate(evidence=evidence, repo_root=root)
    decision = build_stable_v1_decision(evidence=evidence, gate=gate, repo_root=root)

    lines = [
        f"Stable v1 recommendation: {decision.recommendation_label} ({decision.recommendation})",
        f"Confidence: {decision.confidence_summary.confidence}",
        f"Rationale: {decision.confidence_summary.rationale}",
        f"Gate passed: {gate.passed}",
        f"Blockers: {len(gate.blockers)}",
        f"Warnings: {len(gate.warnings)}",
    ]
    if decision.narrow_condition:
        lines.append(f"Narrow condition: {decision.narrow_condition}")
    lines.append(f"Next required action: {decision.next_required_action}")
    explain = "\n".join(lines)

    return StableV1Report(
        evidence=evidence,
        gate=gate,
        decision=decision,
        explain=explain,
    )


def explain_stable_v1_decision(report: StableV1Report | None = None, repo_root: Path | str | None = None) -> str:
    """Human-readable explanation of the stable-v1 decision."""
    if report is None:
        report = build_stable_v1_report(repo_root)
    return report.explain
