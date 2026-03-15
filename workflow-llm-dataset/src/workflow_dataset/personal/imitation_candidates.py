"""
Identify candidate domains/projects/patterns for future output imitation.

Does NOT generate final creative outputs. Produces structured records for the agent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ImitationCandidate(BaseModel):
    """A candidate for future style/output imitation."""

    candidate_id: str = Field(...)
    project_id: str = Field(default="")
    domain: str = Field(default="")
    candidate_type: str = Field(default="", description="e.g. report_style, spreadsheet_layout, export_naming, media_deliverable, project_organization")
    project_path: str = Field(default="")
    source_patterns: list[str] = Field(default_factory=list, description="Pattern or profile IDs that contributed")
    supporting_artifacts: list[str] = Field(default_factory=list, description="Paths or artifact refs")
    evidence: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    strength: float = Field(default=0.0, ge=0.0, le=1.0)  # alias for confidence_score
    description: str = Field(default="")
    notes: str = Field(default="")


def collect_candidates_from_profiles(profiles_dir: Path | str) -> list[ImitationCandidate]:
    """Build imitation candidates from existing style profiles."""
    from workflow_dataset.personal.style_profiles import load_style_profiles
    from workflow_dataset.utils.hashes import stable_id
    profiles = load_style_profiles(profiles_dir)
    candidates: list[ImitationCandidate] = []
    for p in profiles:
        if p.evidence_count < 2:
            continue
        cid = stable_id("candidate", p.profile_id, p.profile_type, prefix="cand")
        candidates.append(ImitationCandidate(
            candidate_id=cid,
            project_id=p.project_id or (p.project_paths[0] if p.project_paths else ""),
            domain=p.domain,
            candidate_type=p.profile_type,
            project_path=p.project_paths[0] if p.project_paths else "",
            source_patterns=[p.profile_id],
            supporting_artifacts=p.provenance_refs[:20],
            evidence=[str(s.get("value", s))[:100] for s in p.signals[:10]],
            confidence_score=p.confidence,
            strength=p.confidence,
            description=p.description,
        ))
    return candidates


def save_imitation_candidates(candidates: list[ImitationCandidate], out_path: Path | str) -> Path:
    """Write candidates to JSON (one file per session or run)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([c.model_dump() for c in candidates], f, indent=2)
    return out_path
