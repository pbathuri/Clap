"""
M26I–M26L: Agent Teaching Studio + Skill Capture.
Explicit, reviewable skill capture from demos/corrections/session patterns.
"""

from workflow_dataset.teaching.skill_models import Skill, SKILL_STATUSES, TRUST_READINESS_LEVELS
from workflow_dataset.teaching.skill_store import (
    get_skills_dir,
    save_skill,
    load_skill,
    list_skills,
    delete_skill,
)
from workflow_dataset.teaching.normalize import (
    demo_to_skill_draft,
    correction_to_skill_draft,
    manual_skill_draft,
)
from workflow_dataset.teaching.review import (
    list_candidate_skills,
    accept_skill,
    reject_skill,
    attach_skill_to_pack,
)
from workflow_dataset.teaching.report import build_skill_report, format_skill_report
from workflow_dataset.teaching.scorecard import (
    build_skill_scorecard,
    format_skill_scorecard,
    build_pack_goal_coverage_report,
    format_pack_goal_coverage_report,
)

__all__ = [
    "Skill",
    "SKILL_STATUSES",
    "TRUST_READINESS_LEVELS",
    "get_skills_dir",
    "save_skill",
    "load_skill",
    "list_skills",
    "delete_skill",
    "demo_to_skill_draft",
    "correction_to_skill_draft",
    "manual_skill_draft",
    "list_candidate_skills",
    "accept_skill",
    "reject_skill",
    "attach_skill_to_pack",
    "build_skill_report",
    "format_skill_report",
    "build_skill_scorecard",
    "format_skill_scorecard",
    "build_pack_goal_coverage_report",
    "format_pack_goal_coverage_report",
]
