"""
Local-first observation layer (Tier 1–3).

Captures file, app, browser, terminal, calendar, and manual-teaching events
on-device only. No event data leaves the device unless the user explicitly
enables sync. See docs/OBSERVATION_PHASES.md.

M31: Source model (sources), consent/boundaries (boundaries), normalized event
stream (local_events), runtime (runtime), local state (state).
M31D.1: Observation profiles (profiles) and safe retention policies.
"""

from workflow_dataset.observe.local_events import ObservationEvent, EventSource
from workflow_dataset.observe.sources import (
    ObservationSourceDef,
    get_observation_source_registry,
    list_source_ids,
)
from workflow_dataset.observe.profiles import (
    ObservationProfile,
    RetentionPolicy,
    get_observation_profiles,
    get_profile,
    get_retention_policy_for_profile,
    list_profile_ids,
)

__all__ = [
    "ObservationEvent",
    "EventSource",
    "ObservationSourceDef",
    "get_observation_source_registry",
    "list_source_ids",
    "ObservationProfile",
    "RetentionPolicy",
    "get_observation_profiles",
    "get_profile",
    "get_retention_policy_for_profile",
    "list_profile_ids",
]
