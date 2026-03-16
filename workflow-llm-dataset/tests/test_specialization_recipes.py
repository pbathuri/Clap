"""M23U: Tests for specialization recipes — build, explain, licensing metadata, no auto-download/train."""

from __future__ import annotations

import pytest

from workflow_dataset.specialization import (
    list_recipes,
    get_recipe,
    build_recipe_for_domain_pack,
    explain_recipe,
)
from workflow_dataset.specialization.recipe_models import SpecializationRecipe


def test_list_recipes() -> None:
    ids = list_recipes()
    assert "retrieval_only" in ids
    assert "adapter_finetune" in ids
    assert "embedding_refresh" in ids
    assert "ocr_doc" in ids
    assert "coding_agent" in ids


def test_get_recipe() -> None:
    r = get_recipe("retrieval_only")
    assert r is not None
    assert r.recipe_id == "retrieval_only"
    assert r.mode == "retrieval_only"
    assert r.auto_download is False
    assert r.auto_train is False
    assert get_recipe("nonexistent") is None


def test_recipe_has_no_auto_flags() -> None:
    for rid in list_recipes():
        r = get_recipe(rid)
        assert r is not None
        assert r.auto_download is False, f"{rid} must not auto_download"
        assert r.auto_train is False, f"{rid} must not auto_train"


def test_build_recipe_for_domain_pack() -> None:
    recipe = build_recipe_for_domain_pack("founder_ops")
    assert recipe is not None
    assert recipe.recipe_id == "retrieval_only"
    assert build_recipe_for_domain_pack("nonexistent") is None


def test_explain_recipe() -> None:
    out = explain_recipe("retrieval_only")
    assert out["found"] is True
    assert out["recipe_id"] == "retrieval_only"
    assert out["auto_download"] is False
    assert out["auto_train"] is False
    assert "steps_summary" in out
    assert "licensing_compliance_metadata" in out
    out_missing = explain_recipe("nonexistent_recipe_id")
    assert out_missing["found"] is False


def test_licensing_metadata_present() -> None:
    r = get_recipe("adapter_finetune")
    assert r is not None
    assert "licensing_compliance_metadata" in r.__dict__ or hasattr(r, "licensing_compliance_metadata")
    assert isinstance(r.licensing_compliance_metadata, dict)
