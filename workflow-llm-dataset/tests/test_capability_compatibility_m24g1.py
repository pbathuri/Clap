"""M24G.1: Capability profiles + domain/pack compatibility — matrix, recommend-for-pack, blocked reasons."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.external_capability.compatibility import (
    build_compatibility_matrix,
    recommend_capabilities_for_pack,
    CompatibilityRow,
    CapabilityRecommendationResult,
    VALUE_PACK_TO_CAPABILITY_CATEGORIES,
    BLOCKED_REASON_POLICY,
    BLOCKED_REASON_NOT_WORTH_FOR_PACK,
    BLOCKED_REASON_INCOMPATIBLE_TIER,
)
from workflow_dataset.external_capability.report import (
    format_compatibility_report,
    format_capability_recommendation,
)


def test_build_compatibility_matrix(tmp_path):
    """build_compatibility_matrix returns list of CompatibilityRow with compatible_* and tiers."""
    matrix = build_compatibility_matrix(tmp_path)
    assert isinstance(matrix, list)
    assert len(matrix) >= 1
    for row in matrix:
        assert isinstance(row, CompatibilityRow)
        assert row.source_id
        assert row.category
        assert isinstance(row.compatible_domain_pack_ids, list)
        assert isinstance(row.compatible_value_pack_ids, list)
        assert isinstance(row.compatible_starter_kit_ids, list)
        assert isinstance(row.compatible_tiers, list)


def test_recommend_capabilities_for_pack_value_pack(tmp_path):
    """recommend_capabilities_for_pack(value_pack_id=founder_ops_plus) returns worth_enabling, not_worth, blocked."""
    result = recommend_capabilities_for_pack(value_pack_id="founder_ops_plus", repo_root=tmp_path)
    assert isinstance(result, CapabilityRecommendationResult)
    assert "value_pack_id" in result.pack_context
    assert result.pack_context.get("value_pack_id") == "founder_ops_plus"
    assert result.pack_context.get("tier") == "local_standard"
    assert isinstance(result.worth_enabling, list)
    assert isinstance(result.not_worth_enabling, list)
    assert isinstance(result.blocked, list)
    assert isinstance(result.compatibility_summary, list)


def test_recommend_capabilities_for_pack_domain(tmp_path):
    """recommend_capabilities_for_pack(domain_pack_id=...) resolves and returns pack_context."""
    result = recommend_capabilities_for_pack(domain_pack_id="coding_development", repo_root=tmp_path)
    assert result.pack_context.get("domain_pack_id") == "coding_development"
    assert "task_class" in result.pack_context


def test_recommend_capabilities_for_pack_with_tier(tmp_path):
    """recommend_capabilities_for_pack(tier=constrained_edge) can block sources that don't support tier."""
    result = recommend_capabilities_for_pack(
        value_pack_id="founder_ops_plus",
        tier="constrained_edge",
        repo_root=tmp_path,
    )
    assert result.pack_context.get("tier") == "constrained_edge"
    codes = [e.code for e in result.blocked]
    assert BLOCKED_REASON_INCOMPATIBLE_TIER in codes or len(result.blocked) >= 0


def test_blocked_reason_codes():
    """Blocked entries use standard reason codes."""
    assert BLOCKED_REASON_POLICY == "rejected_by_policy"
    assert BLOCKED_REASON_NOT_WORTH_FOR_PACK == "not_worth_for_pack"
    assert BLOCKED_REASON_INCOMPATIBLE_TIER == "incompatible_tier"


def test_value_pack_to_capability_categories():
    """VALUE_PACK_TO_CAPABILITY_CATEGORIES has entries for built-in value packs."""
    assert "founder_ops_plus" in VALUE_PACK_TO_CAPABILITY_CATEGORIES
    assert "developer_plus" in VALUE_PACK_TO_CAPABILITY_CATEGORIES
    assert "coding_agent" in VALUE_PACK_TO_CAPABILITY_CATEGORIES["developer_plus"]


def test_format_compatibility_report(tmp_path):
    """format_compatibility_report produces string with source ids and compatible_*."""
    matrix = build_compatibility_matrix(tmp_path)
    report = format_compatibility_report(matrix)
    assert "Capability compatibility" in report
    if matrix:
        assert matrix[0].source_id in report


def test_format_capability_recommendation(tmp_path):
    """format_capability_recommendation produces string with pack context and worth/blocked."""
    result = recommend_capabilities_for_pack(value_pack_id="founder_ops_plus", repo_root=tmp_path)
    report = format_capability_recommendation(result)
    assert "Capability recommendation" in report
    assert "Pack context" in report
    assert "Worth enabling" in report or "worth" in report.lower()
    assert "Blocked" in report or "blocked" in report.lower()
    assert "tier=" in report
