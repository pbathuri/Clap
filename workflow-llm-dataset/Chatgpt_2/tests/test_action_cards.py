"""M32I–M32L: Action cards — models, store, preview, handoff, blocked behavior, trust."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.action_cards.models import (
    ActionCard,
    ActionPreview,
    CardState,
    HandoffTarget,
    TrustRequirement,
)
from workflow_dataset.action_cards.store import (
    get_cards_dir,
    load_all_cards,
    load_card,
    list_cards,
    save_card,
    save_cards,
    update_card_state,
)
from workflow_dataset.action_cards.preview import build_preview
from workflow_dataset.action_cards.handoff import execute_handoff
from workflow_dataset.utils.dates import utc_now_iso


def test_card_create_and_roundtrip(tmp_path):
    """Create a card, save, load — roundtrip preserves fields."""
    card = ActionCard(
        card_id="test_card_1",
        title="Focus project",
        description="Set current project from suggestion",
        source_type="personal_suggestion",
        source_ref="sug_123",
        handoff_target=HandoffTarget.PREFILL_COMMAND,
        handoff_params={"command": "projects set-current --id proj_1", "hint": "projects"},
        trust_requirement=TrustRequirement.NONE,
        reversible=True,
        state=CardState.PENDING,
        created_utc=utc_now_iso(),
        updated_utc=utc_now_iso(),
    )
    save_card(card, tmp_path)
    loaded = load_card("test_card_1", tmp_path)
    assert loaded is not None
    assert loaded.card_id == card.card_id
    assert loaded.title == card.title
    assert loaded.handoff_target == HandoffTarget.PREFILL_COMMAND
    assert loaded.state == CardState.PENDING
    assert loaded.handoff_params.get("command") == "projects set-current --id proj_1"


def test_list_cards_by_state(tmp_path):
    """list_cards with state filter returns only matching cards."""
    cards = [
        ActionCard(card_id="c1", title="One", state=CardState.PENDING, created_utc=utc_now_iso(), updated_utc=utc_now_iso()),
        ActionCard(card_id="c2", title="Two", state=CardState.EXECUTED, created_utc=utc_now_iso(), updated_utc=utc_now_iso()),
        ActionCard(card_id="c3", title="Three", state=CardState.PENDING, created_utc=utc_now_iso(), updated_utc=utc_now_iso()),
    ]
    save_cards(cards, tmp_path)
    pending = list_cards(tmp_path, state=CardState.PENDING, limit=10)
    executed = list_cards(tmp_path, state=CardState.EXECUTED, limit=10)
    assert len(pending) == 2
    assert len(executed) == 1
    assert executed[0].card_id == "c2"


def test_build_preview_prefill_command():
    """build_preview for PREFILL_COMMAND returns summary, what_would_happen, command_hint."""
    card = ActionCard(
        card_id="preview_1",
        title="Run projects set-current",
        handoff_target=HandoffTarget.PREFILL_COMMAND,
        handoff_params={"command": "projects set-current --id x", "hint": "projects"},
    )
    preview = build_preview(card)
    assert isinstance(preview, ActionPreview)
    assert preview.card_id == "preview_1"
    assert "prefill" in preview.what_would_happen.lower() or "prefill" in preview.summary.lower()
    assert "projects" in preview.command_hint or "set-current" in preview.command_hint


def test_build_preview_trust_note_approval_required():
    """Preview includes trust_note when trust_requirement is APPROVAL_REQUIRED."""
    card = ActionCard(
        card_id="trust_1",
        title="Queue job",
        handoff_target=HandoffTarget.QUEUE_SIMULATED,
        handoff_params={"plan_ref": "job_1"},
        trust_requirement=TrustRequirement.APPROVAL_REQUIRED,
    )
    preview = build_preview(card)
    assert preview.approval_required is True
    assert "approval" in preview.trust_note.lower()


def test_execute_handoff_prefill_command(tmp_path):
    """execute_handoff for PREFILL_COMMAND marks card executed and returns command_prefilled."""
    card = ActionCard(
        card_id="handoff_prefill_1",
        title="Prefill test",
        handoff_target=HandoffTarget.PREFILL_COMMAND,
        handoff_params={"command": "projects set-current --id p1"},
        state=CardState.PENDING,
        created_utc=utc_now_iso(),
        updated_utc=utc_now_iso(),
    )
    save_card(card, tmp_path)
    result = execute_handoff("handoff_prefill_1", repo_root=tmp_path)
    assert result.get("ok") is True
    assert result.get("command_prefilled") == "projects set-current --id p1"
    assert "Prefill" in result.get("message", "")
    loaded = load_card("handoff_prefill_1", tmp_path)
    assert loaded.state == CardState.EXECUTED
    assert loaded.outcome_summary


def test_execute_handoff_blocked_card(tmp_path):
    """Executing a blocked card returns ok=False and blocked_reason."""
    card = ActionCard(
        card_id="blocked_1",
        title="Blocked action",
        handoff_target=HandoffTarget.QUEUE_SIMULATED,
        handoff_params={"plan_ref": "j1"},
        state=CardState.BLOCKED,
        blocked_reason="Job has blocking issues; resolve in approval studio.",
        created_utc=utc_now_iso(),
        updated_utc=utc_now_iso(),
    )
    save_card(card, tmp_path)
    result = execute_handoff("blocked_1", repo_root=tmp_path)
    assert result.get("ok") is False
    assert result.get("error") == "card_blocked"
    assert "blocking" in result.get("blocked_reason", "").lower() or "blocked" in result.get("blocked_reason", "").lower()


def test_execute_handoff_dismissed_card(tmp_path):
    """Executing a dismissed card returns ok=False."""
    card = ActionCard(
        card_id="dismissed_1",
        title="Dismissed",
        handoff_target=HandoffTarget.PREFILL_COMMAND,
        handoff_params={"command": "echo ok"},
        state=CardState.DISMISSED,
        created_utc=utc_now_iso(),
        updated_utc=utc_now_iso(),
    )
    save_card(card, tmp_path)
    result = execute_handoff("dismissed_1", repo_root=tmp_path)
    assert result.get("ok") is False
    assert result.get("error") == "card_dismissed"


def test_execute_handoff_card_not_found(tmp_path):
    """execute_handoff for missing card returns ok=False, error card_not_found."""
    result = execute_handoff("nonexistent_id", repo_root=tmp_path)
    assert result.get("ok") is False
    assert result.get("error") == "card_not_found"
    assert result.get("card_id") == "nonexistent_id"


def test_update_card_state(tmp_path):
    """update_card_state updates state and optional outcome_summary."""
    card = ActionCard(
        card_id="update_1",
        title="Update test",
        state=CardState.PENDING,
        created_utc=utc_now_iso(),
        updated_utc=utc_now_iso(),
    )
    save_card(card, tmp_path)
    ok = update_card_state(
        "update_1",
        CardState.EXECUTED,
        repo_root=tmp_path,
        updated_utc=utc_now_iso(),
        executed_at=utc_now_iso(),
        outcome_summary="Done.",
    )
    assert ok is True
    loaded = load_card("update_1", tmp_path)
    assert loaded.state == CardState.EXECUTED
    assert loaded.outcome_summary == "Done."


def test_get_cards_dir(tmp_path):
    """get_cards_dir(repo_root) returns path under repo data/local/action_cards."""
    d = get_cards_dir(tmp_path)
    assert d == tmp_path / "data/local/action_cards"


def test_card_outcome_reporting(tmp_path):
    """After execute, card stores outcome_summary for reporting."""
    card = ActionCard(
        card_id="outcome_1",
        title="Outcome test",
        handoff_target=HandoffTarget.PREFILL_COMMAND,
        handoff_params={"command": "test command"},
        state=CardState.PENDING,
        created_utc=utc_now_iso(),
        updated_utc=utc_now_iso(),
    )
    save_card(card, tmp_path)
    execute_handoff("outcome_1", repo_root=tmp_path)
    loaded = load_card("outcome_1", tmp_path)
    assert loaded.outcome_summary
    assert loaded.executed_at
    assert loaded.state == CardState.EXECUTED


# ----- M32L.1 Micro-assistance bundles + fast review paths + grouped flows -----

from workflow_dataset.action_cards.bundles import (
    load_all_bundles,
    load_bundle,
    save_bundle,
    list_bundles_by_moment,
    add_card_to_bundle,
    remove_card_from_bundle,
)
from workflow_dataset.action_cards.models import MicroAssistanceBundle, FastReviewPath, GroupedCardFlow
from workflow_dataset.action_cards.review_paths import (
    load_all_review_paths,
    load_review_path,
    save_review_path,
    apply_path,
)
from workflow_dataset.action_cards.flows import (
    load_all_flows,
    load_flow,
    get_flow_for_moment,
    run_flow,
    save_flow,
)


def test_bundle_create_save_load(tmp_path):
    """Create and save a micro-assistance bundle; load and list by moment."""
    b = MicroAssistanceBundle(
        bundle_id="bundle_resume_1",
        name="Resume work cards",
        description="Pending and accepted cards for resuming work",
        moment_kind="resume_work",
        card_ids=["card_1", "card_2"],
        created_utc=utc_now_iso(),
        updated_utc=utc_now_iso(),
    )
    save_bundle(b, tmp_path)
    loaded = load_bundle("bundle_resume_1", tmp_path)
    assert loaded is not None
    assert loaded.name == "Resume work cards"
    assert loaded.moment_kind == "resume_work"
    assert loaded.card_ids == ["card_1", "card_2"]
    by_moment = list_bundles_by_moment("resume_work", tmp_path)
    assert len(by_moment) == 1
    assert by_moment[0].bundle_id == "bundle_resume_1"


def test_bundle_add_remove_card(tmp_path):
    """Add and remove card ids from a bundle."""
    b = MicroAssistanceBundle(bundle_id="b2", name="B2", moment_kind="blocked_review", card_ids=[], created_utc=utc_now_iso(), updated_utc=utc_now_iso())
    save_bundle(b, tmp_path)
    add_card_to_bundle("b2", "card_a", tmp_path)
    loaded = load_bundle("b2", tmp_path)
    assert "card_a" in loaded.card_ids
    add_card_to_bundle("b2", "card_b", tmp_path)
    loaded = load_bundle("b2", tmp_path)
    assert "card_a" in loaded.card_ids and "card_b" in loaded.card_ids
    remove_card_from_bundle("b2", "card_a", tmp_path)
    loaded = load_bundle("b2", tmp_path)
    assert "card_a" not in loaded.card_ids and "card_b" in loaded.card_ids


def test_fast_review_path_apply(tmp_path):
    """Create cards and a review path; apply path returns filtered and sorted cards."""
    save_cards(
        [
            ActionCard(card_id="c_old", title="Old", state=CardState.PENDING, updated_utc="2025-01-01T00:00:00Z", created_utc="2025-01-01T00:00:00Z"),
            ActionCard(card_id="c_new", title="New", state=CardState.PENDING, updated_utc="2025-01-02T00:00:00Z", created_utc="2025-01-02T00:00:00Z"),
            ActionCard(card_id="c_exec", title="Executed", state=CardState.EXECUTED, updated_utc="2025-01-03T00:00:00Z", created_utc="2025-01-03T00:00:00Z"),
        ],
        tmp_path,
    )
    path = FastReviewPath(
        path_id="path_pending",
        name="Pending first",
        moment_kind="resume_work",
        filter_state="pending",
        sort_by="updated_utc",
        sort_order="desc",
        limit=5,
        created_utc=utc_now_iso(),
        updated_utc=utc_now_iso(),
    )
    save_review_path(path, tmp_path)
    cards = apply_path("path_pending", tmp_path)
    assert len(cards) == 2
    assert cards[0].card_id == "c_new"
    assert cards[1].card_id == "c_old"


def test_flow_get_for_moment_and_run(tmp_path):
    """Create flow with bundle and path; get_flow_for_moment and run_flow return cards."""
    save_card(
        ActionCard(card_id="fc1", title="Flow card 1", state=CardState.PENDING, created_utc=utc_now_iso(), updated_utc=utc_now_iso()),
        tmp_path,
    )
    b = MicroAssistanceBundle(bundle_id="fb", name="Flow bundle", moment_kind="end_of_day_wrap", card_ids=["fc1"], created_utc=utc_now_iso(), updated_utc=utc_now_iso())
    save_bundle(b, tmp_path)
    p = FastReviewPath(path_id="fp", name="Wrap path", moment_kind="end_of_day_wrap", limit=10, created_utc=utc_now_iso(), updated_utc=utc_now_iso())
    save_review_path(p, tmp_path)
    f = GroupedCardFlow(flow_id="flow_wrap", moment_kind="end_of_day_wrap", label="End of day wrap", bundle_id="fb", review_path_id="fp", created_utc=utc_now_iso(), updated_utc=utc_now_iso())
    save_flow(f, tmp_path)
    flow = get_flow_for_moment("end_of_day_wrap", tmp_path)
    assert flow is not None
    assert flow.flow_id == "flow_wrap"
    result = run_flow("end_of_day_wrap", tmp_path)
    assert result.get("ok") is True
    assert result.get("cards_count") == 1
    assert result["cards"][0]["card_id"] == "fc1"


def test_run_flow_no_flow_for_moment(tmp_path):
    """run_flow for unknown moment returns ok=False."""
    result = run_flow("nonexistent_moment", tmp_path)
    assert result.get("ok") is False
    assert result.get("error") == "no_flow_for_moment"
    assert result.get("cards") == []
