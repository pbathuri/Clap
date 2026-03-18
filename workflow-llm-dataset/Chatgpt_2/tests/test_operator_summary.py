"""M23U: Tests for operator summary — summary generation, machine/resource filtering."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.onboarding.operator_summary import (
    build_operator_summary,
    format_operator_summary_md,
)
from workflow_dataset.onboarding.user_work_profile import UserWorkProfile, save_user_work_profile


def test_build_operator_summary_empty_profile() -> None:
    summary = build_operator_summary(user_profile=None, bootstrap_profile=None, repo_root=None)
    assert "recommended_domain_packs" in summary
    assert "recommended_model_classes" in summary
    assert "safety_posture" in summary
    assert summary["safety_posture"] == "simulate_only"


def test_build_operator_summary_with_field() -> None:
    user = UserWorkProfile(field="operations", job_family="founder")
    summary = build_operator_summary(user_profile=user, bootstrap_profile=None, repo_root=None)
    assert len(summary["recommended_domain_packs"]) >= 1
    assert summary["recommended_specialization_route"] in ("retrieval_only", "adapter_finetune", "")
    assert "local" in str(summary["data_usage"]).lower() or summary["data_usage"]


def test_build_operator_summary_with_catalog() -> None:
    user = UserWorkProfile(field="founder", job_family="ops")
    catalog = [{"name": "llama3.2:latest"}, {"name": "other:model"}]
    summary = build_operator_summary(user_profile=user, catalog_entries=catalog, repo_root=None)
    assert "catalog_filtered_models" in summary
    assert isinstance(summary["catalog_filtered_models"], list)


def test_format_operator_summary_md() -> None:
    summary = {
        "recommended_domain_packs": [{"domain_id": "founder_ops", "name": "Founder ops", "score": 0.8}],
        "recommended_model_classes": ["llama3.2"],
        "recommended_embedding_classes": ["nomic-embed-text"],
        "recommended_ocr_vision_classes": [],
        "recommended_specialization_route": "retrieval_only",
        "data_usage": ["local user data only"],
        "simulate_only_scope": ["All real apply requires approval."],
        "training_inference_path": "Retrieval-only by default.",
        "safety_posture": "simulate_only",
        "machine_tier": "unknown",
    }
    md = format_operator_summary_md(summary)
    assert "Operator summary" in md
    assert "founder_ops" in md
    assert "retrieval_only" in md
    assert "simulate_only" in md


def test_machine_tier_in_summary(tmp_path: Path) -> None:
    user = UserWorkProfile(field="operations", preferred_edge_tier="constrained_edge")
    summary = build_operator_summary(user_profile=user, repo_root=tmp_path)
    assert summary.get("machine_tier") == "constrained_edge" or "degraded" in str(summary.get("simulate_only_scope", []))
