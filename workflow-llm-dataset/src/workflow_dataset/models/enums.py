from __future__ import annotations

from enum import Enum


class TaskType(str, Enum):
    CORE = "core"
    SUPPLEMENTAL = "supplemental"
    INFERRED_CLUSTER = "inferred_cluster"


class AutomationCandidate(str, Enum):
    AUTOMATE = "automate"
    AUGMENT = "augment"
    HUMAN_LED = "human_led"
    UNKNOWN = "unknown"


class ReviewStatus(str, Enum):
    ACCEPTED = "accepted"
    REVIEWED = "reviewed"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"
