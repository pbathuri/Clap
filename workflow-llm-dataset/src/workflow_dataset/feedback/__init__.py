"""
M19: Friendly-user trial feedback — local-only capture, store, and summary.
"""

from __future__ import annotations

from workflow_dataset.feedback.feedback_models import TrialFeedbackEntry, TrialSessionSummary
from workflow_dataset.feedback.feedback_store import (
    save_feedback_entry,
    load_feedback_entries,
    save_session_summary,
    load_session_summaries,
)
from workflow_dataset.feedback.feedback_summary import (
    aggregate_feedback,
    write_feedback_report,
)
from workflow_dataset.feedback.trial_events import record_trial_event, load_trial_events

__all__ = [
    "TrialFeedbackEntry",
    "TrialSessionSummary",
    "save_feedback_entry",
    "load_feedback_entries",
    "save_session_summary",
    "load_session_summaries",
    "aggregate_feedback",
    "write_feedback_report",
    "record_trial_event",
    "load_trial_events",
]
