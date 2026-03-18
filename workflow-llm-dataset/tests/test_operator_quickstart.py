"""M23X: Tests for operator quickstart — quick reference, first-run tour, first-value flow, status card, no-data behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.operator_quickstart import (
    build_quick_reference,
    format_quick_reference_text,
    format_quick_reference_md,
    build_first_run_tour,
    format_tour_text,
    build_first_value_flow,
    format_first_value_flow_text,
    build_status_card,
    format_status_card_text,
)


def test_quick_reference_generation() -> None:
    ref = build_quick_reference()
    assert "sections" in ref
    assert len(ref["sections"]) >= 9
    surfaces = [s["surface"] for s in ref["sections"]]
    assert "dashboard" in surfaces
    assert "profile" in surfaces
    assert "onboard" in surfaces
    assert "jobs" in surfaces
    assert "copilot" in surfaces
    assert "inbox" in surfaces
    assert "trust" in surfaces
    assert "runtime" in surfaces
    assert "mission-control" in surfaces


def test_format_quick_reference_text() -> None:
    text = format_quick_reference_text()
    assert "dashboard" in text
    assert "workflow-dataset" in text
    assert "mission-control" in text


def test_format_quick_reference_md() -> None:
    md = format_quick_reference_md()
    assert "## dashboard" in md or "dashboard" in md
    assert "`workflow-dataset" in md


def test_first_run_tour_content() -> None:
    tour = build_first_run_tour()
    assert "what_system_can_do" in tour
    assert "simulate_only_explained" in tour
    assert "approvals_that_matter" in tour
    assert "recommended_first_workflow" in tour
    assert "how_to_interpret_trust" in tour
    assert "how_to_interpret_runtime" in tour
    assert "how_to_interpret_profile" in tour


def test_format_tour_text() -> None:
    text = format_tour_text()
    assert "What the system can do" in text or "simulate-only" in text.lower()
    assert "approvals" in text.lower()
    assert "recommended first workflow" in text.lower()
    assert "trust" in text.lower()


def test_first_value_flow_steps() -> None:
    flow = build_first_value_flow()
    assert "steps" in flow
    steps = flow["steps"]
    assert len(steps) >= 6
    titles = [s["title"] for s in steps]
    assert "Bootstrap profile" in titles
    assert "Check runtime mesh" in titles
    assert "Onboard approvals" in titles
    assert "Show recommended job pack" in titles
    assert "Show inbox" in titles
    assert "Run one safe simulate-only routine" in titles


def test_format_first_value_flow_text() -> None:
    text = format_first_value_flow_text()
    assert "Step 1" in text
    assert "workflow-dataset" in text
    assert "Bootstrap profile" in text


def test_status_card_structure() -> None:
    card = build_status_card()
    assert "integrated_modules_available" in card
    assert "missing_optional" in card
    assert "trusted_real_vs_simulate" in card
    assert "recommended_next_action" in card


def test_format_status_card_text() -> None:
    text = format_status_card_text()
    assert "Product status card" in text
    assert "Integrated modules" in text or "modules" in text.lower()
    assert "Recommended next action" in text or "action" in text


def test_no_data_partial_setup_behavior(tmp_path: Path) -> None:
    """With empty repo root, tour and status card still produce valid output (may show errors or defaults)."""
    tour = build_first_run_tour(tmp_path)
    assert tour.get("recommended_first_workflow")
    assert isinstance(tour.get("approvals_that_matter"), list)
    card = build_status_card(tmp_path)
    assert "recommended_next_action" in card
    assert isinstance(card.get("integrated_modules_available"), list)
