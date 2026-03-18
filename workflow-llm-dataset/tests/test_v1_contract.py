"""
M50A–M50D: Tests for v1 contract freeze — contract model, surface classification, workflows, explain, freeze report.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.v1_contract import (
    build_stable_v1_contract,
    get_v1_surfaces_classification,
    list_v1_core,
    list_v1_advanced,
    list_quarantined,
    list_excluded,
    explain_surface,
    build_freeze_report,
    format_freeze_report_text,
    build_stable_v1_communication_pack,
    build_experimental_quarantine_summary,
    format_safe_vs_exploratory_text,
    v1_contract_slice,
)
from workflow_dataset.v1_contract.models import (
    StableV1Contract,
    V1CoreSurface,
    StableWorkflowContract,
    SupportCommitmentNote,
)


def test_build_stable_v1_contract_no_cut(tmp_path: Path) -> None:
    """Without active cut, contract is built from default vertical (founder_operator) freeze."""
    contract = build_stable_v1_contract(tmp_path)
    assert contract.contract_id == "stable_v1_contract"
    assert contract.vertical_id in ("founder_operator", "")
    assert contract.has_active_cut is False
    assert isinstance(contract.v1_core_surfaces, list)
    assert isinstance(contract.v1_advanced_surfaces, list)
    assert isinstance(contract.quarantined_surfaces, list)
    assert isinstance(contract.excluded_surfaces, list)
    assert contract.stable_workflow_contract is None or isinstance(contract.stable_workflow_contract, StableWorkflowContract)
    assert contract.support_commitment_note is None or isinstance(contract.support_commitment_note, SupportCommitmentNote)


def test_contract_to_dict(tmp_path: Path) -> None:
    """Contract serializes to dict."""
    contract = build_stable_v1_contract(tmp_path)
    d = contract.to_dict()
    assert "contract_id" in d
    assert "vertical_id" in d
    assert "v1_core_surfaces" in d
    assert "quarantined_surfaces" in d
    assert "excluded_surfaces" in d


def test_get_v1_surfaces_classification(tmp_path: Path) -> None:
    """Classification returns v1_core, v1_advanced, quarantined, excluded with counts."""
    contract = build_stable_v1_contract(tmp_path)
    classification = get_v1_surfaces_classification(contract)
    assert "v1_core" in classification
    assert "v1_core_count" in classification
    assert "v1_advanced" in classification
    assert "quarantined" in classification
    assert "excluded" in classification
    assert classification["v1_core_count"] == len(classification["v1_core"])


def test_explain_surface_core_or_unknown(tmp_path: Path) -> None:
    """Explain returns classification and may_rely_on for known or unknown surface."""
    contract = build_stable_v1_contract(tmp_path)
    # If we have at least one core surface, explain it
    core_ids = list_v1_core(contract)
    if core_ids:
        out = explain_surface(core_ids[0], contract)
        assert out["classification"] == "v1_core"
        assert out["may_rely_on"] is True
    out_unknown = explain_surface("nonexistent_surface_xyz", contract)
    assert out_unknown["classification"] in ("unknown", "excluded")
    assert "may_rely_on" in out_unknown


def test_explain_surface_excluded(tmp_path: Path) -> None:
    """Explain excluded surface returns classification excluded."""
    contract = build_stable_v1_contract(tmp_path)
    excluded_ids = list_excluded(contract)
    if excluded_ids:
        out = explain_surface(excluded_ids[0], contract)
        assert out["classification"] == "excluded"
        assert out["may_rely_on"] is False


def test_build_freeze_report(tmp_path: Path) -> None:
    """Freeze report has in_v1, quarantined, excluded, may_rely_on_summary, next_freeze_action."""
    report = build_freeze_report(repo_root=tmp_path)
    assert "in_v1_surface_ids" in report
    assert "in_v1_count" in report
    assert "quarantined_surface_ids" in report
    assert "excluded_surface_ids" in report
    assert "may_rely_on_summary" in report
    assert "next_freeze_action" in report
    assert "vertical_id" in report


def test_format_freeze_report_text(tmp_path: Path) -> None:
    """Format freeze report returns string with Vertical, In v1, Quarantined, Excluded, Next."""
    contract = build_stable_v1_contract(tmp_path)
    report = build_freeze_report(contract=contract)
    text = format_freeze_report_text(report)
    assert "V1 freeze report" in text
    assert "Vertical" in text
    assert "In v1" in text or "in_v1" in text
    assert "Quarantined" in text
    assert "Excluded" in text
    assert "Next" in text


def test_v1_contract_slice(tmp_path: Path) -> None:
    """Mission control slice has vertical_id, has_active_cut, counts, next_freeze_action, M50D.1 pack/summary."""
    slice_data = v1_contract_slice(tmp_path)
    assert "vertical_id" in slice_data
    assert "has_active_cut" in slice_data
    assert "v1_core_count" in slice_data
    assert "quarantined_count" in slice_data
    assert "excluded_count" in slice_data
    assert "next_freeze_action" in slice_data
    assert "stable_pack_headline" in slice_data
    assert "experimental_summary_count" in slice_data
    assert isinstance(slice_data["experimental_summary_count"], int)


def test_list_v1_core_advanced_quarantined_excluded(tmp_path: Path) -> None:
    """List helpers return surface id lists."""
    contract = build_stable_v1_contract(tmp_path)
    core = list_v1_core(contract)
    advanced = list_v1_advanced(contract)
    quar = list_quarantined(contract)
    excl = list_excluded(contract)
    assert isinstance(core, list)
    assert isinstance(advanced, list)
    assert isinstance(quar, list)
    assert isinstance(excl, list)
    # No overlap between in-v1 and excluded
    in_v1 = set(core) | set(advanced)
    assert not (in_v1 & set(excl)), "excluded should not overlap with in_v1"


def test_build_stable_v1_communication_pack(tmp_path: Path) -> None:
    """M50D.1: Stable v1 communication pack has safe_to_rely_on, do_not_rely_on, headline, summaries."""
    contract = build_stable_v1_contract(tmp_path)
    pack = build_stable_v1_communication_pack(contract=contract)
    assert pack.pack_id == "stable_v1_communication_pack"
    assert pack.generated_at_utc
    assert pack.headline
    assert isinstance(pack.safe_to_rely_on, list)
    assert isinstance(pack.do_not_rely_on, list)
    assert pack.stable_surfaces_summary
    assert pack.support_commitment_one_liner
    assert pack.exploratory_summary_one_liner
    # Counts align with contract
    assert len(pack.safe_to_rely_on) >= len(contract.v1_core_surfaces) + len(contract.v1_advanced_surfaces)
    assert len(pack.do_not_rely_on) == len(contract.quarantined_surfaces) + len(contract.excluded_surfaces)
    d = pack.to_dict()
    assert "safe_to_rely_on" in d and "do_not_rely_on" in d


def test_build_experimental_quarantine_summary(tmp_path: Path) -> None:
    """M50D.1: Experimental quarantine summary has items, count matches quarantined + excluded."""
    contract = build_stable_v1_contract(tmp_path)
    summary = build_experimental_quarantine_summary(contract=contract)
    assert summary.summary_id == "experimental_quarantine_summary"
    assert summary.generated_at_utc
    assert summary.headline
    assert summary.one_liner
    assert summary.count == len(contract.quarantined_surfaces) + len(contract.excluded_surfaces)
    assert len(summary.items) == summary.count
    for it in summary.items:
        assert "surface_id" in it or "label" in it
        assert "why_exploratory" in it
    d = summary.to_dict()
    assert "items" in d and "count" in d


def test_format_safe_vs_exploratory_text(tmp_path: Path) -> None:
    """M50D.1: format_safe_vs_exploratory_text returns operator-facing string."""
    text = format_safe_vs_exploratory_text(repo_root=tmp_path)
    assert "Safe to rely on" in text or "safe" in text.lower()
    assert "exploratory" in text.lower() or "Do not rely" in text
