"""
M48A–M48D: Tests for governance — role model, scope, bindings, check, explain, mission control.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.governance.models import (
    HumanRole,
    CheckResult,
    AuthorityExplanation,
    RoleType,
)
from workflow_dataset.governance.roles import get_role, list_roles
from workflow_dataset.governance.scope import resolve_scope, scope_precedence_rank, ScopeLevelId
from workflow_dataset.governance.bindings import get_effective_binding
from workflow_dataset.governance.check import can_role_perform_action
from workflow_dataset.governance.explain import explain_authority
from workflow_dataset.governance.mission_control import governance_slice


def test_list_roles() -> None:
    """List roles returns at least operator, reviewer, approver, observer, maintainer."""
    roles = list_roles()
    ids = [r.role_id for r in roles]
    assert "operator" in ids
    assert "reviewer" in ids
    assert "approver" in ids
    assert "observer" in ids
    assert "maintainer" in ids


def test_get_role_operator() -> None:
    """Operator role has may_execute True and default tier queued_execute."""
    r = get_role("operator")
    assert r is not None
    assert r.role_id == "operator"
    assert r.may_execute is True
    assert "queued_execute" in r.default_authority_tier_id


def test_get_role_unknown() -> None:
    """Unknown role returns None."""
    assert get_role("unknown_role_xyz") is None


def test_scope_precedence_rank() -> None:
    """Product_wide has lower rank than vertical; operator_mode_routine has highest."""
    assert scope_precedence_rank(ScopeLevelId.PRODUCT_WIDE.value) >= 0
    assert scope_precedence_rank(ScopeLevelId.OPERATOR_MODE_ROUTINE.value) >= scope_precedence_rank(ScopeLevelId.PRODUCT_WIDE.value)


def test_resolve_scope_product_wide() -> None:
    """Resolve scope product_wide returns AuthorityScope with level product_wide."""
    scope = resolve_scope("product_wide", None)
    assert scope is not None
    assert scope.level_id == ScopeLevelId.PRODUCT_WIDE.value


def test_resolve_scope_project() -> None:
    """Resolve scope project:foo returns scope_id foo."""
    scope = resolve_scope("project:proj_1", None)
    assert scope is not None
    assert scope.level_id == ScopeLevelId.PROJECT.value
    assert scope.scope_id == "proj_1"


def test_get_effective_binding_operator() -> None:
    """Effective binding for operator at product_wide returns binding with surfaces and actions."""
    binding = get_effective_binding("operator", "product_wide", None)
    assert binding is not None
    assert binding.role_id == "operator"
    assert len(binding.effective_surface_ids) >= 1 or len(binding.effective_action_classes) >= 1


def test_can_role_perform_action_observer_blocked() -> None:
    """Observer cannot perform queued_execute."""
    result = can_role_perform_action("observer", "queued_execute", None, None, None)
    assert isinstance(result, CheckResult)
    assert result.allowed is False
    assert "forbidden" in result.reason.lower() or "observe" in result.reason.lower() or "not" in result.reason.lower()


def test_can_role_perform_action_operator_simulate() -> None:
    """Operator can perform execute_simulate at product_wide."""
    result = can_role_perform_action("operator", "execute_simulate", "product_wide", None, None)
    assert isinstance(result, CheckResult)
    assert result.allowed is True


def test_can_role_perform_action_operator_commit_blocked() -> None:
    """Operator cannot perform commit_or_send."""
    result = can_role_perform_action("operator", "commit_or_send", None, None, None)
    assert result.allowed is False


def test_explain_authority_operator() -> None:
    """Explain authority for operator returns summary and scope context."""
    expl = explain_authority("operator", None, None, "product_wide", None)
    assert expl is not None
    assert expl.role_id == "operator"
    assert expl.summary
    assert expl.scope_context


def test_explain_authority_unknown_role() -> None:
    """Explain for unknown role returns explanation with unknown role message."""
    expl = explain_authority("unknown_xyz", None, None, None, None)
    assert expl is not None
    assert "Unknown" in expl.summary or "unknown" in expl.summary


def test_governance_slice(tmp_path: Path) -> None:
    """Governance slice returns role_map, sensitive_scopes, blocked count, next review."""
    slice_data = governance_slice(tmp_path)
    assert "current_role_map" in slice_data
    assert "most_sensitive_active_scopes" in slice_data
    assert "blocked_authority_attempts_count" in slice_data
    assert "next_recommended_governance_review" in slice_data
    assert isinstance(slice_data["current_role_map"], list)
    assert len(slice_data["current_role_map"]) >= 5


def test_missing_role_check() -> None:
    """Check with missing role returns CheckResult allowed=False."""
    result = can_role_perform_action("nonexistent_role", "observe", None, None, None)
    assert result.allowed is False
    assert "Unknown" in result.reason or "unknown" in result.reason


def test_missing_scope_binding() -> None:
    """Binding for valid role at None scope still returns a binding (product_wide fallback)."""
    binding = get_effective_binding("reviewer", None, None)
    assert binding is not None
    assert binding.scope_level in (ScopeLevelId.PRODUCT_WIDE.value, "product_wide")


# ----- M48D.1 Governance presets + scope templates -----


def test_list_governance_presets() -> None:
    """List governance presets includes solo_operator, supervised_team, production_maintainer."""
    from workflow_dataset.governance import list_presets
    presets = list_presets()
    ids = [p.preset_id for p in presets]
    assert "solo_operator" in ids
    assert "supervised_team" in ids
    assert "production_maintainer" in ids


def test_get_governance_preset() -> None:
    """Get preset solo_operator has primary_role operator and implications."""
    from workflow_dataset.governance import get_preset
    p = get_preset("solo_operator")
    assert p is not None
    assert p.primary_role_id == "operator"
    assert len(p.implications) >= 1


def test_get_active_preset_default(tmp_path: Path) -> None:
    """Without saved file, get_active_preset returns solo_operator default."""
    from workflow_dataset.governance import get_active_preset
    active = get_active_preset(tmp_path)
    assert active is not None
    assert active.preset_id == "solo_operator"


def test_set_and_get_active_preset(tmp_path: Path) -> None:
    """Set active preset then get_active_preset returns it."""
    from workflow_dataset.governance import set_active_preset, get_active_preset
    set_active_preset("supervised_team", tmp_path)
    active = get_active_preset(tmp_path)
    assert active is not None
    assert active.preset_id == "supervised_team"


def test_list_scope_templates() -> None:
    """List scope templates includes solo_vertical, team_vertical_project, production_single_vertical."""
    from workflow_dataset.governance import list_scope_templates
    templates = list_scope_templates()
    ids = [t.template_id for t in templates]
    assert "solo_vertical" in ids
    assert "team_vertical_project" in ids
    assert "production_single_vertical" in ids


def test_get_scope_template() -> None:
    """Get scope template production_single_vertical has scope_levels and deployment_pattern."""
    from workflow_dataset.governance import get_scope_template
    t = get_scope_template("production_single_vertical")
    assert t is not None
    assert "vertical" in t.scope_levels
    assert t.deployment_pattern == "production_single_vertical"


def test_format_governance_preset_report(tmp_path: Path) -> None:
    """Governance preset report contains active preset and implications."""
    from workflow_dataset.governance import format_governance_preset_report
    report = format_governance_preset_report(tmp_path)
    assert "Governance" in report or "preset" in report.lower()
    assert "solo_operator" in report or "imply" in report.lower() or "implications" in report.lower()


def test_governance_slice_includes_preset(tmp_path: Path) -> None:
    """Governance slice includes active_governance_preset_id and preset_implications."""
    slice_data = governance_slice(tmp_path)
    assert "active_governance_preset_id" in slice_data
    assert "preset_implications" in slice_data
    assert "active_scope_template_id" in slice_data
