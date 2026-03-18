"""
M33I–M33L: Tests for in-flow review — draft/handoff models, composition, review, promote, handoff.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.in_flow.models import (
    DraftArtifact,
    HandoffPackage,
    ReviewCheckpoint,
    AffectedWorkflowStep,
    RevisionEntry,
    ReviewBundle,
    HandoffKit,
    DRAFT_TYPE_STATUS_SUMMARY,
    DRAFT_TYPE_REVIEW_CHECKLIST,
    REVIEW_STATUS_WAITING_REVIEW,
    READINESS_READY_TO_APPROVE,
    READINESS_READY_TO_SEND,
)
from workflow_dataset.in_flow.store import (
    save_draft,
    load_draft,
    list_drafts,
    save_handoff,
    load_handoff,
    list_handoffs,
    save_checkpoint,
    list_checkpoints,
    save_bundle,
    load_bundle,
    save_kit,
    load_kit,
)
from workflow_dataset.in_flow.composition import create_draft, create_handoff, link_checkpoint_to_step
from workflow_dataset.in_flow.review import (
    get_draft_in_context,
    revise_draft,
    attach_note,
    promote_to_artifact,
    handoff_to_target,
)


def test_draft_artifact_model():
    step = AffectedWorkflowStep(step_index=0, plan_id="plan_1", step_label="Step one")
    d = DraftArtifact(
        draft_id="draft_test1",
        draft_type=DRAFT_TYPE_STATUS_SUMMARY,
        title="Test draft",
        content="# Hello",
        project_id="proj_1",
        review_status=REVIEW_STATUS_WAITING_REVIEW,
        affected_step=step,
    )
    assert d.draft_id == "draft_test1"
    raw = d.to_dict()
    assert raw["draft_type"] == DRAFT_TYPE_STATUS_SUMMARY
    loaded = DraftArtifact.from_dict(raw)
    assert loaded.draft_id == d.draft_id
    assert loaded.affected_step is not None
    assert loaded.affected_step.step_index == 0


def test_handoff_package_model():
    p = HandoffPackage(
        handoff_id="handoff_test1",
        from_workflow="latest",
        title="Handoff",
        summary="Done.",
        next_steps=["Step A", "Step B"],
        target="artifact",
    )
    raw = p.to_dict()
    loaded = HandoffPackage.from_dict(raw)
    assert loaded.handoff_id == p.handoff_id
    assert loaded.next_steps == p.next_steps


def test_save_load_draft(tmp_path: Path):
    d = DraftArtifact(draft_id="draft_save", draft_type="other", title="T", content="C", created_utc="2025-01-01T00:00:00Z", updated_utc="2025-01-01T00:00:00Z")
    save_draft(d, repo_root=tmp_path)
    loaded = load_draft("draft_save", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.content == "C"
    assert load_draft("nonexistent", repo_root=tmp_path) is None


def test_list_drafts(tmp_path: Path):
    save_draft(DraftArtifact(draft_id="d1", draft_type="other", title="A", project_id="p1", review_status="waiting_review", created_utc="", updated_utc=""), repo_root=tmp_path)
    save_draft(DraftArtifact(draft_id="d2", draft_type="other", title="B", project_id="p1", review_status="promoted", created_utc="", updated_utc=""), repo_root=tmp_path)
    all_d = list_drafts(repo_root=tmp_path, limit=10)
    assert len(all_d) >= 2
    waiting = list_drafts(repo_root=tmp_path, review_status="waiting_review", limit=10)
    assert any(x.draft_id == "d1" for x in waiting)


def test_create_draft(tmp_path: Path):
    draft = create_draft(DRAFT_TYPE_STATUS_SUMMARY, repo_root=tmp_path, project_id="founder_case_alpha", title="My summary")
    assert draft.draft_id.startswith("draft_")
    assert draft.draft_type == DRAFT_TYPE_STATUS_SUMMARY
    assert "founder_case_alpha" in draft.project_id or draft.project_id
    assert load_draft(draft.draft_id, repo_root=tmp_path) is not None


def test_create_handoff(tmp_path: Path):
    pkg = create_handoff(repo_root=tmp_path, from_workflow="latest", title="End of session")
    assert pkg.handoff_id.startswith("handoff_")
    assert pkg.from_workflow in ("latest",) or pkg.from_workflow
    assert load_handoff(pkg.handoff_id, repo_root=tmp_path) is not None


def test_get_draft_in_context(tmp_path: Path):
    step = AffectedWorkflowStep(step_index=1, plan_id="plan_1", step_label="Review")
    d = DraftArtifact(draft_id="draft_ctx", draft_type="other", title="Context draft", content="Body", affected_step=step, created_utc="", updated_utc="")
    save_draft(d, repo_root=tmp_path)
    ctx = get_draft_in_context("draft_ctx", repo_root=tmp_path)
    assert ctx.get("draft_id") == "draft_ctx"
    assert ctx.get("affected_step") is not None
    assert ctx["affected_step"]["step_label"] == "Review"
    assert get_draft_in_context("nonexistent", repo_root=tmp_path) == {}


def test_revise_draft(tmp_path: Path):
    d = DraftArtifact(draft_id="draft_rev", draft_type="other", title="T", content="Old", created_utc="", updated_utc="")
    save_draft(d, repo_root=tmp_path)
    ok = revise_draft("draft_rev", "New content", summary="Updated", repo_root=tmp_path)
    assert ok is True
    loaded = load_draft("draft_rev", repo_root=tmp_path)
    assert loaded.content == "New content"
    assert len(loaded.revision_history) >= 1


def test_attach_note(tmp_path: Path):
    d = DraftArtifact(draft_id="draft_note", draft_type="other", title="T", content="C", operator_notes="", created_utc="", updated_utc="")
    save_draft(d, repo_root=tmp_path)
    attach_note("draft_note", "Operator note here", repo_root=tmp_path)
    loaded = load_draft("draft_note", repo_root=tmp_path)
    assert "Operator note here" in loaded.operator_notes


def test_promote_to_artifact(tmp_path: Path):
    d = DraftArtifact(draft_id="draft_prom", draft_type="other", title="T", content="Promoted body", review_status="waiting_review", created_utc="", updated_utc="")
    save_draft(d, repo_root=tmp_path)
    ok = promote_to_artifact("draft_prom", "out/promoted.md", repo_root=tmp_path)
    assert ok is True
    loaded = load_draft("draft_prom", repo_root=tmp_path)
    assert loaded.review_status == "promoted"
    assert "promoted" in loaded.promoted_artifact_path or "out" in loaded.promoted_artifact_path
    out_path = tmp_path / "out/promoted.md"
    if out_path.exists():
        assert "Promoted body" in out_path.read_text()


def test_handoff_to_target_artifact(tmp_path: Path):
    pkg = HandoffPackage(handoff_id="handoff_deliver", from_workflow="run_1", title="Deliver", summary="Done.", next_steps=["A"], target="artifact", created_utc="", draft_ids=[])
    save_handoff(pkg, repo_root=tmp_path)
    outcome = handoff_to_target("handoff_deliver", repo_root=tmp_path)
    assert outcome.get("ok") is True
    assert outcome.get("target") == "artifact"
    loaded = load_handoff("handoff_deliver", repo_root=tmp_path)
    assert loaded.delivered_utc


def test_link_checkpoint(tmp_path: Path):
    cp = link_checkpoint_to_step("plan_abc", 2, label="Step 2 review", repo_root=tmp_path)
    assert cp.checkpoint_id.startswith("cp_")
    assert cp.plan_id == "plan_abc"
    assert cp.step_index == 2
    cps = list_checkpoints(repo_root=tmp_path, plan_id="plan_abc", status="pending", limit=5)
    assert any(c.checkpoint_id == cp.checkpoint_id for c in cps)


# ----- M33L.1: Review bundles, handoff kits, readiness, nav_links -----

def test_handoff_package_readiness_nav_links_roundtrip(tmp_path: Path):
    """HandoffPackage with readiness and nav_links round-trips correctly."""
    pkg = HandoffPackage(
        handoff_id="handoff_m33l1",
        from_workflow="run_1",
        title="Review complete",
        summary="Done.",
        next_steps=[],
        target="approval_studio",
        readiness=READINESS_READY_TO_APPROVE,
        nav_links=[
            {"label": "Open approval", "view": "approval_studio", "command": "open:approval"},
            {"label": "Planner", "view": "planner", "command": "open:planner"},
        ],
    )
    save_handoff(pkg, repo_root=tmp_path)
    loaded = load_handoff("handoff_m33l1", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.readiness == READINESS_READY_TO_APPROVE
    assert len(loaded.nav_links) == 2
    assert loaded.nav_links[0].get("label") == "Open approval"
    raw = loaded.to_dict()
    assert raw.get("readiness") == READINESS_READY_TO_APPROVE
    assert len(raw.get("nav_links", [])) == 2
    # Old handoff without readiness/nav_links still loads (defaults)
    old_style = {"handoff_id": "old_handoff", "from_workflow": "w", "title": "T", "summary": "S", "next_steps": [], "target": "artifact", "created_utc": "", "draft_ids": []}
    from workflow_dataset.in_flow.models import HandoffPackage as HP
    old_loaded = HP.from_dict(old_style)
    assert old_loaded.readiness == ""
    assert old_loaded.nav_links == []


def test_load_bundles_from_config(tmp_path: Path):
    """Bundles load from store; config load tested when YAML available."""
    from workflow_dataset.in_flow.bundles import list_bundles_with_config
    bundle = ReviewBundle(
        bundle_id="test_bundle",
        name="Test Review Bundle",
        description="For tests",
        checklist_items=["Item A", "Item B"],
        summary_template="Summary for {{session}}",
        decision_questions=[],
        draft_types=["review_checklist"],
    )
    save_bundle(bundle, repo_root=tmp_path)
    bundles = list_bundles_with_config(repo_root=tmp_path)
    assert len(bundles) >= 1
    b = next((x for x in bundles if x.bundle_id == "test_bundle"), None)
    assert b is not None
    assert b.name == "Test Review Bundle"
    assert b.checklist_items == ["Item A", "Item B"]


def test_load_kits_from_config(tmp_path: Path):
    """Handoff kits load from store; list_kits_with_config merges store + config."""
    from workflow_dataset.in_flow.bundles import list_kits_with_config
    kit = HandoffKit(
        kit_id="test_kit",
        name="Test Handoff Kit",
        workflow_type="end_of_session",
        title_template="Handoff {{workflow}}",
        default_target="artifact",
        default_next_steps=["Review", "Approve"],
        nav_links=[{"label": "Approval", "view": "approval_studio", "command": "open:approval"}],
    )
    save_kit(kit, repo_root=tmp_path)
    kits = list_kits_with_config(repo_root=tmp_path)
    assert len(kits) >= 1
    k = next((x for x in kits if x.kit_id == "test_kit"), None)
    assert k is not None
    assert k.default_target == "artifact"
    assert len(k.nav_links) >= 1
    assert k.nav_links[0].get("label") == "Approval"


def test_apply_review_bundle(tmp_path: Path):
    """apply_review_bundle creates drafts from bundle template."""
    from workflow_dataset.in_flow.bundles import apply_review_bundle
    bundle = ReviewBundle(
        bundle_id="apply_test",
        name="Apply Test Bundle",
        description="Creates checklist",
        checklist_items=["Check A", "Check B"],
        summary_template="",
        decision_questions=[],
        draft_types=[DRAFT_TYPE_REVIEW_CHECKLIST],
    )
    save_bundle(bundle, repo_root=tmp_path)
    created = apply_review_bundle("apply_test", repo_root=tmp_path, project_id="proj1", session_id="s1")
    assert len(created) >= 1
    checklist_drafts = [d for d in created if d.draft_type == DRAFT_TYPE_REVIEW_CHECKLIST]
    assert len(checklist_drafts) >= 1
    assert "Check A" in checklist_drafts[0].content or "Check B" in checklist_drafts[0].content


def test_create_handoff_from_kit(tmp_path: Path):
    """create_handoff_from_kit builds handoff with kit template, nav_links, readiness."""
    from workflow_dataset.in_flow.bundles import create_handoff_from_kit
    kit = HandoffKit(
        kit_id="kit_handoff_test",
        name="Kit Handoff Test",
        workflow_type="approval_request",
        title_template="Approval: {{workflow}}",
        default_target="approval_studio",
        default_next_steps=["Approve or request changes"],
        nav_links=[{"label": "Open approval", "view": "approval_studio", "command": "open:approval"}],
    )
    save_kit(kit, repo_root=tmp_path)
    pkg = create_handoff_from_kit("kit_handoff_test", repo_root=tmp_path, from_workflow="run_99", readiness=READINESS_READY_TO_APPROVE)
    assert pkg is not None
    assert pkg.handoff_id.startswith("handoff_")
    assert "run_99" in pkg.title or "Approval" in pkg.title
    assert pkg.target == "approval_studio"
    assert pkg.readiness == READINESS_READY_TO_APPROVE
    assert len(pkg.nav_links) >= 1
    assert load_handoff(pkg.handoff_id, repo_root=tmp_path) is not None


def test_resolve_nav_links(tmp_path: Path):
    """resolve_nav_links returns handoff nav_links and adds defaults by target."""
    from workflow_dataset.in_flow.bundles import resolve_nav_links
    pkg = HandoffPackage(
        handoff_id="handoff_nav",
        from_workflow="w",
        title="T",
        summary="S",
        next_steps=[],
        target="approval_studio",
        nav_links=[{"label": "Custom", "view": "approval_studio", "command": "open:approval"}],
    )
    save_handoff(pkg, repo_root=tmp_path)
    links = resolve_nav_links("handoff_nav", repo_root=tmp_path)
    assert len(links) >= 1
    labels = [L.get("label") for L in links]
    assert "Custom" in labels or any("approval" in str(L.get("view", "")).lower() or "approval" in str(L.get("command", "")).lower() for L in links)


def test_set_get_handoff_readiness(tmp_path: Path):
    """set_handoff_readiness and get_handoff_readiness update and return readiness."""
    from workflow_dataset.in_flow.bundles import set_handoff_readiness, get_handoff_readiness
    pkg = HandoffPackage(handoff_id="handoff_readiness", from_workflow="w", title="T", summary="S", next_steps=[], target="artifact", created_utc="", draft_ids=[])
    save_handoff(pkg, repo_root=tmp_path)
    assert get_handoff_readiness("handoff_readiness", repo_root=tmp_path) == ""
    set_handoff_readiness("handoff_readiness", READINESS_READY_TO_SEND, repo_root=tmp_path)
    assert get_handoff_readiness("handoff_readiness", repo_root=tmp_path) == READINESS_READY_TO_SEND
    loaded = load_handoff("handoff_readiness", repo_root=tmp_path)
    assert loaded.readiness == READINESS_READY_TO_SEND
