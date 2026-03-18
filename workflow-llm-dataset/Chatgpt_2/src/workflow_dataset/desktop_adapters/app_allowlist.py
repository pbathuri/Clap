"""
M23C-F3: Approved app names for app_launch adapter. Simulate only; no real launch.
Resolve display names for preview. Local-first; explicit allowlist.
"""

from __future__ import annotations

# Approved app display names / identifiers for preview resolution. Simulate-only; no execution.
APPROVED_APP_NAMES: tuple[str, ...] = (
    "Notes",
    "Safari",
    "Terminal",
    "TextEdit",
    "Finder",
    "Mail",
    "Calendar",
    "Reminders",
    "System Preferences",
    "System Settings",
)


def resolve_app_display_name(app_name_or_path: str) -> str | None:
    """
    Resolve to an approved display name for preview. Returns the matched approved name
    if the input matches (case-insensitive) an entry in APPROVED_APP_NAMES; otherwise None.
    Does not launch anything; simulate-only.
    """
    if not app_name_or_path or not isinstance(app_name_or_path, str):
        return None
    key = app_name_or_path.strip()
    if not key:
        return None
    for approved in APPROVED_APP_NAMES:
        if approved.lower() == key.lower():
            return approved
    return None
