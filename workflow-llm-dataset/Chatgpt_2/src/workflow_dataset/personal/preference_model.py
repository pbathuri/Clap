"""
Model user preferences: UI, notifications, execution boundaries.

Stored in personal work graph; used by agent to respect user choices.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PreferenceRecord(BaseModel):
    """Single preference entry."""

    key: str = Field(..., description="e.g. ui.theme, execution.require_confirm")
    value: str | bool | int | list[str] = Field(...)
    source: str = Field(default="teaching", description="teaching | inferred")
    updated_utc: str = Field(default="")


def get_preference(
    graph_store: Any,
    key: str,
) -> PreferenceRecord | None:
    """Retrieve preference by key. TODO: implement."""
    return None


def set_preference(
    graph_store: Any,
    pref: PreferenceRecord,
) -> None:
    """Set or update preference. TODO: implement persistence."""
    pass
