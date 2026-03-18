"""
M44C: Retrieval explanation / traceability — why this memory was retrieved, evidence, confidence, weak warnings.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.memory_os.models import RetrievalExplanation


def build_explanation(
    retrieval_id: str,
    explanation: RetrievalExplanation,
    include_evidence: bool = True,
    include_weak: bool = True,
) -> dict[str, Any]:
    """Format explanation for CLI or reports. Includes profile_used and profile_reason when set (M44D.1)."""
    out: dict[str, Any] = {
        "retrieval_id": retrieval_id,
        "reason": explanation.reason,
        "confidence": explanation.confidence,
        "no_match_reason": explanation.no_match_reason or "",
    }
    if explanation.profile_used:
        out["profile_used"] = explanation.profile_used
    if explanation.profile_reason:
        out["profile_reason"] = explanation.profile_reason
    if include_evidence and explanation.evidence_bundle:
        out["evidence"] = {
            "total_count": explanation.evidence_bundle.total_count,
            "items": [i.to_dict() for i in explanation.evidence_bundle.items[:10]],
        }
    out["near_match_ids"] = explanation.near_match_ids[:5]
    if include_weak:
        out["weak_memory_warnings"] = explanation.weak_memory_warnings
    return out


def format_explanation_text(explanation: RetrievalExplanation) -> str:
    """Human-readable explanation text. Includes profile and why preferred when set (M44D.1)."""
    lines = [f"Reason: {explanation.reason}", f"Confidence: {explanation.confidence:.2f}"]
    if explanation.profile_used and explanation.profile_reason:
        lines.append(f"Profile: {explanation.profile_used} — {explanation.profile_reason}")
    elif explanation.profile_used:
        lines.append(f"Profile: {explanation.profile_used}")
    if explanation.no_match_reason:
        lines.append(f"No match: {explanation.no_match_reason}")
    if explanation.evidence_bundle and explanation.evidence_bundle.items:
        lines.append(f"Evidence: {len(explanation.evidence_bundle.items)} item(s)")
    if explanation.weak_memory_warnings:
        lines.append(f"Weak memory warnings: {len(explanation.weak_memory_warnings)}")
    return "\n".join(lines)
