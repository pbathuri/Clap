"""
M51H.1: Demo user presets + sample workspace packs + staging guide.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.demo_onboarding.models import SampleWorkspacePack, DemoUserPreset, DemoOnboardingSession
from workflow_dataset.demo_onboarding.workspace_packs import (
    get_workspace_pack,
    list_workspace_pack_ids,
    resolve_workspace_pack_path,
    SAMPLE_WORKSPACE_PACKS,
)
from workflow_dataset.demo_onboarding.user_presets import (
    get_demo_user_preset,
    get_default_demo_user_preset,
    DEFAULT_DEMO_USER_PRESET_ID,
)
from workflow_dataset.demo_onboarding.staging_guide import build_operator_staging_guide, format_staging_guide_text
from workflow_dataset.demo_onboarding.flow import (
    demo_onboarding_start,
    demo_onboarding_apply_user_preset,
    demo_onboarding_bootstrap_memory,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_sample_workspace_packs_registry():
    assert "acme_operator_default" in list_workspace_pack_ids()
    assert "document_review_slice" in list_workspace_pack_ids()
    assert "analyst_followup_slice" in list_workspace_pack_ids()
    pk = get_workspace_pack("acme_operator_default")
    assert pk and "demo_onboarding_workspace" in pk.path_relative


def test_resolve_workspace_pack_paths_exist():
    root = _repo_root()
    for pid in list_workspace_pack_ids():
        p = resolve_workspace_pack_path(pid, root)
        assert p is not None and p.is_dir(), f"missing pack dir: {pid}"


def test_demo_user_presets():
    primary = get_default_demo_user_preset()
    assert primary.user_preset_id == DEFAULT_DEMO_USER_PRESET_ID
    assert primary.workspace_pack_id == "acme_operator_default"
    assert primary.role_preset_id == "founder_operator_demo"
    doc = get_demo_user_preset("investor_demo_documents")
    assert doc and doc.workspace_pack_id == "document_review_slice"


def test_session_roundtrip_with_m51h1_fields():
    s = DemoOnboardingSession(
        session_id="x",
        started_at_utc="t",
        role_preset_id="founder_operator_demo",
        demo_user_preset_id="investor_demo_primary",
        workspace_pack_id="acme_operator_default",
    )
    d = s.to_dict()
    assert d["demo_user_preset_id"] == "investor_demo_primary"
    s2 = DemoOnboardingSession.from_dict(d)
    assert s2.workspace_pack_id == "acme_operator_default"


def test_staging_guide_structure():
    g = build_operator_staging_guide(_repo_root())
    assert "demo_user_presets" in g
    assert "workspace_packs" in g
    assert "before_live_demo" in g
    text = format_staging_guide_text(g)
    assert "investor_demo_primary" in text
    assert "acme_operator_default" in text


def test_user_preset_then_bootstrap_at_repo():
    root = _repo_root()
    demo_onboarding_start(root, reset=True)
    session, err = demo_onboarding_apply_user_preset("investor_demo_primary", root)
    assert not err and session
    summary = demo_onboarding_bootstrap_memory(None, root)
    assert not summary.get("error")
    assert summary.get("files_scanned", 0) >= 1
    assert summary.get("workspace_pack_id_used") == "acme_operator_default"
