"""
M35D.1: Tests for trust presets, routine eligibility matrix, and validation reporting.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.trust.presets import (
    TrustPreset,
    BUILTIN_PRESETS,
    get_preset,
    list_presets,
    preset_allows_tier,
)
from workflow_dataset.trust.eligibility import (
    ROUTINE_TYPES,
    ROUTINE_TYPE_DIGEST,
    ROUTINE_TYPE_FOLLOWUP,
    ROUTINE_TYPE_AD_HOC,
    routine_type_for,
    is_eligible,
    eligibility_matrix_report,
    max_tier_for_routine_under_preset,
)
from workflow_dataset.trust.validation_report import (
    TrustValidationReport,
    TrustConfigIssue,
    validate_trust_config,
    format_validation_report,
    get_active_preset_id,
)
from workflow_dataset.trust.contracts import TrustedRoutineContract, save_contracts


def test_builtin_presets_present() -> None:
    """All four built-in presets exist with expected ids."""
    presets = list_presets()
    assert len(presets) >= 4
    ids = {p.preset_id for p in presets}
    assert "cautious" in ids
    assert "supervised_operator" in ids
    assert "bounded_trusted_routine" in ids
    assert "release_safe" in ids


def test_get_preset() -> None:
    """get_preset returns preset by id."""
    p = get_preset("cautious")
    assert p is not None
    assert p.preset_id == "cautious"
    assert p.max_authority_tier_id == "suggest_only"
    assert get_preset("nonexistent") is None


def test_preset_allows_tier() -> None:
    """cautious allows suggest_only but not sandbox_write."""
    p = get_preset("cautious")
    assert p is not None
    assert preset_allows_tier(p, "suggest_only") is True
    assert preset_allows_tier(p, "sandbox_write") is False


def test_routine_type_for() -> None:
    """routine_type_for maps known and inferred routine ids."""
    assert routine_type_for("morning_digest") == ROUTINE_TYPE_DIGEST
    assert routine_type_for("blocked_followup") == ROUTINE_TYPE_FOLLOWUP
    assert routine_type_for("custom_digest_weekly") == ROUTINE_TYPE_DIGEST
    assert routine_type_for("unknown_xyz") == ROUTINE_TYPE_AD_HOC


def test_eligibility_matrix_has_all_presets() -> None:
    """Eligibility matrix report returns rows for all presets."""
    rows = eligibility_matrix_report()
    assert len(rows) >= 4
    for row in rows:
        assert "preset_id" in row
        assert "routine_types" in row
        for rt in ROUTINE_TYPES:
            assert rt in row["routine_types"]


def test_max_tier_for_routine_under_preset() -> None:
    """Under cautious, digest is suggest_only; under bounded_trusted_routine, digest can be bounded_trusted_real."""
    assert max_tier_for_routine_under_preset("cautious", ROUTINE_TYPE_DIGEST) == "suggest_only"
    assert max_tier_for_routine_under_preset("bounded_trusted_routine", ROUTINE_TYPE_DIGEST) == "bounded_trusted_real"


def test_is_eligible_cautious_digest_suggest() -> None:
    """morning_digest at suggest_only is eligible under cautious."""
    ok, msg = is_eligible("cautious", "morning_digest", "suggest_only")
    assert ok is True


def test_is_eligible_cautious_digest_sandbox_not_eligible() -> None:
    """morning_digest at sandbox_write is not eligible under cautious."""
    ok, msg = is_eligible("cautious", "morning_digest", "sandbox_write")
    assert ok is False
    assert "exceeds" in msg or "Not eligible" in msg


def test_validate_trust_config_no_preset_valid_contracts(tmp_path: Path) -> None:
    """With no active preset, valid contracts yield valid report."""
    c = TrustedRoutineContract(
        contract_id="valid_one",
        routine_id="morning_digest",
        scope="global",
        authority_tier_id="sandbox_write",
        enabled=True,
    )
    save_contracts([c], tmp_path)
    report = validate_trust_config(repo_root=tmp_path)
    assert report.valid is True
    assert len(report.invalid) == 0


def test_validate_trust_config_invalid_contract(tmp_path: Path) -> None:
    """Contract with unknown tier yields invalid issue."""
    c = TrustedRoutineContract(
        contract_id="bad_tier",
        routine_id="r1",
        authority_tier_id="nonexistent_tier",
        enabled=True,
    )
    save_contracts([c], tmp_path)
    report = validate_trust_config(repo_root=tmp_path)
    assert report.valid is False
    assert len(report.invalid) >= 1
    assert any("bad_tier" in i.contract_id for i in report.invalid)


def test_validate_trust_config_unsafe_exceeds_preset(tmp_path: Path) -> None:
    """Contract tier exceeding preset cap yields unsafe issue."""
    c = TrustedRoutineContract(
        contract_id="too_high",
        routine_id="morning_digest",
        scope="global",
        authority_tier_id="sandbox_write",
        enabled=True,
    )
    save_contracts([c], tmp_path)
    report = validate_trust_config(active_preset_id="cautious", repo_root=tmp_path)
    assert report.valid is False
    assert len(report.unsafe) >= 1
    assert any("too_high" in i.contract_id for i in report.unsafe)


def test_format_validation_report() -> None:
    """format_validation_report returns non-empty string."""
    report = TrustValidationReport(valid=True, summary_lines=["Trust configuration is valid."])
    out = format_validation_report(report)
    assert "Trust configuration" in out
    assert "valid" in out.lower()


def test_get_active_preset_id_missing(tmp_path: Path) -> None:
    """get_active_preset_id returns None when file absent."""
    assert get_active_preset_id(tmp_path) is None


def test_get_active_preset_id_present(tmp_path: Path) -> None:
    """get_active_preset_id returns content when file present."""
    (tmp_path / "data/local/trust").mkdir(parents=True)
    (tmp_path / "data/local/trust/active_preset.txt").write_text("cautious", encoding="utf-8")
    assert get_active_preset_id(tmp_path) == "cautious"
