"""
M21: Structured pilot feedback capture. Persist per-session feedback locally.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.pilot.session_models import PilotFeedbackRecord
from workflow_dataset.pilot.session_log import get_current_session_id
from workflow_dataset.utils.dates import utc_now_iso

DEFAULT_PILOT_DIR = Path("data/local/pilot")
FEEDBACK_SUBDIR = "feedback"


def _feedback_dir(pilot_dir: Path | str | None = None) -> Path:
    root = Path(pilot_dir) if pilot_dir else DEFAULT_PILOT_DIR
    d = root / FEEDBACK_SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def capture_feedback(
    session_id: str | None = None,
    usefulness_score: int = 0,
    trust_score: int = 0,
    clarity_score: int = 0,
    adoption_likelihood: int = 0,
    blocker_encountered: bool = False,
    top_failure_reason: str = "",
    operator_friction_notes: str = "",
    user_quote: str = "",
    freeform_notes: str = "",
    pilot_dir: Path | str | None = None,
) -> Path:
    """Write structured feedback for a session. Uses current session if session_id omitted."""
    sid = session_id or get_current_session_id(pilot_dir)
    if not sid:
        raise ValueError("No session_id and no current session; run pilot start-session first")
    record = PilotFeedbackRecord(
        session_id=sid,
        timestamp=utc_now_iso(),
        usefulness_score=min(5, max(0, usefulness_score)),
        trust_score=min(5, max(0, trust_score)),
        clarity_score=min(5, max(0, clarity_score)),
        adoption_likelihood=min(5, max(0, adoption_likelihood)),
        blocker_encountered=blocker_encountered,
        top_failure_reason=top_failure_reason,
        operator_friction_notes=operator_friction_notes,
        user_quote=user_quote,
        freeform_notes=freeform_notes,
    )
    fb_dir = _feedback_dir(pilot_dir)
    path = fb_dir / f"{sid}_feedback.json"
    path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")
    return path


def load_feedback(session_id: str, pilot_dir: Path | str | None = None) -> PilotFeedbackRecord | None:
    """Load feedback for a session."""
    fb_dir = _feedback_dir(pilot_dir)
    path = fb_dir / f"{session_id}_feedback.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return PilotFeedbackRecord.from_dict(data)
    except Exception:
        return None


def list_feedback_files(pilot_dir: Path | str | None = None, limit: int = 100) -> list[Path]:
    """List feedback JSON paths (newest first by mtime)."""
    fb_dir = _feedback_dir(pilot_dir)
    paths = sorted(fb_dir.glob("*_feedback.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return paths[:limit]
