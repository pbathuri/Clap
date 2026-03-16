"""
M19: Local persistence for trial feedback and session summaries.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from workflow_dataset.feedback.feedback_models import TrialFeedbackEntry, TrialSessionSummary


def _trials_dir(store_path: Path | str | None) -> Path:
    base = Path(store_path) if store_path else Path("data/local/trials")
    base.mkdir(parents=True, exist_ok=True)
    return base


def save_feedback_entry(entry: TrialFeedbackEntry, store_path: Path | str | None = None) -> Path:
    """Persist one feedback entry as JSON. Returns path to file."""
    if not entry.feedback_id or not entry.feedback_id.startswith("fb_"):
        entry = TrialFeedbackEntry(
            **{**entry.model_dump(), "feedback_id": f"fb_{uuid.uuid4().hex[:12]}"}
        )
    root = _trials_dir(store_path)
    feedback_dir = root / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    path = feedback_dir / f"{entry.feedback_id}.json"
    path.write_text(entry.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_feedback_entries(store_path: Path | str | None = None) -> list[TrialFeedbackEntry]:
    """Load all feedback entries from store. Returns empty list if dir missing."""
    root = _trials_dir(store_path)
    feedback_dir = root / "feedback"
    if not feedback_dir.exists():
        return []
    entries = []
    for path in sorted(feedback_dir.glob("fb_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entries.append(TrialFeedbackEntry.model_validate(data))
        except Exception:
            continue
    return entries


def save_session_summary(summary: TrialSessionSummary, store_path: Path | str | None = None) -> Path:
    """Persist session summary. Returns path to file."""
    if not summary.summary_id or not summary.summary_id.startswith("sum_"):
        summary = TrialSessionSummary(
            **{**summary.model_dump(), "summary_id": f"sum_{uuid.uuid4().hex[:12]}"}
        )
    root = _trials_dir(store_path)
    summary_dir = root / "summaries"
    summary_dir.mkdir(parents=True, exist_ok=True)
    path = summary_dir / f"{summary.summary_id}.json"
    path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_session_summaries(store_path: Path | str | None = None) -> list[TrialSessionSummary]:
    """Load all session summaries from store."""
    root = _trials_dir(store_path)
    summary_dir = root / "summaries"
    if not summary_dir.exists():
        return []
    summaries = []
    for path in sorted(summary_dir.glob("sum_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            summaries.append(TrialSessionSummary.model_validate(data))
        except Exception:
            continue
    return summaries
