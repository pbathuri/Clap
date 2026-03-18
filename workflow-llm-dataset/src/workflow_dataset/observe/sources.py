"""
Observation source model and registry (M31A).

Each bounded local observation source defines:
- allowed scope
- consent requirement
- collection mode (observe_only | rich_metadata)
- redaction rules if applicable
- retention/storage expectations
- trust notes

All data stays local; no cloud collection.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from workflow_dataset.observe.local_events import EventSource


class CollectionMode(str, Enum):
    """How much metadata to collect for a source."""
    OBSERVE_ONLY = "observe_only"   # Minimal: coarse type, timing, no PII where avoidable
    RICH_METADATA = "rich_metadata"  # Richer: e.g. domain vs full URL, optional fields


class ObservationSourceDef(BaseModel):
    """Definition of one observation source: scope, consent, mode, redaction, retention, trust."""

    source_id: str = Field(..., description="Matches EventSource value (file, app, browser, ...)")
    display_name: str = Field(..., description="Human-readable name")
    allowed_scope_description: str = Field(
        default="",
        description="What is in scope (e.g. paths under root_paths, approved apps)",
    )
    consent_required: bool = Field(
        default=True,
        description="Source must be in allowed_observation_sources to collect",
    )
    default_collection_mode: CollectionMode = Field(
        default=CollectionMode.OBSERVE_ONLY,
        description="Default mode for this source",
    )
    redaction_rules: str = Field(
        default="",
        description="When to redact (e.g. terminal command/cwd, browser URL to domain)",
    )
    retention_days: int | None = Field(
        default=None,
        description="Suggested max retention in days; None = use global default",
    )
    max_events_per_day: int | None = Field(
        default=None,
        description="Cap events per day for this source; None = no cap",
    )
    trust_notes: str = Field(
        default="",
        description="Short trust/privacy note for operators",
    )
    implemented: bool = Field(
        default=False,
        description="Whether a real collector exists (True for file only in v1)",
    )


def get_observation_source_registry() -> dict[str, ObservationSourceDef]:
    """
    Return the canonical registry of observation sources.
    Keys are EventSource values (file, app, browser, terminal, calendar, teaching).
    """
    return {
        EventSource.FILE.value: ObservationSourceDef(
            source_id=EventSource.FILE.value,
            display_name="File and folder metadata",
            allowed_scope_description="Paths under file_observer.root_paths; exclude_dirs applied. No content read.",
            consent_required=True,
            default_collection_mode=CollectionMode.OBSERVE_ONLY,
            redaction_rules="None; metadata only (path, name, size, mtime). Paths are not redacted by default.",
            retention_days=90,
            max_events_per_day=50_000,
            trust_notes="Metadata only; no file body. Safe for local work graph.",
            implemented=True,
        ),
        EventSource.APP.value: ObservationSourceDef(
            source_id=EventSource.APP.value,
            display_name="App usage",
            allowed_scope_description="Foreground app, switch events, duration. No in-app content.",
            consent_required=True,
            default_collection_mode=CollectionMode.OBSERVE_ONLY,
            redaction_rules="App name/bundle id only; no window titles or content.",
            retention_days=30,
            max_events_per_day=10_000,
            trust_notes="OS-level only; requires platform integration (stub in v1).",
            implemented=False,
        ),
        EventSource.BROWSER.value: ObservationSourceDef(
            source_id=EventSource.BROWSER.value,
            display_name="Browser tab/domain",
            allowed_scope_description="Tab URL/domain, title, timing. No page body or form data.",
            consent_required=True,
            default_collection_mode=CollectionMode.OBSERVE_ONLY,
            redaction_rules="URL may be reduced to domain only when observe_only.",
            retention_days=30,
            max_events_per_day=5_000,
            trust_notes="Requires browser extension or native integration (stub in v1).",
            implemented=False,
        ),
        EventSource.TERMINAL.value: ObservationSourceDef(
            source_id=EventSource.TERMINAL.value,
            display_name="Terminal commands",
            allowed_scope_description="Commands in configured shells; user can exclude paths or disable.",
            consent_required=True,
            default_collection_mode=CollectionMode.OBSERVE_ONLY,
            redaction_rules="Command and cwd may be redacted or hashed; configurable.",
            retention_days=14,
            max_events_per_day=2_000,
            trust_notes="Sensitive; optional redaction. Stub in v1.",
            implemented=False,
        ),
        EventSource.CALENDAR.value: ObservationSourceDef(
            source_id=EventSource.CALENDAR.value,
            display_name="Calendar metadata",
            allowed_scope_description="Event title, start/end, attendees. No body/description.",
            consent_required=True,
            default_collection_mode=CollectionMode.OBSERVE_ONLY,
            redaction_rules="Attendees optional; no body text.",
            retention_days=90,
            max_events_per_day=1_000,
            trust_notes="CalDAV or local API (stub in v1).",
            implemented=False,
        ),
        EventSource.TEACHING.value: ObservationSourceDef(
            source_id=EventSource.TEACHING.value,
            display_name="Manual teaching events",
            allowed_scope_description="User-provided labels, corrections, step-by-step instructions.",
            consent_required=True,
            default_collection_mode=CollectionMode.RICH_METADATA,
            redaction_rules="User controls content; no automatic redaction.",
            retention_days=None,
            max_events_per_day=None,
            trust_notes="Explicit user input; highest trust.",
            implemented=False,
        ),
    }


def list_source_ids() -> list[str]:
    """Return all registered source IDs in stable order."""
    registry = get_observation_source_registry()
    order = [
        EventSource.FILE.value,
        EventSource.APP.value,
        EventSource.BROWSER.value,
        EventSource.TERMINAL.value,
        EventSource.CALENDAR.value,
        EventSource.TEACHING.value,
    ]
    return [s for s in order if s in registry]
