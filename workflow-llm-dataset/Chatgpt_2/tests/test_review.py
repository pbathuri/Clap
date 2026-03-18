"""
Tests for M12 review, refinement, variant management, and adoption bridge.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.review.review_models import (
    GeneratedArtifactReview,
    VariantRecord,
    RefineRequest,
    AdoptionCandidate,
)
from workflow_dataset.review.artifact_preview import (
    preview_artifact,
    build_summary,
)
from workflow_dataset.review.variant_manager import (
    create_variant_record,
    compare_variants,
    set_preferred_variant,
)
from workflow_dataset.review.refine_request_builder import build_refine_request
from workflow_dataset.review.document_refiner import refine_document, _deterministic_refine
from workflow_dataset.review.adoption_bridge import (
    create_adoption_candidate,
    save_adoption_candidate,
    load_adoption_candidate,
    build_apply_plan_for_adoption,
    list_adoption_candidates,
)
from workflow_dataset.review.version_store import (
    save_variant_record,
    load_variant_record,
    list_variants_for_generation,
)


@pytest.fixture
def tmp_review_root(tmp_path: Path) -> Path:
    return tmp_path / "review"


@pytest.fixture
def sample_md(tmp_path: Path) -> Path:
    p = tmp_path / "creative_brief_generated.md"
    p.write_text("# Creative Brief\n\n*Generated*\n\n## Brief\n\nA short film.\n", encoding="utf-8")
    return p


def test_preview_artifact(sample_md: Path) -> None:
    review, body = preview_artifact(sample_md, generation_id="gen_1")
    assert review.artifact_type == "markdown"
    assert "Creative Brief" in body
    assert review.generation_id == "gen_1"


def test_build_summary(sample_md: Path) -> None:
    content = sample_md.read_text(encoding="utf-8")
    s = build_summary(sample_md, content, "markdown")
    assert "creative_brief_generated" in s
    assert "markdown" in s


def test_variant_record_create_and_save(tmp_review_root: Path) -> None:
    rec = create_variant_record(
        base_artifact_id="art_1",
        generation_id="gen_1",
        output_paths=[str(tmp_review_root / "refined.md")],
        variant_type="refined",
        revision_note="Tightened tone",
        used_llm_refinement=False,
    )
    assert rec.variant_id
    assert rec.generation_id == "gen_1"
    save_variant_record(rec, tmp_review_root)
    loaded = load_variant_record(rec.variant_id, tmp_review_root)
    assert loaded is not None
    assert loaded.revision_note == "Tightened tone"
    listed = list_variants_for_generation("gen_1", tmp_review_root)
    assert len(listed) == 1


def test_compare_variants(sample_md: Path, tmp_path: Path) -> None:
    other = tmp_path / "other.md"
    other.write_text("# Other\n\nDifferent content.\n", encoding="utf-8")
    result = compare_variants(sample_md, other)
    assert result["same_content"] is False
    assert result["line_count_a"] >= 1
    assert result["line_count_b"] >= 1


def test_build_refine_request() -> None:
    req = build_refine_request(
        artifact_id="art_1",
        generation_id="gen_1",
        use_llm=False,
        user_instruction="Add a section on risks",
    )
    assert req.refine_id
    assert req.refine_mode == "deterministic"
    assert "risks" in req.user_instruction


def test_deterministic_refine() -> None:
    text = "# Doc\n\nBody.\n"
    out = _deterministic_refine(text, user_instruction="Add revision note.", style_constraints=["formal"])
    assert "Revision notes" in out
    assert "Add revision note" in out
    assert "formal" in out


def test_refine_document(sample_md: Path, tmp_path: Path) -> None:
    workspace_path = tmp_path / "ws"
    workspace_path.mkdir()
    req = build_refine_request("art_1", "gen_1", use_llm=False, user_instruction="Clarify scope.")
    ok, msg, paths, variant = refine_document(
        sample_md,
        workspace_path,
        req,
        generation_id="gen_1",
        review_store_path=tmp_path / "review",
    )
    assert ok is True
    assert len(paths) >= 1
    assert (workspace_path / "refined").exists()
    assert variant is not None
    assert variant.used_llm_refinement is False


def test_adoption_candidate_and_bridge(tmp_path: Path) -> None:
    ws = tmp_path / "gen_ws"
    ws.mkdir()
    (ws / "out.md").write_text("content", encoding="utf-8")
    candidate = create_adoption_candidate(
        generation_id="gen_1",
        workspace_path=ws,
        candidate_paths=["out.md"],
    )
    assert candidate.adoption_id
    assert candidate.ready_for_apply
    save_adoption_candidate(candidate, tmp_path / "review")
    loaded = load_adoption_candidate(candidate.adoption_id, tmp_path / "review")
    assert loaded is not None
    assert loaded.candidate_paths == ["out.md"]
    target = tmp_path / "target"
    target.mkdir()
    plan, err = build_apply_plan_for_adoption(candidate, target)
    assert err == ""
    assert plan is not None
    assert plan.estimated_file_count >= 1
    listed = list_adoption_candidates(tmp_path / "review", generation_id="gen_1")
    assert len(listed) == 1
