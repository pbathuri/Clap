"""
Minimal suggestion generator from inferred routines.

Local-only, deterministic, explainable. No actions taken; suggestions
are stored for user review. Safe: no modification to the user's real system.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


class Suggestion(BaseModel):
    """Single suggestion; stored locally, never executed without user approval."""

    suggestion_id: str = Field(..., description="Stable unique ID")
    suggestion_type: str = Field(..., description="e.g. focus_project, operations_workflow, named_project")
    title: str = Field(default="", description="Short title")
    description: str = Field(default="", description="Explainable description")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    supporting_signals: list[str] | list[dict[str, Any]] = Field(default_factory=list)
    created_utc: str = Field(default="")
    status: str = Field(default="pending", description="pending | accepted | dismissed")


def generate_suggestions(
    routines: list[dict[str, Any]],
    max_per_type: int = 3,
) -> list[Suggestion]:
    """
    Generate suggestions from inferred routines. Deterministic and grounded in observed metadata.
    No LLM; no file content; no actions taken.
    """
    suggestions: list[Suggestion] = []
    ts = utc_now_iso()

    # focus_project: "You often work in X; pin as focus project?"
    focus_routines = [r for r in routines if r.get("routine_type") == "frequent_project"]
    for r in focus_routines[:max_per_type]:
        project = r.get("project", "")
        if not project:
            continue
        count = r.get("touch_count", 0)
        sigs = r.get("supporting_signals", [])
        suggestions.append(Suggestion(
            suggestion_id=stable_id("sug", "focus", project, str(count), prefix="sug"),
            suggestion_type="focus_project",
            title=f"Pin '{project}' as focus project?",
            description=f"You often work in '{project}' ({count} file touches). Pin it as a focus project for quick access?",
            confidence_score=float(r.get("confidence", 0.7)),
            supporting_signals=sigs,
            created_utc=ts,
            status="pending",
        ))

    # operations_workflow: "You repeatedly open .csv/.xlsx in Y; treat as operations workflow?"
    ext_routines = [r for r in routines if r.get("routine_type") == "repeated_extensions_by_project"]
    for r in ext_routines[:max_per_type]:
        project = r.get("project", "")
        exts = r.get("extensions", [])
        if not project or not exts:
            continue
        spreadsheet_like = [e for e in exts if e in ("csv", "xlsx", "xls", "ods")]
        if not spreadsheet_like:
            continue
        label_exts = ", ".join(f".{e}" for e in exts[:3])
        suggestions.append(Suggestion(
            suggestion_id=stable_id("sug", "ops", project, label_exts, prefix="sug"),
            suggestion_type="operations_workflow",
            title=f"Treat '{project}' as operations workflow?",
            description=f"You repeatedly open {label_exts} files in '{project}'. Treat this as an operations/data workflow?",
            confidence_score=float(r.get("confidence", 0.75)),
            supporting_signals=r.get("supporting_signals", []),
            created_utc=ts,
            status="pending",
        ))

    # named_project: "This folder appears active; mark as named project?"
    folder_routines = [r for r in routines if r.get("routine_type") == "frequent_folder"]
    for r in folder_routines[:max_per_type]:
        path = r.get("path", "")
        if not path:
            continue
        name = Path(path).name
        count = r.get("touch_count", 0)
        suggestions.append(Suggestion(
            suggestion_id=stable_id("sug", "named", path, str(count), prefix="sug"),
            suggestion_type="named_project",
            title=f"Mark '{name}' as a named project?",
            description=f"This folder appears to be an active project ({count} touches). Give it a display name?",
            confidence_score=float(r.get("confidence", 0.7)),
            supporting_signals=r.get("supporting_signals", []),
            created_utc=ts,
            status="pending",
        ))

    return suggestions


def persist_suggestions(
    store_path: Path | str,
    suggestions: list[Suggestion],
) -> None:
    """Write suggestions to the local suggestions table (same DB as graph)."""
    import sqlite3

    from workflow_dataset.personal.graph_store import init_store, save_suggestion

    store_path = Path(store_path)
    init_store(store_path)
    conn = sqlite3.connect(str(store_path))
    try:
        for s in suggestions:
            save_suggestion(
                conn,
                suggestion_id=s.suggestion_id,
                suggestion_type=s.suggestion_type,
                title=s.title,
                description=s.description,
                confidence_score=s.confidence_score,
                supporting_signals=s.supporting_signals,
                created_utc=s.created_utc,
                status=s.status,
            )
        conn.commit()
    finally:
        conn.close()


def load_suggestions(
    store_path: Path | str,
    status_filter: str | None = "pending",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Load suggestions from the local store."""
    import sqlite3

    from workflow_dataset.personal.graph_store import init_store, list_suggestions

    store_path = Path(store_path)
    if not store_path.exists():
        return []
    init_store(store_path)
    conn = sqlite3.connect(str(store_path))
    try:
        return list_suggestions(conn, status_filter=status_filter, limit=limit)
    finally:
        conn.close()
