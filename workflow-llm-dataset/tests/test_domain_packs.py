"""M23U: Tests for domain packs — list, get, recommend, policy filtering, refusal."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.domain_packs import (
    list_domain_packs,
    get_domain_pack,
    recommend_domain_packs,
    filter_models_by_policy,
    resolve_domain_pack_for_field,
    get_allowed_options_for_machine,
)


def test_list_domain_packs() -> None:
    ids = list_domain_packs()
    assert "founder_ops" in ids
    assert "office_admin" in ids
    assert "coding_development" in ids
    assert "document_ocr_heavy" in ids


def test_get_domain_pack() -> None:
    pack = get_domain_pack("founder_ops")
    assert pack is not None
    assert pack.domain_id == "founder_ops"
    assert "weekly_status" in pack.suggested_job_packs
    assert pack.suggested_recipe_id == "retrieval_only"
    assert get_domain_pack("nonexistent") is None


def test_recommend_domain_packs_by_field() -> None:
    recs = recommend_domain_packs(field="operations")
    assert len(recs) >= 1
    top_id = recs[0][0].domain_id
    assert top_id in list_domain_packs()
    recs_founder = recommend_domain_packs(field="founder")
    assert len(recs_founder) >= 1
    assert recs_founder[0][0].domain_id == "founder_ops"


def test_recommend_domain_packs_by_job_family() -> None:
    recs = recommend_domain_packs(job_family="analyst")
    assert len(recs) >= 1


def test_resolve_domain_pack_for_field() -> None:
    pack = resolve_domain_pack_for_field(field="founder", job_family="ops")
    assert pack is not None
    assert pack.domain_id == "founder_ops"
    pack_empty = resolve_domain_pack_for_field(field="", job_family="")
    assert pack_empty is None or pack_empty.domain_id  # may return first with minimal score


def test_get_allowed_options_for_machine() -> None:
    pack = get_domain_pack("founder_ops")
    opts = get_allowed_options_for_machine(repo_root=Path("/tmp"), tier="local_standard", domain_pack=pack)
    assert "allowed_model_classes" in opts
    assert "llama3.2" in opts["allowed_model_classes"]
    assert opts["tier"] == "local_standard"
    opts_minimal = get_allowed_options_for_machine(tier="minimal_eval", domain_pack=pack)
    assert opts_minimal["allowed_model_classes"] == []
    assert "degraded" in opts_minimal


def test_filter_models_by_policy() -> None:
    catalog = [
        {"name": "llama3.2:latest", "size": "2G"},
        {"name": "mistral:7b", "size": "4G"},
        {"name": "other:model", "size": "1G"},
    ]
    allowed = ["llama3.2", "mistral"]
    filtered = filter_models_by_policy(catalog, allowed, safety_posture="simulate_only")
    assert len(filtered) == 2
    names = [m.get("name", "") for m in filtered]
    assert any("llama" in n for n in names)
    assert any("mistral" in n for n in names)
    assert filter_models_by_policy(catalog, [], "simulate_only") == []


def test_unsupported_or_refusal() -> None:
    pack = get_domain_pack("nonexistent_domain")
    assert pack is None
    recipe = get_domain_pack("founder_ops")
    assert recipe is not None
    opts = get_allowed_options_for_machine(tier="minimal_eval", domain_pack=recipe)
    assert opts["allowed_model_classes"] == []
