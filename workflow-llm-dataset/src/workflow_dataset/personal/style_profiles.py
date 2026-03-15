"""
Aggregate extracted style signatures into style profiles for future imitation.

Does NOT generate final creative outputs. Produces structured records the future agent can use.
M5: extended with pattern lists, session/project refs, and build from style signals.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


class StyleProfile(BaseModel):
    """Aggregated style profile for a domain or project."""

    profile_id: str = Field(..., description="Stable id")
    profile_type: str = Field(default="", description="e.g. naming_style, folder_structure_style, document_template_style")
    domain: str = Field(default="", description="creative, design, finance, ops, etc.")
    evidence_count: int = Field(default=0)
    signals: list[dict[str, Any]] = Field(default_factory=list)
    description: str = Field(default="")
    project_paths: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    # Extended for M5 assistive loop
    session_id: str = Field(default="")
    project_id: str = Field(default="", description="Primary project context")
    style_family: str = Field(default="", description="e.g. naming, folder, export, spreadsheet")
    naming_patterns: list[str] = Field(default_factory=list)
    folder_patterns: list[str] = Field(default_factory=list)
    artifact_bundle_patterns: list[str] = Field(default_factory=list)
    export_patterns: list[str] = Field(default_factory=list)
    spreadsheet_patterns: list[str] = Field(default_factory=list)
    document_template_patterns: list[str] = Field(default_factory=list)
    repeated_structure_patterns: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")


def aggregate_naming_style(signals: list[dict[str, Any]]) -> StyleProfile | None:
    """Build a naming_style profile from revision/export naming signals."""
    if not signals:
        return None
    ids = [str(s.get("value") or s.get("pattern_type", "")) for s in signals[:10]]
    profile_id = stable_id("style", "naming", *ids, prefix="profile")
    ts = utc_now_iso()
    naming = [str(s.get("value", "")) for s in signals if s.get("value")][:20]
    return StyleProfile(
        profile_id=profile_id,
        profile_type="naming_style",
        style_family="naming",
        domain=signals[0].get("domain", ""),
        evidence_count=len(signals),
        signals=signals[:50],
        description="Revision/export naming patterns observed",
        confidence=min(0.9, 0.3 + 0.05 * len(signals)),
        naming_patterns=naming,
        provenance_refs=sum([s.get("evidence_paths", []) for s in signals[:5] if s.get("evidence_paths")], [])[:20],
        created_utc=ts,
        updated_utc=ts,
    )


def aggregate_folder_structure_style(signals: list[dict[str, Any]]) -> StyleProfile | None:
    """Build folder_structure_style profile from folder layout signals."""
    if not signals:
        return None
    profile_id = stable_id("style", "folder", str(signals[0].get("value", ""))[:50], prefix="profile")
    ts = utc_now_iso()
    folder = [str(s.get("value", "")) for s in signals if s.get("value")][:15]
    return StyleProfile(
        profile_id=profile_id,
        profile_type="folder_structure_style",
        style_family="folder",
        domain=signals[0].get("domain", ""),
        evidence_count=len(signals),
        signals=signals[:30],
        description="Recurring folder layout patterns",
        confidence=0.5 + 0.05 * min(len(signals), 5),
        folder_patterns=folder,
        created_utc=ts,
        updated_utc=ts,
    )


def save_style_profile(profile: StyleProfile, out_dir: Path | str) -> Path:
    """Persist a style profile to JSON under out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{profile.profile_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        f.write(profile.model_dump_json(indent=2))
    return path


def load_style_profiles(profiles_dir: Path | str) -> list[StyleProfile]:
    """Load all style profiles from a directory."""
    profiles_dir = Path(profiles_dir)
    if not profiles_dir.exists():
        return []
    out = []
    for path in profiles_dir.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                out.append(StyleProfile.model_validate_json(f.read()))
        except Exception:
            continue
    return out


def build_profiles_from_style_signals(
    style_signal_records: list[Any],
    session_id: str = "",
    project_id: str = "",
) -> list[StyleProfile]:
    """
    Build style profiles from persisted style signal records (e.g. from load_style_signals).
    Groups by pattern_type and aggregates naming, folder, export, spreadsheet patterns.
    """
    from workflow_dataset.setup.style_persistence import StyleSignalRecord
    profiles: list[StyleProfile] = []
    ts = utc_now_iso()
    by_type: dict[str, list[dict[str, Any]]] = {}
    for rec in style_signal_records:
        if isinstance(rec, StyleSignalRecord):
            d = rec.model_dump()
        else:
            d = rec if isinstance(rec, dict) else {}
        pt = d.get("pattern_type") or "unknown"
        by_type.setdefault(pt, []).append(d)
    for pattern_type, group in by_type.items():
        if len(group) < 1:
            continue
        if pattern_type in ("naming_convention", "revision_pattern", "export_pattern"):
            p = aggregate_naming_style(group)
            if p:
                p.session_id = session_id
                p.project_id = project_id
                p.export_patterns = [str(g.get("value", "")) for g in group if g.get("value")][:15]
                profiles.append(p)
        elif pattern_type in ("folder_layout", "folder_structure"):
            p = aggregate_folder_structure_style(group)
            if p:
                p.session_id = session_id
                p.project_id = project_id
                profiles.append(p)
        elif pattern_type == "spreadsheet_schema":
            profile_id = stable_id("style", "spreadsheet", session_id, str(len(group)), prefix="profile")
            profiles.append(StyleProfile(
                profile_id=profile_id,
                profile_type="spreadsheet_schema_style",
                style_family="spreadsheet",
                domain=group[0].get("domain", "tabular"),
                evidence_count=len(group),
                signals=group[:30],
                description="Recurring spreadsheet schema patterns",
                spreadsheet_patterns=[str(g.get("value", ""))[:200] for g in group if g.get("value")][:10],
                confidence=min(0.85, 0.4 + 0.05 * len(group)),
                session_id=session_id,
                project_id=project_id,
                created_utc=ts,
                updated_utc=ts,
            ))
    return profiles
