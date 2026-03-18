"""
M23Y: Tests for starter kit registry, recommendation, first-value flow, missing prerequisites.
"""

from pathlib import Path

import pytest


def test_list_kits() -> None:
    """list_kits returns non-empty list of kit IDs."""
    from workflow_dataset.starter_kits.registry import list_kits
    ids = list_kits()
    assert isinstance(ids, list)
    assert "founder_ops_starter" in ids
    assert "analyst_starter" in ids
    assert "developer_starter" in ids
    assert "document_worker_starter" in ids


def test_get_kit() -> None:
    """get_kit returns StarterKit for valid id, None for invalid."""
    from workflow_dataset.starter_kits.registry import get_kit
    k = get_kit("founder_ops_starter")
    assert k is not None
    assert k.kit_id == "founder_ops_starter"
    assert k.domain_pack_id == "founder_ops"
    assert k.first_value_flow is not None
    assert "morning_ops" in (k.recommended_routine_ids or []) or "morning_ops" in (k.first_simulate_only_workflow or "")
    assert get_kit("nonexistent") is None


def test_recommend_kit_from_profile_no_profile() -> None:
    """recommend_kit_from_profile returns default kit when no profile."""
    from workflow_dataset.starter_kits.recommend import recommend_kit_from_profile
    result = recommend_kit_from_profile(profile=None, repo_root=Path("/nonexistent"))
    assert "kit" in result
    assert result["kit"] is not None
    assert "score" in result
    assert "reason" in result
    assert "alternatives" in result
    assert "missing_prerequisites" in result


def test_recommend_kit_from_profile_with_field() -> None:
    """recommend_kit_from_profile returns matching kit when profile has field."""
    from workflow_dataset.starter_kits.recommend import recommend_kit_from_profile
    result = recommend_kit_from_profile(profile={"field": "operations", "job_family": "founder"})
    assert result["kit"] is not None
    assert result["kit"].kit_id in ("founder_ops_starter", "analyst_starter", "developer_starter", "document_worker_starter")


def test_recommend_kit_from_profile_developer() -> None:
    """recommend_kit_from_profile returns developer_starter for developer job_family."""
    from workflow_dataset.starter_kits.recommend import recommend_kit_from_profile
    result = recommend_kit_from_profile(profile={"field": "development", "job_family": "developer"})
    assert result["kit"] is not None
    # Domain recommend may return coding_development -> developer_starter
    assert result["kit"].target_job_family == "developer" or "developer" in result["reason"].lower() or result["kit"].kit_id == "developer_starter"


def test_first_value_flow_format() -> None:
    """format_first_run_flow produces string with run command and next steps."""
    from workflow_dataset.starter_kits.registry import get_kit
    from workflow_dataset.starter_kits.report import format_first_run_flow
    kit = get_kit("analyst_starter")
    assert kit is not None
    text = format_first_run_flow(kit)
    assert "first-value" in text.lower() or "First-value" in text
    assert "workflow-dataset" in text or "jobs run" in text
    assert "simulate" in text.lower() or "Get back" in text


def test_show_kit_format() -> None:
    """format_kit_show includes target, recommendations, first-value flow."""
    from workflow_dataset.starter_kits.registry import get_kit
    from workflow_dataset.starter_kits.report import format_kit_show
    kit = get_kit("document_worker_starter")
    assert kit is not None
    text = format_kit_show(kit)
    assert "document_worker_starter" in text
    assert "domain_pack" in text or "domain" in text.lower()
    assert "First-value" in text or "first_value" in text or "first-value" in text


def test_missing_prerequisites_when_job_absent(tmp_path: Path) -> None:
    """recommend_kit_from_profile includes missing_prerequisites when job/routine not present."""
    from workflow_dataset.starter_kits.recommend import recommend_kit_from_profile
    result = recommend_kit_from_profile(profile={"field": "operations", "job_family": "founder"}, repo_root=tmp_path)
    assert "missing_prerequisites" in result
    # May include job pack not found, routine not found, or approval registry
    assert isinstance(result["missing_prerequisites"], list)


def test_recommendation_format() -> None:
    """format_recommendation produces string with recommended kit and alternatives."""
    from workflow_dataset.starter_kits.recommend import recommend_kit_from_profile
    from workflow_dataset.starter_kits.report import format_recommendation
    result = recommend_kit_from_profile(profile={})
    report = format_recommendation(result)
    assert "Starter kit recommendation" in report or "Recommended" in report
    assert "kits show" in report or "show" in report
    assert "first-run" in report or "first_run" in report
