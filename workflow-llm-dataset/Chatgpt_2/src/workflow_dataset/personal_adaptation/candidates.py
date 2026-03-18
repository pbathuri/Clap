"""
M31I–M31L: Generate preference and style pattern candidates from observed work, corrections, routines, teaching.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.personal_adaptation.models import (
    PreferenceCandidate,
    StylePatternCandidate,
    REVIEW_STATUS_PENDING,
    AFFECTED_SURFACES,
)

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:16]


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def generate_preference_candidates(
    repo_root: Path | str | None = None,
    limit_corrections: int = 50,
) -> list[PreferenceCandidate]:
    """
    Build preference candidates from: corrections (output_style, path preference, etc.),
    proposed updates, and optionally routines. Each candidate has key, proposed_value, confidence, evidence.
    """
    root = _repo_root(repo_root)
    ts = utc_now_iso()
    out: list[PreferenceCandidate] = []

    # From corrections: propose_updates already maps categories to target types
    try:
        from workflow_dataset.corrections.store import list_corrections
        from workflow_dataset.corrections.propose import propose_updates
        corrections = list_corrections(limit=limit_corrections, repo_root=root, eligible_only=True)
        proposed = propose_updates(repo_root=root, limit_corrections=limit_corrections)
        for p in proposed:
            if p.target_type == "specialization_output_style" and p.after_value:
                cid = stable_id("pref", "output_style", p.target_id, p.update_id, prefix="pref_")
                out.append(PreferenceCandidate(
                    candidate_id=cid,
                    key=f"output_style.{p.target_id}",
                    proposed_value=p.after_value,
                    confidence=0.75,
                    evidence=[f"Correction(s): {p.correction_ids}", p.reason],
                    source="corrections",
                    source_reference_id=p.correction_ids[0] if p.correction_ids else "",
                    affected_surface="specialization_output_style",
                    review_status=REVIEW_STATUS_PENDING,
                    created_utc=ts,
                    updated_utc=ts,
                ))
            if p.target_type == "specialization_paths" and p.after_value:
                cid = stable_id("pref", "paths", p.target_id, p.update_id, prefix="pref_")
                out.append(PreferenceCandidate(
                    candidate_id=cid,
                    key=f"paths.{p.target_id}",
                    proposed_value=p.after_value,
                    confidence=0.7,
                    evidence=[f"Correction(s): {p.correction_ids}", p.reason],
                    source="corrections",
                    source_reference_id=p.correction_ids[0] if p.correction_ids else "",
                    affected_surface="specialization_paths",
                    review_status=REVIEW_STATUS_PENDING,
                    created_utc=ts,
                    updated_utc=ts,
                ))
            if p.target_type == "specialization_params" and p.after_value:
                cid = stable_id("pref", "params", p.target_id, p.update_id, prefix="pref_")
                out.append(PreferenceCandidate(
                    candidate_id=cid,
                    key=f"params.{p.target_id}",
                    proposed_value=p.after_value,
                    confidence=0.7,
                    evidence=[f"Correction(s): {p.correction_ids}", p.reason],
                    source="corrections",
                    source_reference_id=p.correction_ids[0] if p.correction_ids else "",
                    affected_surface="specialization_params",
                    review_status=REVIEW_STATUS_PENDING,
                    created_utc=ts,
                    updated_utc=ts,
                ))
    except Exception:
        pass

    # From routines: pin project / workflow preference (lightweight)
    try:
        from workflow_dataset.personal.suggestion_engine import load_suggestions
        store_path = root / "data/local/personal/graph.db"
        suggestions = load_suggestions(store_path, status_filter="pending", limit=10) if store_path.parent.exists() else []
        for s in suggestions[:5]:
            if s.get("status", "pending") != "pending":
                continue
            sug_type = s.get("suggestion_type", "")
            if sug_type == "focus_project":
                proj = s.get("supporting_signals", [])
                proj_str = proj[0] if isinstance(proj, list) and proj else ""
                cid = stable_id("pref", "focus_project", s.get("suggestion_id", ""), prefix="pref_")
                out.append(PreferenceCandidate(
                    candidate_id=cid,
                    key="workspace.focus_project",
                    proposed_value=proj_str if isinstance(proj_str, str) else str(proj_str),
                    confidence=float(s.get("confidence_score", 0.7)),
                    evidence=s.get("supporting_signals", []) or [],
                    source="routines",
                    source_reference_id=s.get("suggestion_id", ""),
                    affected_surface="workspace_preset",
                    review_status=REVIEW_STATUS_PENDING,
                    created_utc=ts,
                    updated_utc=ts,
                ))
    except Exception:
        pass

    return out


def generate_style_candidates(
    repo_root: Path | str | None = None,
    profiles_dir: Path | str | None = None,
    max_per_type: int = 5,
) -> list[StylePatternCandidate]:
    """
    Build style pattern candidates from style profiles and imitation candidates.
    """
    root = _repo_root(repo_root)
    ts = utc_now_iso()
    out: list[StylePatternCandidate] = []

    if profiles_dir is None:
        profiles_dir = root / "data/local/personal/style_profiles"
    profiles_path = Path(profiles_dir)

    try:
        from workflow_dataset.personal.style_profiles import load_style_profiles
        from workflow_dataset.personal.imitation_candidates import collect_candidates_from_profiles
        profiles = load_style_profiles(profiles_path)
        for p in profiles[:max_per_type * 2]:
            if p.evidence_count < 1:
                continue
            cid = stable_id("style", p.profile_id, p.profile_type, prefix="style_")
            surface = "output_framing" if "naming" in p.profile_type or "export" in p.profile_type else "workspace_preset"
            out.append(StylePatternCandidate(
                candidate_id=cid,
                pattern_type=p.profile_type,
                description=p.description or f"Style: {p.profile_type}",
                evidence=[str(s.get("value", s))[:100] for s in p.signals[:5]] or p.naming_patterns[:5] or p.folder_patterns[:5],
                confidence=p.confidence,
                source="style_profile",
                source_reference_id=p.profile_id,
                affected_surface=surface,
                review_status=REVIEW_STATUS_PENDING,
                style_profile_ref=p.profile_id,
                created_utc=ts,
                updated_utc=ts,
            ))
        # Imitation candidates as style candidates
        imitations = collect_candidates_from_profiles(profiles_path)
        for im in imitations[:max_per_type]:
            cid = stable_id("style", "imitation", im.candidate_id, prefix="style_")
            out.append(StylePatternCandidate(
                candidate_id=cid,
                pattern_type=im.candidate_type or "imitation",
                description=im.description or im.candidate_type,
                evidence=im.evidence[:10],
                confidence=im.confidence_score,
                source="imitation_candidate",
                source_reference_id=im.candidate_id,
                affected_surface="output_framing",
                review_status=REVIEW_STATUS_PENDING,
                style_profile_ref=im.source_patterns[0] if im.source_patterns else "",
                created_utc=ts,
                updated_utc=ts,
            ))
    except Exception:
        pass

    return out
