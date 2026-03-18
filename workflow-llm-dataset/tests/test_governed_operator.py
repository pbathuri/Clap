"""
M48I–M48L: Tests for governed operator mode and delegation safety.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.governed_operator.models import (
    DelegatedScope,
    DelegationExplanation,
    GovernedOperatorStatus,
)
from workflow_dataset.governed_operator.store import (
    save_scope,
    get_scope,
    list_scope_ids,
    load_governed_state,
    save_governed_state,
)
from workflow_dataset.governed_operator.controls import (
    role_safe_delegation,
    domain_bound_delegation,
    check_delegation,
)
from workflow_dataset.governed_operator.flows import (
    suspend_delegated_loop,
    revoke_delegated_scope,
    clear_suspension,
    explain_delegation,
    require_reauthorization,
    narrow_operator_scope,
)
from workflow_dataset.governed_operator.mission_control import governed_operator_slice
from workflow_dataset.governed_operator.presets import list_delegation_presets, get_delegation_preset
from workflow_dataset.governed_operator.playbooks import (
    list_reauthorization_playbooks,
    get_reauthorization_playbook,
    get_playbook_for_situation,
)
from workflow_dataset.governed_operator.guidance import suspension_revocation_guidance


def test_governed_scope_model() -> None:
    scope = DelegatedScope(
        scope_id="test_scope",
        label="Test scope",
        review_domain_id="operator_routine",
        role_id="operator",
        routine_ids=["morning_digest"],
        status=GovernedOperatorStatus.ACTIVE.value,
    )
    assert scope.scope_id == "test_scope"
    assert scope.review_domain_id == "operator_routine"
    d = scope.to_dict()
    assert d["scope_id"] == scope.scope_id
    assert d["status"] == "active"


def test_save_and_get_scope(tmp_path: Path) -> None:
    scope = DelegatedScope(
        scope_id="s1",
        label="Scope 1",
        review_domain_id="operator_routine",
        role_id="operator",
    )
    save_scope(scope, repo_root=tmp_path)
    assert "s1" in list_scope_ids(repo_root=tmp_path)
    loaded = get_scope("s1", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.label == "Scope 1"


def test_role_safe_delegation_scope_not_found(tmp_path: Path) -> None:
    out = role_safe_delegation("nonexistent", "operator", repo_root=tmp_path)
    assert out["allowed"] is False
    assert "scope_not_found" in out["reason"] or "not found" in out["detail"].lower()


def test_domain_bound_delegation(tmp_path: Path) -> None:
    scope = DelegatedScope(scope_id="d1", label="D1", review_domain_id="operator_routine", role_id="operator")
    save_scope(scope, repo_root=tmp_path)
    out = domain_bound_delegation("d1", "operator_routine", repo_root=tmp_path)
    assert out["allowed"] is True
    out2 = domain_bound_delegation("d1", "sensitive_gate", repo_root=tmp_path)
    assert out2["allowed"] is False
    assert "domain_mismatch" in out2["reason"] or "mismatch" in out2["detail"].lower()


def test_check_delegation_no_scope(tmp_path: Path) -> None:
    out = check_delegation(role_id="operator", routine_id="morning_digest", repo_root=tmp_path)
    assert out["allowed"] is False
    assert "no_scope" in out["reason"] or "scope" in out["detail"].lower()


def test_check_delegation_with_scope(tmp_path: Path) -> None:
    scope = DelegatedScope(
        scope_id="op_scope",
        label="Operator scope",
        review_domain_id="operator_routine",
        role_id="operator",
        routine_ids=["morning_digest"],
    )
    save_scope(scope, repo_root=tmp_path)
    out = check_delegation(role_id="operator", routine_id="morning_digest", scope_id="op_scope", repo_root=tmp_path)
    assert out["allowed"] is True
    assert out["scope_id"] == "op_scope"


def test_suspend_and_clear(tmp_path: Path) -> None:
    scope = DelegatedScope(scope_id="suspend_me", label="Suspend me", review_domain_id="operator_routine", role_id="operator")
    save_scope(scope, repo_root=tmp_path)
    out = suspend_delegated_loop("suspend_me", reason="Test", repo_root=tmp_path)
    assert out["ok"] is True
    assert "suspend_me" in out["suspended_scope_ids"]
    state = load_governed_state(repo_root=tmp_path)
    assert "suspend_me" in state.get("suspended_scope_ids", [])
    out2 = clear_suspension("suspend_me", repo_root=tmp_path)
    assert out2["ok"] is True
    assert "suspend_me" not in out2["suspended_scope_ids"]


def test_revoke_scope(tmp_path: Path) -> None:
    scope = DelegatedScope(scope_id="revoke_me", label="Revoke me", review_domain_id="operator_routine", role_id="operator")
    save_scope(scope, repo_root=tmp_path)
    out = revoke_delegated_scope("revoke_me", reason="Unsafe", repo_root=tmp_path)
    assert out["ok"] is True
    assert "revoke_me" in out["revoked_scope_ids"]
    check = check_delegation(role_id="operator", routine_id="x", scope_id="revoke_me", repo_root=tmp_path)
    assert check["allowed"] is False
    assert "revoked" in check["reason"] or "revoked" in check["detail"].lower()


def test_explain_delegation_allowed(tmp_path: Path) -> None:
    scope = DelegatedScope(scope_id="explain_ok", label="OK", review_domain_id="operator_routine", role_id="operator")
    save_scope(scope, repo_root=tmp_path)
    expl = explain_delegation("explain_ok", role_id="operator", repo_root=tmp_path)
    assert expl.allowed is True
    assert expl.status == GovernedOperatorStatus.ACTIVE.value
    assert "active" in expl.reason.lower() or "allowed" in expl.recommendation.lower()


def test_explain_delegation_revoked(tmp_path: Path) -> None:
    scope = DelegatedScope(scope_id="explain_rev", label="Rev", review_domain_id="operator_routine", role_id="operator")
    save_scope(scope, repo_root=tmp_path)
    revoke_delegated_scope("explain_rev", repo_root=tmp_path)
    expl = explain_delegation("explain_rev", repo_root=tmp_path)
    assert expl.allowed is False
    assert expl.status == GovernedOperatorStatus.REVOKED.value


def test_require_reauthorization(tmp_path: Path) -> None:
    scope = DelegatedScope(scope_id="reauth_1", label="Reauth", review_domain_id="operator_routine", role_id="operator")
    save_scope(scope, repo_root=tmp_path)
    out = require_reauthorization("reauth_1", repo_root=tmp_path)
    assert out["ok"] is True
    state = load_governed_state(repo_root=tmp_path)
    assert "reauth_1" in state.get("reauthorization_needed_scope_ids", [])


def test_narrow_operator_scope(tmp_path: Path) -> None:
    scope = DelegatedScope(
        scope_id="narrow_me",
        label="Narrow",
        review_domain_id="operator_routine",
        role_id="operator",
        routine_ids=["a", "b"],
        allowed_action_classes=["draft", "execute_simulate"],
    )
    save_scope(scope, repo_root=tmp_path)
    out = narrow_operator_scope("narrow_me", new_routine_ids=["a"], repo_root=tmp_path)
    assert out["ok"] is True
    loaded = get_scope("narrow_me", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.routine_ids == ["a"]


def test_governed_operator_slice(tmp_path: Path) -> None:
    scope = DelegatedScope(scope_id="slice_scope", label="Slice", review_domain_id="operator_routine", role_id="operator")
    save_scope(scope, repo_root=tmp_path)
    slice_data = governed_operator_slice(repo_root=tmp_path)
    assert "error" not in slice_data or not slice_data["error"]
    assert "active_governed_delegation_scope_ids" in slice_data
    assert "slice_scope" in slice_data.get("active_governed_delegation_scope_ids", [])
    assert "next_governance_action" in slice_data


def test_unsafe_cross_domain_delegation(tmp_path: Path) -> None:
    scope = DelegatedScope(
        scope_id="cross_scope",
        label="Cross",
        review_domain_id="operator_routine",
        role_id="operator",
    )
    save_scope(scope, repo_root=tmp_path)
    out = check_delegation(role_id="operator", routine_id="x", scope_id="cross_scope", review_domain_id="sensitive_gate", repo_root=tmp_path)
    assert out["allowed"] is False
    assert "domain_mismatch" in out["reason"] or "domain" in out["detail"].lower()


# ----- M48L.1 Delegation presets + reauthorization playbooks -----


def test_list_delegation_presets() -> None:
    presets = list_delegation_presets()
    assert len(presets) >= 3
    ids = [p.preset_id for p in presets]
    assert "narrow_trusted_routine" in ids
    assert "supervised_operator" in ids
    assert "maintenance_only" in ids


def test_get_delegation_preset() -> None:
    p = get_delegation_preset("narrow_trusted_routine")
    assert p is not None
    assert p.authority_tier_id == "bounded_trusted_real"
    assert p.max_routine_ids == 3
    assert get_delegation_preset("nonexistent") is None


def test_list_reauthorization_playbooks() -> None:
    playbooks = list_reauthorization_playbooks()
    assert len(playbooks) >= 4
    ids = [p.playbook_id for p in playbooks]
    assert "after_suspend" in ids
    assert "after_revoke" in ids
    assert "reauthorization_needed" in ids


def test_get_playbook_for_situation() -> None:
    p = get_playbook_for_situation("suspended")
    assert p is not None
    assert p.situation == "suspended"
    assert len(p.steps) >= 1
    p2 = get_playbook_for_situation("revoked")
    assert p2 is not None
    assert p2.playbook_id == "after_revoke"


def test_suspension_revocation_guidance_suspended(tmp_path: Path) -> None:
    scope = DelegatedScope(scope_id="guid_scope", label="G", review_domain_id="operator_routine", role_id="operator")
    save_scope(scope, repo_root=tmp_path)
    suspend_delegated_loop("guid_scope", repo_root=tmp_path)
    g = suspension_revocation_guidance("guid_scope", repo_root=tmp_path)
    assert g.status == "suspended"
    assert "suspended" in g.what_happens.lower()
    assert len(g.next_steps) >= 1
    assert g.suggested_playbook_id == "after_suspend"


def test_suspension_revocation_guidance_revoked(tmp_path: Path) -> None:
    scope = DelegatedScope(scope_id="guid_rev", label="R", review_domain_id="operator_routine", role_id="operator")
    save_scope(scope, repo_root=tmp_path)
    revoke_delegated_scope("guid_rev", repo_root=tmp_path)
    g = suspension_revocation_guidance("guid_rev", repo_root=tmp_path)
    assert g.status == "revoked"
    assert "revoked" in g.what_happens.lower()
    assert g.suggested_playbook_id == "after_revoke"


def test_explain_includes_playbook_and_guidance(tmp_path: Path) -> None:
    scope = DelegatedScope(scope_id="expl_pb", label="E", review_domain_id="operator_routine", role_id="operator")
    save_scope(scope, repo_root=tmp_path)
    suspend_delegated_loop("expl_pb", repo_root=tmp_path)
    expl = explain_delegation("expl_pb", repo_root=tmp_path)
    assert expl.suggested_playbook_id == "after_suspend"
    assert expl.guidance_summary
    assert "suspended" in expl.guidance_summary.lower()
