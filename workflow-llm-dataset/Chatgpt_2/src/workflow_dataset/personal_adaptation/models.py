"""
M31I–M31L: Preference/style candidates and accepted updates. Explicit, reviewable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

REVIEW_STATUS_PENDING = "pending"
REVIEW_STATUS_ACCEPTED = "accepted"
REVIEW_STATUS_DISMISSED = "dismissed"

AFFECTED_SURFACES = (
    "pack_defaults",
    "output_framing",
    "workspace_preset",
    "suggested_actions",
    "notification_style",
    "planning_style",
    "specialization_params",
    "specialization_paths",
    "specialization_output_style",
)


@dataclass
class PreferenceCandidate:
    """A single user preference candidate inferred from work/feedback; reviewable."""
    candidate_id: str
    key: str  # e.g. ui.theme, execution.require_confirm, output_style.bullet_preference
    proposed_value: str | bool | int | list[str]
    confidence: float  # 0..1
    evidence: list[str] = field(default_factory=list)
    source: str = ""  # corrections | routines | style_profile | teaching
    source_reference_id: str = ""
    affected_surface: str = ""  # one of AFFECTED_SURFACES
    review_status: str = REVIEW_STATUS_PENDING
    created_utc: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "key": self.key,
            "proposed_value": self.proposed_value,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "source": self.source,
            "source_reference_id": self.source_reference_id,
            "affected_surface": self.affected_surface,
            "review_status": self.review_status,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PreferenceCandidate:
        return cls(
            candidate_id=str(d.get("candidate_id", "")),
            key=str(d.get("key", "")),
            proposed_value=d.get("proposed_value"),
            confidence=float(d.get("confidence", 0)),
            evidence=list(d.get("evidence", [])),
            source=str(d.get("source", "")),
            source_reference_id=str(d.get("source_reference_id", "")),
            affected_surface=str(d.get("affected_surface", "")),
            review_status=str(d.get("review_status", REVIEW_STATUS_PENDING)),
            created_utc=str(d.get("created_utc", "")),
            updated_utc=str(d.get("updated_utc", "")),
        )


@dataclass
class StylePatternCandidate:
    """A style pattern candidate (naming, folder, output style) from observed work; reviewable."""
    candidate_id: str
    pattern_type: str  # e.g. naming_style, folder_structure, output_style
    description: str = ""
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    source: str = ""
    source_reference_id: str = ""
    affected_surface: str = ""
    review_status: str = REVIEW_STATUS_PENDING
    style_profile_ref: str = ""
    created_utc: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
            "source": self.source,
            "source_reference_id": self.source_reference_id,
            "affected_surface": self.affected_surface,
            "review_status": self.review_status,
            "style_profile_ref": self.style_profile_ref,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StylePatternCandidate:
        return cls(
            candidate_id=str(d.get("candidate_id", "")),
            pattern_type=str(d.get("pattern_type", "")),
            description=str(d.get("description", "")),
            evidence=list(d.get("evidence", [])),
            confidence=float(d.get("confidence", 0)),
            source=str(d.get("source", "")),
            source_reference_id=str(d.get("source_reference_id", "")),
            affected_surface=str(d.get("affected_surface", "")),
            review_status=str(d.get("review_status", REVIEW_STATUS_PENDING)),
            style_profile_ref=str(d.get("style_profile_ref", "")),
            created_utc=str(d.get("created_utc", "")),
            updated_utc=str(d.get("updated_utc", "")),
        )


@dataclass
class AcceptedPreferenceUpdate:
    """Record of an accepted preference/style applied to a surface."""
    update_id: str
    candidate_id: str
    candidate_type: str  # preference | style_pattern
    key_or_pattern: str = ""
    applied_value: Any = None
    applied_surface: str = ""
    applied_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "update_id": self.update_id,
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type,
            "key_or_pattern": self.key_or_pattern,
            "applied_value": self.applied_value,
            "applied_surface": self.applied_surface,
            "applied_utc": self.applied_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AcceptedPreferenceUpdate:
        return cls(
            update_id=str(d.get("update_id", "")),
            candidate_id=str(d.get("candidate_id", "")),
            candidate_type=str(d.get("candidate_type", "preference")),
            key_or_pattern=str(d.get("key_or_pattern", "")),
            applied_value=d.get("applied_value"),
            applied_surface=str(d.get("applied_surface", "")),
            applied_utc=str(d.get("applied_utc", "")),
        )


@dataclass
class BehaviorDelta:
    """M31L.1: Explicit before/after for one surface when applying a learned preference."""
    surface: str
    key_or_target: str = ""
    before_value: Any = None
    after_value: Any = None
    human_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "key_or_target": self.key_or_target,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "human_summary": self.human_summary,
        }


@dataclass
class PersonalProfilePreset:
    """M31L.1: Named set of preference/style candidates to apply as a group."""
    preset_id: str
    name: str
    description: str = ""
    candidate_ids: list[str] = field(default_factory=list)
    created_utc: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "name": self.name,
            "description": self.description,
            "candidate_ids": list(self.candidate_ids),
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PersonalProfilePreset:
        return cls(
            preset_id=str(d.get("preset_id", "")),
            name=str(d.get("name", "")),
            description=str(d.get("description", "")),
            candidate_ids=list(d.get("candidate_ids", [])),
            created_utc=str(d.get("created_utc", "")),
            updated_utc=str(d.get("updated_utc", "")),
        )
