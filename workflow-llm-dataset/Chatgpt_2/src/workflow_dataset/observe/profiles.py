"""
Observation profiles and safe retention policies (M31D.1).

Predefined profiles: minimal, standard, teaching-heavy, document-heavy, developer-focused.
Each defines enabled sources, metadata depth, retention boundaries, redaction expectations,
and suitable user/workflow types. All data stays local.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from workflow_dataset.observe.sources import get_observation_source_registry


class ObservationProfile(BaseModel):
    """First-draft observation profile: sources, depth, retention, redaction, suitability."""

    profile_id: str = Field(..., description="Stable id: minimal, standard, teaching-heavy, document-heavy, developer-focused")
    display_name: str = Field(..., description="Human-readable name")
    enabled_sources: list[str] = Field(default_factory=list, description="Source ids enabled in this profile")
    metadata_depth: str = Field(
        default="observe_only",
        description="Default depth: observe_only | rich_metadata; can be overridden per source later",
    )
    retention_global_default_days: int = Field(default=90, description="Default retention when source has no override")
    retention_overrides_days: dict[str, int] = Field(
        default_factory=dict,
        description="Per-source retention in days; overrides profile default and source default",
    )
    redaction_expectations: str = Field(
        default="",
        description="Short description: what to redact or minimize (paths, commands, URLs, etc.)",
    )
    suitable_user_types: list[str] = Field(
        default_factory=list,
        description="Suggested user/persona types (e.g. privacy-first, developers, instructors)",
    )
    suitable_workflow_types: list[str] = Field(
        default_factory=list,
        description="Suggested workflow types (e.g. audit-only, document workflows, coding)",
    )


class RetentionPolicy(BaseModel):
    """Safe retention policy derived from a profile and source registry."""

    profile_id: str = Field(..., description="Profile this policy is for")
    global_default_days: int = Field(default=90, description="Default retention in days")
    per_source_days: dict[str, int] = Field(
        default_factory=dict,
        description="Effective retention days per source id",
    )
    per_source_max_events_per_day: dict[str, int | None] = Field(
        default_factory=dict,
        description="Cap events per day per source; None = no cap from profile",
    )
    summary: str = Field(default="", description="One-line human summary of the policy")


def get_observation_profiles() -> dict[str, ObservationProfile]:
    """Return the canonical set of observation profiles."""
    return {
        "minimal": ObservationProfile(
            profile_id="minimal",
            display_name="Minimal",
            enabled_sources=["file"],
            metadata_depth="observe_only",
            retention_global_default_days=14,
            retention_overrides_days={"file": 14},
            redaction_expectations="Prefer path hashes or basename-only for file paths; no PII.",
            suitable_user_types=["privacy-first users", "audit-only operators"],
            suitable_workflow_types=["audit-only", "lightweight presence"],
        ),
        "standard": ObservationProfile(
            profile_id="standard",
            display_name="Standard",
            enabled_sources=["file", "app", "calendar"],
            metadata_depth="observe_only",
            retention_global_default_days=90,
            retention_overrides_days={},
            redaction_expectations="Standard: metadata only; no content. Calendar: title and times only; attendees optional.",
            suitable_user_types=["general knowledge workers", "office roles"],
            suitable_workflow_types=["routine work", "calendar-aware scheduling", "project presence"],
        ),
        "teaching-heavy": ObservationProfile(
            profile_id="teaching-heavy",
            display_name="Teaching-heavy",
            enabled_sources=["file", "teaching", "calendar"],
            metadata_depth="rich_metadata",
            retention_global_default_days=90,
            retention_overrides_days={"teaching": 365, "file": 90},
            redaction_expectations="Teaching content user-controlled; no automatic redaction. File and calendar as standard.",
            suitable_user_types=["instructors", "coaches", "feedback-driven roles"],
            suitable_workflow_types=["feedback loops", "skill capture", "correction and labeling"],
        ),
        "document-heavy": ObservationProfile(
            profile_id="document-heavy",
            display_name="Document-heavy",
            enabled_sources=["file", "app", "browser"],
            metadata_depth="rich_metadata",
            retention_global_default_days=90,
            retention_overrides_days={"file": 90, "browser": 30},
            redaction_expectations="Browser: domain-only when observe_only. File: full path and extension; no content.",
            suitable_user_types=["content creators", "editors", "researchers"],
            suitable_workflow_types=["document workflows", "research", "writing and editing"],
        ),
        "developer-focused": ObservationProfile(
            profile_id="developer-focused",
            display_name="Developer-focused",
            enabled_sources=["file", "terminal", "app", "browser"],
            metadata_depth="observe_only",
            retention_global_default_days=60,
            retention_overrides_days={"file": 60, "terminal": 14},
            redaction_expectations="Terminal: command and cwd redacted or hashed by default. File and browser: metadata only.",
            suitable_user_types=["developers", "DevOps", "technical roles"],
            suitable_workflow_types=["coding", "builds", "repos", "CLI workflows"],
        ),
    }


def get_profile(profile_id: str) -> ObservationProfile | None:
    """Return the profile for profile_id, or None if unknown."""
    return get_observation_profiles().get(profile_id)


def list_profile_ids() -> list[str]:
    """Return profile ids in stable order."""
    return ["minimal", "standard", "teaching-heavy", "document-heavy", "developer-focused"]


def get_retention_policy_for_profile(profile_id: str) -> RetentionPolicy | None:
    """
    Build the effective retention policy for a profile by merging profile overrides
    with source registry defaults. Returns None if profile_id is unknown.
    """
    profiles = get_observation_profiles()
    profile = profiles.get(profile_id)
    if not profile:
        return None
    registry = get_observation_source_registry()
    per_source_days: dict[str, int] = {}
    per_source_max_events: dict[str, int | None] = {}
    for sid in profile.enabled_sources:
        defn = registry.get(sid)
        source_default_days = defn.retention_days if defn else None
        days = (
            profile.retention_overrides_days.get(sid)
            or source_default_days
            or profile.retention_global_default_days
        )
        per_source_days[sid] = days
        per_source_max_events[sid] = defn.max_events_per_day if defn else None
    summary_parts = [f"default={profile.retention_global_default_days}d"]
    for sid, d in per_source_days.items():
        summary_parts.append(f"{sid}={d}d")
    return RetentionPolicy(
        profile_id=profile_id,
        global_default_days=profile.retention_global_default_days,
        per_source_days=per_source_days,
        per_source_max_events_per_day=per_source_max_events,
        summary="; ".join(summary_parts),
    )


def format_retention_policy_output(policy: RetentionPolicy) -> dict[str, Any]:
    """Return a dict suitable for CLI or report output (sample retention policy output)."""
    return {
        "profile_id": policy.profile_id,
        "global_default_days": policy.global_default_days,
        "per_source_retention_days": policy.per_source_days,
        "per_source_max_events_per_day": policy.per_source_max_events_per_day,
        "summary": policy.summary,
    }
