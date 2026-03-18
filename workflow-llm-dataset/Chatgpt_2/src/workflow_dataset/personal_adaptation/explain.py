"""
M31I–M31L: Explain a preference/style candidate: evidence, reasoning, affected surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.personal_adaptation.store import get_candidate


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def explain_preference(
    candidate_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Return operator-facing explanation for a preference or style candidate: evidence, reasoning, affected surface.
    """
    root = _repo_root(repo_root)
    cand = get_candidate(candidate_id, root)
    if not cand:
        return {"candidate_id": candidate_id, "error": "Candidate not found.", "evidence": [], "reasoning": "", "affected_surface": ""}
    evidence = list(cand.evidence) if hasattr(cand, "evidence") else []
    confidence = getattr(cand, "confidence", 0)
    source = getattr(cand, "source", "")
    affected_surface = getattr(cand, "affected_surface", "")
    key_or_pattern = getattr(cand, "key", None) or getattr(cand, "pattern_type", "")
    proposed = getattr(cand, "proposed_value", None) or getattr(cand, "description", "")
    reasoning = (
        f"Inferred from {source}. Confidence: {confidence:.2f}. "
        f"Affected surface: {affected_surface}. "
        f"If accepted, this will be applied as: {key_or_pattern} → {proposed}."
    )
    return {
        "candidate_id": candidate_id,
        "key_or_pattern": key_or_pattern,
        "proposed_value": proposed,
        "confidence": confidence,
        "evidence": evidence,
        "reasoning": reasoning,
        "affected_surface": affected_surface,
        "source": source,
        "source_reference_id": getattr(cand, "source_reference_id", ""),
        "review_status": getattr(cand, "review_status", "pending"),
    }


def format_explain_output(explain_dict: dict[str, Any]) -> str:
    """Format explain dict as human-readable text."""
    if explain_dict.get("error"):
        return f"Candidate {explain_dict.get('candidate_id', '')}: {explain_dict['error']}"
    lines = [
        f"# Preference / style candidate: {explain_dict.get('candidate_id', '')}",
        "",
        f"**Key/pattern:** {explain_dict.get('key_or_pattern', '')}",
        f"**Proposed value:** {explain_dict.get('proposed_value', '')}",
        f"**Confidence:** {explain_dict.get('confidence', 0):.2f}",
        f"**Affected surface:** {explain_dict.get('affected_surface', '')}",
        f"**Source:** {explain_dict.get('source', '')}",
        "",
        "## Evidence",
    ]
    for e in explain_dict.get("evidence", []):
        lines.append(f"  - {e}")
    lines.extend(["", "## Reasoning", explain_dict.get("reasoning", "")])
    return "\n".join(lines)
