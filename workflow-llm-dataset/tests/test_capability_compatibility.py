"""M24G.1: Capability profiles and domain/pack compatibility — matrix, recommendation, worth-enabling, blocked reasoning."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.external_capability.compatibility import (
    TASK_CLASS_TO_CAPABILITY_CATEGORIES,
    DOMAIN_PACK_TO_CAPABILITY_CATEGORIES,
    build_compatibility_matrix,
    recommend_capabilities_for_pack,
    CompatibilityRow,
    CapabilityRecommendationResult,
    CapabilityRecommendationEntry,
)
from workflow_dataset.external_capability.report import format_compatibility_report, format_capability_recommendation


def test_task_class_mapping():
    assert "desktop_copilot" in TASK_CLASS_TO_CAPABILITY_CATEGORIES
    assert "ollama_model" in TASK_CLASS_TO_CAPABILITY_CATEGORIES["desktop_copilot"]
    assert "coding_agent" in TASK_CLASS_TO_CAPABILITY_CATEGORIES["codebase_task"]


def test_domain_pack_mapping():
    assert "founder_ops" in DOMAIN_PACK_TO_CAPABILITY_CATEGORIES
    assert "coding_development" in DOMAIN_PACK_TO_CAPABILITY_CATEGORIES
    assert "coding_agent" in DOMAIN_PACK_TO_CAPABILITY_CATEGORIES["coding_development"]


def test_build_compatibility_matrix(tmp_path):
    matrix = build_compatibility_matrix(repo_root=tmp_path)
    assert isinstance(matrix, list)
    for row in matrix:
        assert isinstance(row, CompatibilityRow)
        assert row.source_id
        assert row.category
        assert isinstance(row.compatible_domain_pack_ids, list)
        assert isinstance(row.compatible_value_pack_ids, list)
        assert isinstance(row.compatible_starter_kit_ids, list)
        assert isinstance(row.compatible_tiers, list)


def test_recommend_capabilities_for_pack_value_pack(tmp_path):
    result = recommend_capabilities_for_pack(value_pack_id="founder_ops_plus", repo_root=tmp_path)
    assert isinstance(result, CapabilityRecommendationResult)
    assert result.pack_context.get("value_pack_id") == "founder_ops_plus"
    assert result.pack_context.get("domain_pack_id") == "founder_ops"
    assert "desktop_copilot" in (result.pack_context.get("task_class") or "")
    assert isinstance(result.worth_enabling, list)
    assert isinstance(result.not_worth_enabling, list)
    assert isinstance(result.blocked, list)
    assert isinstance(result.compatibility_summary, list)


def test_recommend_capabilities_for_pack_domain(tmp_path):
    result = recommend_capabilities_for_pack(domain_pack_id="founder_ops", repo_root=tmp_path)
    assert result.pack_context.get("domain_pack_id") == "founder_ops"
    assert isinstance(result.worth_enabling, list)
    assert isinstance(result.not_worth_enabling, list)
    assert isinstance(result.blocked, list)


def test_recommend_capabilities_for_pack_developer(tmp_path):
    result = recommend_capabilities_for_pack(value_pack_id="developer_plus", repo_root=tmp_path)
    assert result.pack_context.get("value_pack_id") == "developer_plus"
    assert result.pack_context.get("task_class") == "codebase_task"
    for e in result.worth_enabling:
        assert isinstance(e, CapabilityRecommendationEntry)
        assert e.source_id
        assert e.reason


def test_format_compatibility_report(tmp_path):
    matrix = build_compatibility_matrix(repo_root=tmp_path)
    text = format_compatibility_report(matrix)
    assert "Capability compatibility" in text
    assert "category=" in text or "domains:" in text


def test_format_capability_recommendation(tmp_path):
    result = recommend_capabilities_for_pack(value_pack_id="founder_ops_plus", repo_root=tmp_path)
    text = format_capability_recommendation(result)
    assert "Capability recommendation" in text
    assert "Worth enabling" in text
    assert "Not worth" in text
    assert "Blocked" in text
    assert "founder_ops" in text or "founder_ops_plus" in text
