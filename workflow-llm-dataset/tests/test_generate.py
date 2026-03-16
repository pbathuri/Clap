"""
Tests for M10 generation scaffolding: context, style pack, prompt pack, asset plan, store, manifest.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.generate.generate_models import (
    GenerationRequest,
    StylePack,
    PromptPack,
    AssetPlan,
    VariantPlan,
    GenerationManifest,
    GenerationStatus,
    BackendExecutionRecord,
)
from workflow_dataset.generate.generation_context import build_generation_context
from workflow_dataset.generate.style_pack_builder import build_style_pack_from_context
from workflow_dataset.generate.prompt_pack_builder import build_prompt_pack
from workflow_dataset.generate.asset_plan_builder import build_asset_plan
from workflow_dataset.generate.variant_plan_builder import build_variant_plan
from workflow_dataset.generate.generation_manifest import build_generation_manifest
from workflow_dataset.generate.sandbox_generation_store import (
    save_generation_request,
    save_style_pack,
    save_prompt_pack,
    save_asset_plan,
    save_variant_plan,
    save_generation_manifest,
    list_generation_requests,
    load_generation_manifest,
    load_packs_for_manifest,
)
from workflow_dataset.generate.backend_registry import (
    get_backend,
    register_backend,
    execute_generation,
    list_backends,
    BackendCapability,
)
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


@pytest.fixture
def tmp_generation_root(tmp_path: Path) -> Path:
    return tmp_path / "generation"


def test_build_generation_context_empty(tmp_path: Path) -> None:
    """With no graph/dirs, context has empty lists."""
    ctx = build_generation_context(
        graph_path=tmp_path / "nonexistent.sqlite",
        style_signals_dir=tmp_path / "style",
        parsed_artifacts_dir=tmp_path / "parsed",
        style_profiles_dir=tmp_path / "profiles",
        suggestions_dir=tmp_path / "suggestions",
        draft_structures_dir=tmp_path / "drafts",
        setup_session_id="",
        project_id="",
        domain_filter="",
    )
    assert "projects" in ctx
    assert "style_profiles" in ctx
    assert "summary" in ctx
    assert ctx["summary"]["n_profiles"] == 0


def test_build_style_pack_from_context_empty() -> None:
    """Empty context still produces a valid StylePack."""
    ctx = {"style_profiles": [], "imitation_candidates": [], "project_id": "", "domain_filter": ""}
    pack = build_style_pack_from_context(ctx, project_id="", domain="")
    assert pack.style_pack_id
    assert isinstance(pack.naming_patterns, list)
    assert isinstance(pack.style_profile_refs, list)


def test_build_prompt_pack() -> None:
    """PromptPack has required fields."""
    ctx = {"projects": [], "summary": {}, "domain_filter": "creative"}
    pp = build_prompt_pack("gen_1", "image", context=ctx, style_pack=None)
    assert pp.prompt_pack_id
    assert pp.generation_id == "gen_1"
    assert pp.prompt_family == "image"
    assert pp.prompt_text
    assert "Do not fabricate" in (pp.negative_constraints or [""])[0]


def test_build_asset_plan() -> None:
    """AssetPlan has target_outputs and lists."""
    ctx = {"drafts": [], "summary": {}, "domain_filter": "creative", "style_profiles": []}
    ap = build_asset_plan("gen_1", context=ctx, style_pack=None, generation_type="image_pack")
    assert ap.asset_plan_id
    assert ap.generation_id == "gen_1"
    assert isinstance(ap.target_outputs, list)
    assert isinstance(ap.shot_list, list)


def test_build_variant_plan() -> None:
    """VariantPlan for report has variant_type and narrative_outline (variants may be empty with minimal context)."""
    ctx = {"drafts": [], "summary": {}, "domain_filter": "finance"}
    vp = build_variant_plan("gen_1", context=ctx, variant_type="report", style_pack=None)
    assert vp.variant_plan_id
    assert vp.variant_type == "report"
    assert len(vp.narrative_outline) > 0
    assert isinstance(vp.variants, list)


def test_build_generation_manifest() -> None:
    """GenerationManifest aggregates refs."""
    ts = utc_now_iso()
    req = GenerationRequest(generation_id="gen_1", created_utc=ts)
    sp = StylePack(style_pack_id="sp_1", created_utc=ts)
    pp = PromptPack(prompt_pack_id="pp_1", generation_id="gen_1", created_utc=ts)
    ap = AssetPlan(asset_plan_id="ap_1", generation_id="gen_1", created_utc=ts)
    manifest = build_generation_manifest(
        request=req,
        workspace_path="/tmp/ws",
        style_packs=[sp],
        prompt_packs=[pp],
        asset_plans=[ap],
        variant_plans=[],
    )
    assert manifest.manifest_id
    assert manifest.generation_id == "gen_1"
    assert manifest.style_pack_refs == ["sp_1"]
    assert manifest.prompt_pack_refs == ["pp_1"]
    assert manifest.asset_plan_refs == ["ap_1"]


def test_save_and_load_manifest(tmp_generation_root: Path) -> None:
    """Persist and load generation manifest."""
    ts = utc_now_iso()
    manifest = GenerationManifest(
        manifest_id="gm_test1",
        generation_id="gen_1",
        workspace_path=str(tmp_generation_root),
        style_pack_refs=["sp_1"],
        prompt_pack_refs=[],
        asset_plan_refs=[],
        created_utc=ts,
    )
    save_generation_manifest(manifest, tmp_generation_root)
    loaded = load_generation_manifest("gm_test1", tmp_generation_root)
    assert loaded is not None
    assert loaded.manifest_id == "gm_test1"
    assert loaded.generation_id == "gen_1"


def test_save_request_and_list(tmp_generation_root: Path) -> None:
    """Save generation request and list."""
    ts = utc_now_iso()
    req = GenerationRequest(
        generation_id="gen_list_test",
        session_id="s1",
        project_id="p1",
        generation_type="image_pack",
        created_utc=ts,
    )
    save_generation_request(req, tmp_generation_root)
    items = list_generation_requests(tmp_generation_root, limit=10)
    assert any(g["generation_id"] == "gen_list_test" for g in items)
    filtered = list_generation_requests(tmp_generation_root, session_id="s1", project_id="p1")
    assert any(g["generation_id"] == "gen_list_test" for g in filtered)


def test_backend_registry_mock(tmp_path: Path) -> None:
    """Mock backend is registered and executable; returns (ok, msg, paths, record)."""
    backend = get_backend("mock")
    assert backend is not None
    assert "execute" in backend
    ts = utc_now_iso()
    req = GenerationRequest(generation_id="gen_1", created_utc=ts)
    manifest = GenerationManifest(manifest_id="gm_1", generation_id="gen_1", created_utc=ts)
    ok, msg, paths, rec = execute_generation("mock", req, manifest, tmp_path, [], [])
    assert ok is True
    assert "Mock" in msg or "placeholder" in msg.lower()
    assert isinstance(paths, list)
    assert len(paths) >= 1
    assert rec is not None
    assert rec.backend_name == "mock"
    assert rec.execution_status == "success"


def test_backend_unknown() -> None:
    """Unknown backend returns False and an execution record."""
    ts = utc_now_iso()
    req = GenerationRequest(generation_id="gen_1", created_utc=ts)
    manifest = GenerationManifest(manifest_id="gm_1", generation_id="gen_1", created_utc=ts)
    ok, msg, paths, rec = execute_generation("nonexistent_backend_xyz", req, manifest, Path("/tmp"), [], [])
    assert ok is False
    assert "not registered" in msg or "Backend" in msg
    assert paths == []
    assert rec is not None
    assert rec.execution_status == "failed"


def test_list_backends() -> None:
    """list_backends returns at least mock; may include document/image_demo if package imported."""
    backends = list_backends()
    names = [b.backend_name for b in backends]
    assert "mock" in names
    assert all(hasattr(b, "supported_families") for b in backends)


def test_document_backend_produces_files(tmp_path: Path) -> None:
    """Document backend writes real markdown from prompt packs."""
    from workflow_dataset.generate.backends.document_backend import execute_document_backend

    ts = utc_now_iso()
    req = GenerationRequest(generation_id="gen_doc", created_utc=ts)
    pp = PromptPack(
        prompt_pack_id="pp_1",
        generation_id="gen_doc",
        prompt_family="creative_brief",
        prompt_text="A short film about resilience.",
        structural_constraints=["3 acts", "under 5 min"],
        created_utc=ts,
    )
    manifest = GenerationManifest(
        manifest_id="gm_doc",
        generation_id="gen_doc",
        workspace_path=str(tmp_path),
        prompt_pack_refs=["pp_1"],
        prompt_packs=[pp],
    )
    ok, msg, paths, rec = execute_document_backend(
        req, manifest, tmp_path, [pp], [], [], use_llm=False, allow_fallback=True
    )
    assert ok is True
    assert rec is not None
    assert rec.execution_status == "success"
    assert len(paths) >= 1
    out = tmp_path / "creative_brief_generated.md"
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "creative brief" in content.lower() or "Creative" in content
    assert "resilience" in content
    assert "3 acts" in content


def test_image_demo_backend_produces_artifacts(tmp_path: Path) -> None:
    """Image demo backend writes storyboard frames and/or prompt_cards.html."""
    from workflow_dataset.generate.backends.image_demo_backend import execute_image_demo_backend

    ts = utc_now_iso()
    req = GenerationRequest(generation_id="gen_img", created_utc=ts)
    pp = PromptPack(
        prompt_pack_id="pp_1",
        generation_id="gen_img",
        prompt_family="image",
        prompt_text="Hero shot at sunset",
        created_utc=ts,
    )
    manifest = GenerationManifest(
        manifest_id="gm_img",
        generation_id="gen_img",
        workspace_path=str(tmp_path),
        prompt_pack_refs=["pp_1"],
        prompt_packs=[pp],
    )
    ok, msg, paths, rec = execute_image_demo_backend(
        req, manifest, tmp_path, [pp], [], [], use_llm=False, allow_fallback=True
    )
    assert ok is True
    assert rec is not None
    assert rec.execution_status == "success"
    assert len(paths) >= 1
    # Either storyboard_frames/ or prompt_cards.html
    has_html = (tmp_path / "prompt_cards.html").exists()
    has_frames = (tmp_path / "storyboard_frames").exists()
    assert has_html or has_frames or len(paths) > 0


def test_manifest_persists_execution_records(tmp_generation_root: Path) -> None:
    """Manifest with execution_records and generated_output_paths round-trips."""
    ts = utc_now_iso()
    rec = BackendExecutionRecord(
        backend_name="document",
        backend_version="1.0",
        execution_status="success",
        generated_output_paths=[str(tmp_generation_root / "out.md")],
        used_llm=False,
        used_fallback=True,
        executed_utc=ts,
    )
    manifest = GenerationManifest(
        manifest_id="gm_rec",
        generation_id="gen_1",
        workspace_path=str(tmp_generation_root),
        execution_records=[rec],
        generated_output_paths=[str(tmp_generation_root / "out.md")],
        created_utc=ts,
    )
    save_generation_manifest(manifest, tmp_generation_root)
    loaded = load_generation_manifest("gm_rec", tmp_generation_root)
    assert loaded is not None
    assert len(loaded.execution_records) == 1
    assert loaded.execution_records[0].backend_name == "document"
    assert loaded.execution_records[0].execution_status == "success"
    assert len(loaded.generated_output_paths) == 1
