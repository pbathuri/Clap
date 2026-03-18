"""
M27D.1: Project templates and goal archetypes. First-draft reusable templates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.project_case.models import ProjectTemplate, GoalArchetype
from workflow_dataset.project_case.store import create_project, load_project, attach_artifact
from workflow_dataset.project_case.goal_stack import add_goal

# Built-in templates
FOUNDER_OPS = ProjectTemplate(
    template_id="founder_ops",
    title="Founder ops project",
    description="Light ops, reporting, stakeholder updates. Weekly cadence.",
    default_goal_stack=[
        GoalArchetype("ship_weekly_report", "Ship weekly report", "Produce and send weekly status.", 0),
        GoalArchetype("stakeholder_review", "Stakeholder review", "Review with stakeholders.", 1, "Waiting on approval"),
        GoalArchetype("close_loop", "Close the loop", "Capture outcomes and next actions.", 2),
    ],
    common_artifacts=["weekly_status.md", "stakeholder_notes", "outcomes.json"],
    likely_blockers=["approval_missing", "timeout", "user_abandoned"],
    recommended_pack_ids=["founder_ops_pack", "ops_reporting_pack"],
    recommended_value_pack_ids=["founder_ops", "reporting_workspace"],
)

ANALYST_RESEARCH = ProjectTemplate(
    template_id="analyst_research",
    title="Analyst research case",
    description="Research case: gather sources, synthesize, draft report.",
    default_goal_stack=[
        GoalArchetype("gather_sources", "Gather sources", "Collect and tag sources.", 0),
        GoalArchetype("synthesize", "Synthesize", "Synthesize findings.", 1),
        GoalArchetype("draft_report", "Draft report", "Draft research report.", 2),
        GoalArchetype("review_and_publish", "Review and publish", "Review and publish.", 3, "Waiting on review"),
    ],
    common_artifacts=["sources.json", "synthesis_notes.md", "research_report.md"],
    likely_blockers=["approval_missing", "path_scope_denied", "timeout"],
    recommended_pack_ids=["analyst_pack", "research_pack"],
    recommended_value_pack_ids=["analyst_workspace", "research_kit"],
)

DOCUMENT_REVIEW = ProjectTemplate(
    template_id="document_review",
    title="Document review case",
    description="Review documents: intake, triage, review, sign-off.",
    default_goal_stack=[
        GoalArchetype("intake_docs", "Intake documents", "Ingest and classify documents.", 0),
        GoalArchetype("triage", "Triage", "Triage and assign.", 1),
        GoalArchetype("review_round", "Review round", "Complete review round.", 2),
        GoalArchetype("sign_off", "Sign-off", "Obtain sign-off.", 3, "Waiting on sign-off"),
    ],
    common_artifacts=["intake_list.csv", "triage_notes.md", "review_checklist", "sign_off_record"],
    likely_blockers=["approval_missing", "policy_denied", "user_abandoned"],
    recommended_pack_ids=["document_review_pack", "compliance_pack"],
    recommended_value_pack_ids=["review_workspace", "compliance_kit"],
)

DEVELOPER_FEATURE = ProjectTemplate(
    template_id="developer_feature",
    title="Developer feature case",
    description="Feature work: spec, implement, test, ship.",
    default_goal_stack=[
        GoalArchetype("spec", "Spec", "Write and agree spec.", 0),
        GoalArchetype("implement", "Implement", "Implement changes.", 1),
        GoalArchetype("test", "Test", "Test and fix.", 2),
        GoalArchetype("ship", "Ship", "Ship and document.", 3, "Waiting on merge/review"),
    ],
    common_artifacts=["spec.md", "changelog", "test_report", "release_notes"],
    likely_blockers=["approval_missing", "policy_denied", "runtime_unavailable"],
    recommended_pack_ids=["developer_pack", "feature_pack"],
    recommended_value_pack_ids=["developer_starter", "coding_kit"],
)

BUILTIN_TEMPLATES: list[ProjectTemplate] = [
    FOUNDER_OPS,
    ANALYST_RESEARCH,
    DOCUMENT_REVIEW,
    DEVELOPER_FEATURE,
]


def list_templates(repo_root: Path | str | None = None) -> list[ProjectTemplate]:
    """Return all available templates (built-in only in this first draft)."""
    return list(BUILTIN_TEMPLATES)


def get_template(template_id: str, repo_root: Path | str | None = None) -> ProjectTemplate | None:
    """Get template by id. Returns None if not found."""
    for t in BUILTIN_TEMPLATES:
        if t.template_id == template_id:
            return t
    return None


def create_project_from_template(
    project_id: str,
    template_id: str,
    title: str = "",
    description: str = "",
    repo_root: Path | str | None = None,
) -> Any | None:
    """
    Create a project from a template: create project, add default goals, attach common artifacts as labels.
    Returns the created Project or None if template not found.
    """
    template = get_template(template_id, repo_root)
    if not template:
        return None
    proj_title = title or template.title or project_id
    proj_desc = description or template.description
    project = create_project(project_id, title=proj_title, description=proj_desc, repo_root=repo_root)
    for g in template.default_goal_stack:
        add_goal(
            project_id,
            g.goal_id,
            title=g.title,
            description=g.description,
            order=g.order,
            repo_root=repo_root,
        )
        if g.default_blocked_reason:
            from workflow_dataset.project_case.goal_stack import set_goal_status
            set_goal_status(project_id, g.goal_id, "blocked", blocked_reason=g.default_blocked_reason, repo_root=repo_root)
    for artifact_label in template.common_artifacts:
        attach_artifact(project_id, artifact_label, repo_root=repo_root)
    return project
