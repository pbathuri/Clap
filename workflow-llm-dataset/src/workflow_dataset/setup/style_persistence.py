"""
Persist style signals from setup under data/local/style_signals/<session_id>/.

Reproducible, local-only, with provenance to artifact/project/session.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class StyleSignalRecord(BaseModel):
    """A single persisted style signal with provenance."""
    pattern_type: str = Field(..., description="e.g. naming_convention, folder_layout, export_revision")
    value: str | list[str] | dict[str, Any] = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_paths: list[str] = Field(default_factory=list)
    session_id: str = Field(default="")
    project_path: str = Field(default="")
    description: str = Field(default="")


def persist_style_signals(
    session_id: str,
    signals: list[dict[str, Any]],
    out_dir: Path | str,
) -> Path:
    """Write style signals to out_dir/session_id/signatures.json."""
    out_dir = Path(out_dir)
    session_dir = out_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / "signatures.json"
    records = []
    for s in signals:
        records.append(StyleSignalRecord(
            pattern_type=s.get("pattern_type", ""),
            value=s.get("value", ""),
            confidence=float(s.get("confidence", 0)),
            evidence_paths=list(s.get("evidence_paths", []))[:50],
            session_id=session_id,
            project_path=s.get("project_path", ""),
            description=s.get("description", ""),
        ))
    with open(path, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in records], f, indent=2)
    return path


def load_style_signals(session_id: str, style_signals_dir: Path | str) -> list[StyleSignalRecord]:
    """Load persisted style signals for a session."""
    session_dir = Path(style_signals_dir) / session_id
    path = session_dir / "signatures.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [StyleSignalRecord.model_validate(r) for r in data]
