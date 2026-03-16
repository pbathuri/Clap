"""
M23M: Capture operator corrections. Build event, validate, save.
"""

from __future__ import annotations

from pathlib import Path
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

from workflow_dataset.corrections.schema import (
    CorrectionEvent,
    SOURCE_TYPES,
    CORRECTION_CATEGORIES,
    OPERATOR_ACTIONS,
    SEVERITY_LEVELS,
    is_eligible_for_memory_update,
)
from workflow_dataset.corrections.store import save_correction


def add_correction(
    source_type: str,
    source_reference_id: str,
    correction_category: str,
    operator_action: str = "corrected",
    original_value: Any = None,
    corrected_value: Any = None,
    correction_reason: str = "",
    severity: str = "medium",
    notes: str = "",
    repo_root: Path | str | None = None,
) -> CorrectionEvent:
    """
    Record a correction event. Validates source_type and category; sets eligible_for_memory_update from category.
    """
    if source_type not in SOURCE_TYPES:
        source_type = "other"
    if correction_category not in CORRECTION_CATEGORIES:
        correction_category = "other"
    if operator_action not in OPERATOR_ACTIONS:
        operator_action = "corrected"
    if severity not in SEVERITY_LEVELS:
        severity = "medium"

    eligible = is_eligible_for_memory_update(correction_category)
    correction_id = f"corr_{stable_id(source_type, source_reference_id, correction_category, utc_now_iso(), prefix='')[:16]}"

    event = CorrectionEvent(
        correction_id=correction_id,
        timestamp=utc_now_iso(),
        source_type=source_type,
        source_reference_id=source_reference_id,
        operator_action=operator_action,
        correction_category=correction_category,
        original_value=original_value,
        corrected_value=corrected_value,
        correction_reason=correction_reason,
        severity=severity,
        eligible_for_memory_update=eligible,
        reversible=True,
        notes=notes,
    )
    save_correction(event, repo_root)
    return event
