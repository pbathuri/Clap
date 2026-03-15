"""
Manual user teaching (Tier 1).

Demonstrations, corrections, labels, freeform instructions.
See docs/schemas/LOCAL_OBSERVATION_EVENTS.md — source 'teaching'.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InstructionType(str, Enum):
    DEMONSTRATION = "demonstration"
    CORRECTION = "correction"
    LABEL = "label"
    FREEFORM = "freeform"


class TeachingPayload(BaseModel):
    """Payload for a manual teaching event."""

    instruction_type: InstructionType
    content: str | dict[str, Any] = Field(..., description="Steps or freeform text")
    target_entity_id: str | None = Field(default=None, description="e.g. workflow_step_id")


def teaching_payload(
    instruction_type: str,
    content: str | dict[str, Any],
    target_entity_id: str | None = None,
) -> dict[str, Any]:
    """Build payload for a teaching event."""
    return {
        "instruction_type": instruction_type,
        "content": content,
        "target_entity_id": target_entity_id,
    }


def record_teaching_event(
    instruction_type: InstructionType,
    content: str | dict[str, Any],
    target_entity_id: str | None = None,
) -> dict[str, Any]:
    """Record one manual teaching event. TODO: persist to event log and feed personal graph."""
    return teaching_payload(instruction_type.value, content, target_entity_id)
