"""
M35A–M35D: Tests for authority tiers and trusted routine contracts.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.trust.tiers import (
    AuthorityTierId,
    BUILTIN_TIERS,
    list_tiers,
    get_tier,
    tier_allows_action,
    ACTION_OBSERVE,
    ACTION_EXECUTE_SIMULATE,
    ACTION_COMMIT_OR_SEND,
)
from workflow_dataset.trust.contracts import (
    TrustedRoutineContract,
    load_contracts,
    save_contracts,
    get_contract,
    get_contracts_for_routine,
    validate_contract,
)
from workflow_dataset.trust.scope import effective_contract, merge_contract_with_tier, SCOPE_ORDER
from workflow_dataset.trust.explain_contract import (
    explain_why_allowed,
    explain_why_blocked,
    explain_routine,
)


def test_builtin_tiers_present() -> None:
    """All seven built-in authority tiers exist and have required fields."""
    tiers = list_tiers()
    assert len(tiers) == 7
    ids = {t.tier_id for t in tiers}
    for e in AuthorityTierId:
        assert e.value in ids
    for t in tiers:
        assert t.tier_id
        assert isinstance(t.allowed_action_classes, list)
        assert isinstance(t.forbidden_action_classes, list)
        assert isinstance(t.order, int)


def test_tier_allows_action_observe() -> None:
    """observe_only allows observe, forbids execute and commit."""
    tier = get_tier("observe_only")
    assert tier is not None
    assert tier_allows_action(tier, ACTION_OBSERVE) is True
    assert tier_allows_action(tier, ACTION_EXECUTE_SIMULATE) is False
    assert tier_allows_action(tier, ACTION_COMMIT_OR_SEND) is False


def test_tier_allows_action_sandbox() -> None:
    """sandbox_write allows observe, suggest, draft, sandbox_write, execute_simulate."""
    tier = get_tier("sandbox_write")
    assert tier is not None
    assert tier_allows_action(tier, ACTION_OBSERVE) is True
    assert tier_allows_action(tier, ACTION_EXECUTE_SIMULATE) is True
    assert tier_allows_action(tier, ACTION_COMMIT_OR_SEND) is False


def test_validate_contract_valid(tmp_path: Path) -> None:
    """A valid contract passes validation."""
    c = TrustedRoutineContract(
        contract_id="test_contract",
        routine_id="morning_digest",
        scope="global",
        authority_tier_id="sandbox_write",
        permitted_action_classes=[ACTION_OBSERVE, ACTION_EXECUTE_SIMULATE],
    )
    valid, errors = validate_contract(c)
    assert valid is True
    assert len(errors) == 0


def test_validate_contract_unknown_tier() -> None:
    """Contract with unknown tier_id fails validation."""
    c = TrustedRoutineContract(
        contract_id="bad_tier",
        routine_id="r1",
        authority_tier_id="nonexistent_tier",
    )
    valid, errors = validate_contract(c)
    assert valid is False
    assert any("Unknown" in e or "nonexistent" in e for e in errors)


def test_validate_contract_permitted_excluded_conflict() -> None:
    """Contract with same action in permitted and excluded fails."""
    c = TrustedRoutineContract(
        contract_id="conflict",
        routine_id="r1",
        authority_tier_id="sandbox_write",
        permitted_action_classes=[ACTION_OBSERVE],
        excluded_action_classes=[ACTION_OBSERVE],
    )
    valid, errors = validate_contract(c)
    assert valid is False
    assert any("permitted" in e.lower() and "excluded" in e.lower() for e in errors)


def test_validate_contract_permitted_beyond_tier() -> None:
    """Contract that permits an action the tier forbids fails."""
    c = TrustedRoutineContract(
        contract_id="beyond_tier",
        routine_id="r1",
        authority_tier_id="observe_only",
        permitted_action_classes=[ACTION_COMMIT_OR_SEND],
    )
    valid, errors = validate_contract(c)
    assert valid is False
    assert any("does not allow" in e for e in errors)


def test_scope_precedence_project_over_global(tmp_path: Path) -> None:
    """Project-scoped contract wins over global for matching project context."""
    (tmp_path / "data/local/trust").mkdir(parents=True)
    global_c = TrustedRoutineContract(
        contract_id="global_r",
        routine_id="digest",
        scope="global",
        authority_tier_id="sandbox_write",
        enabled=True,
    )
    project_c = TrustedRoutineContract(
        contract_id="project_r",
        routine_id="digest",
        scope="project",
        scope_id="proj_alpha",
        authority_tier_id="draft_only",
        enabled=True,
    )
    save_contracts([global_c, project_c], tmp_path)
    # No context: global wins (only matching)
    eff = effective_contract("digest", {}, tmp_path)
    assert eff is not None
    assert eff.contract_id == "global_r"
    # With project_id: project wins
    eff2 = effective_contract("digest", {"project_id": "proj_alpha"}, tmp_path)
    assert eff2 is not None
    assert eff2.contract_id == "project_r"


def test_explain_why_blocked_no_contract(tmp_path: Path) -> None:
    """explain_why_blocked returns no_contract when no contract exists for routine."""
    out = explain_why_blocked("nonexistent_routine", ACTION_EXECUTE_SIMULATE, repo_root=tmp_path)
    assert out.get("allowed") is False
    assert out.get("reason") == "no_contract"
    assert "No trusted routine contract" in " ".join(out.get("explanation", []))


def test_explain_why_allowed_with_contract(tmp_path: Path) -> None:
    """explain_why_allowed returns allowed=True when contract and tier permit action."""
    c = TrustedRoutineContract(
        contract_id="allow_sandbox",
        routine_id="morning_digest",
        scope="global",
        authority_tier_id="sandbox_write",
        permitted_action_classes=[ACTION_OBSERVE, ACTION_EXECUTE_SIMULATE],
        enabled=True,
    )
    save_contracts([c], tmp_path)
    out = explain_why_allowed("morning_digest", ACTION_OBSERVE, repo_root=tmp_path)
    assert out.get("allowed") is True
    assert out.get("tier_id") == "sandbox_write"
    assert out.get("contract_id") == "allow_sandbox"


def test_explain_routine_blocked_when_no_contract(tmp_path: Path) -> None:
    """explain_routine reports blocked when no contract for routine."""
    out = explain_routine("no_contract_routine", repo_root=tmp_path)
    assert out.get("blocked") is True
    assert out.get("routine_id") == "no_contract_routine"


def test_merge_contract_with_tier_excluded_wins() -> None:
    """Excluded list from contract is merged; excluded always wins."""
    tier = get_tier("sandbox_write")
    contract = TrustedRoutineContract(
        contract_id="c1",
        routine_id="r1",
        authority_tier_id="sandbox_write",
        excluded_action_classes=[ACTION_EXECUTE_SIMULATE],
    )
    merged = merge_contract_with_tier(contract, tier)
    assert ACTION_EXECUTE_SIMULATE in merged.get("excluded_action_classes", [])


def test_scope_order_defined() -> None:
    """SCOPE_ORDER has expected precedence (more specific last)."""
    assert "global" in SCOPE_ORDER
    assert "project" in SCOPE_ORDER
    assert "recurring_routine" in SCOPE_ORDER
    assert SCOPE_ORDER.index("global") < SCOPE_ORDER.index("recurring_routine")
