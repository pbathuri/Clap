"""
M23V / M23O: Daily inbox / digest — start-here surface for operator.
"""

from workflow_dataset.daily.inbox import build_daily_digest, DailyDigest
from workflow_dataset.daily.inbox_report import format_inbox_report, format_explain_why_now
from workflow_dataset.daily.digest_history import (
    save_digest_snapshot,
    load_digest_snapshot,
    list_digest_snapshots,
    compare_digests,
    DigestCompare,
)

__all__ = [
    "build_daily_digest",
    "DailyDigest",
    "format_inbox_report",
    "format_explain_why_now",
    "save_digest_snapshot",
    "load_digest_snapshot",
    "list_digest_snapshots",
    "compare_digests",
    "DigestCompare",
]
