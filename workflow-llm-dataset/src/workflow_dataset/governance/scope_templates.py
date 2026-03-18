"""
M48D.1: Scope templates for common deployment patterns.
"""

from __future__ import annotations

from workflow_dataset.governance.models import ScopeTemplate


def _builtin_templates() -> list[ScopeTemplate]:
    return [
        ScopeTemplate(
            template_id="solo_vertical",
            label="Solo vertical",
            description="Single vertical; product-wide or chosen vertical scope.",
            scope_levels=["product_wide", "vertical"],
            default_scope_hint="vertical",
            deployment_pattern="solo_vertical",
            order=0,
        ),
        ScopeTemplate(
            template_id="team_vertical_project",
            label="Team vertical + project",
            description="Chosen vertical with optional project-level scope.",
            scope_levels=["vertical", "project"],
            default_scope_hint="vertical",
            deployment_pattern="team_vertical_project",
            order=1,
        ),
        ScopeTemplate(
            template_id="production_single_vertical",
            label="Production single vertical",
            description="Locked production cut; single vertical, review domains and operator routines scoped.",
            scope_levels=["vertical", "review_domain", "operator_mode_routine"],
            default_scope_hint="vertical",
            deployment_pattern="production_single_vertical",
            order=2,
        ),
    ]


def list_scope_templates() -> list[ScopeTemplate]:
    """Return all built-in scope templates in order."""
    return list(_builtin_templates())


def get_scope_template(template_id: str) -> ScopeTemplate | None:
    """Return scope template by id."""
    for t in _builtin_templates():
        if t.template_id == template_id:
            return t
    return None
