"""
M23M: Correction event schema and structured categories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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

SOURCE_TYPES = (
    "recommendation",
    "routine",
    "plan_preview",
    "job_run",
    "artifact_output",
    "task_replay",
    "benchmark_result",
    "other",
)

CORRECTION_CATEGORIES = (
    "wrong_recommendation_timing",
    "wrong_recommendation_target",
    "missing_approval_blocker_explanation",
    "bad_job_parameter_default",
    "bad_path_app_preference",
    "output_style_correction",
    "artifact_content_correction",
    "trust_level_too_high",
    "trust_level_too_low",
    "trust_notes_correction",
    "routine_ordering_correction",
    "plan_preview_mismatch",
    "simulate_vs_real_mismatch",
    "context_trigger_false_positive",
    "context_trigger_false_negative",
    "other",
)

OPERATOR_ACTIONS = ("rejected", "corrected", "accepted_with_note", "skipped", "deferred")

SEVERITY_LEVELS = ("low", "medium", "high")


@dataclass
class CorrectionEvent:
    """Single operator correction event. Stored locally; inspectable."""
    correction_id: str
    timestamp: str
    source_type: str  # recommendation | routine | plan_preview | job_run | artifact_output | task_replay | benchmark_result
    source_reference_id: str
    operator_action: str  # rejected | corrected | accepted_with_note | skipped | deferred
    correction_category: str
    original_value: Any = None
    corrected_value: Any = None
    correction_reason: str = ""
    severity: str = "medium"
    eligible_for_memory_update: bool = False
    reversible: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "correction_id": self.correction_id,
            "timestamp": self.timestamp,
            "source_type": self.source_type,
            "source_reference_id": self.source_reference_id,
            "operator_action": self.operator_action,
            "correction_category": self.correction_category,
            "original_value": self.original_value,
            "corrected_value": self.corrected_value,
            "correction_reason": self.correction_reason,
            "severity": self.severity,
            "eligible_for_memory_update": self.eligible_for_memory_update,
            "reversible": self.reversible,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CorrectionEvent:
        return cls(
            correction_id=str(d.get("correction_id", "")),
            timestamp=str(d.get("timestamp", "")),
            source_type=str(d.get("source_type", "other")),
            source_reference_id=str(d.get("source_reference_id", "")),
            operator_action=str(d.get("operator_action", "corrected")),
            correction_category=str(d.get("correction_category", "other")),
            original_value=d.get("original_value"),
            corrected_value=d.get("corrected_value"),
            correction_reason=str(d.get("correction_reason", "")),
            severity=str(d.get("severity", "medium")),
            eligible_for_memory_update=bool(d.get("eligible_for_memory_update", False)),
            reversible=bool(d.get("reversible", True)),
            notes=str(d.get("notes", "")),
        )


def validate_category_for_source(category: str, source_type: str) -> bool:
    """Return True if this category is valid for this source type (advisory; we still store unknown)."""
    if category not in CORRECTION_CATEGORIES:
        return False
    if source_type not in SOURCE_TYPES:
        return False
    # Tighten: e.g. bad_job_parameter_default makes sense for job_run, recommendation, plan_preview
    return True


def _eligible_categories() -> set[str]:
    """Categories that can drive memory/default updates (under rules)."""
    return {
        "bad_job_parameter_default",
        "bad_path_app_preference",
        "output_style_correction",
        "trust_notes_correction",
        "routine_ordering_correction",
        "context_trigger_false_positive",
        "context_trigger_false_negative",
    }


def is_eligible_for_memory_update(category: str) -> bool:
    return category in _eligible_categories()
