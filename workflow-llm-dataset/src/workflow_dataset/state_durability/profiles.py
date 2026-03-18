"""
M37L.1: State compaction + long-run maintenance profiles.
Built-in profiles: light, balanced, aggressive.
"""

from __future__ import annotations

from workflow_dataset.state_durability.models import MaintenanceProfile, CompactionPolicy


def _default_policies() -> list[CompactionPolicy]:
    return [
        CompactionPolicy(
            subsystem_id="background_run",
            retain_days=30,
            max_items_before_summarize=500,
            summarization_kind="summarize_only",
            description="Background run history: suggest summarization after 500 entries or 30 days.",
        ),
        CompactionPolicy(
            subsystem_id="automation_inbox",
            retain_days=14,
            max_items_before_summarize=200,
            summarization_kind="summarize_only",
            description="Automation inbox decisions: suggest summarization after 200 or 14 days.",
        ),
        CompactionPolicy(
            subsystem_id="event_log",
            retain_days=30,
            max_items_before_summarize=1000,
            summarization_kind="summarize_only",
            description="Event/timeline log: suggest summarization after 1000 or 30 days.",
        ),
    ]


def get_maintenance_profile(profile_id: str) -> MaintenanceProfile:
    """Return built-in maintenance profile by id. Default: balanced."""
    if profile_id == "light":
        return MaintenanceProfile(
            profile_id="light",
            label="Light maintenance",
            description="Minimal compaction; long retention. Good for low-volume use.",
            policies=[
                CompactionPolicy("background_run", retain_days=90, max_items_before_summarize=1000, summarization_kind="summarize_only", description="90d / 1000 items"),
                CompactionPolicy("automation_inbox", retain_days=30, max_items_before_summarize=500, summarization_kind="summarize_only", description="30d / 500 items"),
                CompactionPolicy("event_log", retain_days=60, max_items_before_summarize=2000, summarization_kind="summarize_only", description="60d / 2000 items"),
            ],
        )
    if profile_id == "aggressive":
        return MaintenanceProfile(
            profile_id="aggressive",
            label="Aggressive maintenance",
            description="Shorter retention; suggest summarization sooner. Good for high-volume or disk-sensitive.",
            policies=[
                CompactionPolicy("background_run", retain_days=14, max_items_before_summarize=200, summarization_kind="summarize_only", description="14d / 200 items"),
                CompactionPolicy("automation_inbox", retain_days=7, max_items_before_summarize=100, summarization_kind="summarize_only", description="7d / 100 items"),
                CompactionPolicy("event_log", retain_days=14, max_items_before_summarize=500, summarization_kind="summarize_only", description="14d / 500 items"),
            ],
        )
    # balanced (default)
    return MaintenanceProfile(
        profile_id="balanced",
        label="Balanced maintenance",
        description="Moderate retention and summarization thresholds. Default for long-run use.",
        policies=_default_policies(),
    )


def list_maintenance_profiles() -> list[MaintenanceProfile]:
    """Return all built-in maintenance profiles."""
    return [
        get_maintenance_profile("light"),
        get_maintenance_profile("balanced"),
        get_maintenance_profile("aggressive"),
    ]
