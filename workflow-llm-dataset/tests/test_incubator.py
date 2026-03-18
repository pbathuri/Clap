"""M23W: Incubator package — registry and gates. Local-only; no cloud."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.incubator.registry import (
    list_candidates,
    add_candidate,
    get_candidate,
    update_candidate,
    set_promotion_decision,
    mark_stage,
    attach_evidence,
)
from workflow_dataset.incubator.gates import evaluate_gates, promotion_report


def test_list_candidates_empty(tmp_path):
    """list_candidates on empty dir returns []."""
    assert list_candidates(tmp_path) == []


def test_add_and_list_candidates(tmp_path):
    """add_candidate then list_candidates returns the candidate."""
    add_candidate("wf-x", description="Test workflow", stage="idea", root=tmp_path)
    cands = list_candidates(tmp_path)
    assert len(cands) == 1
    assert cands[0].get("id") == "wf-x"
    assert cands[0].get("stage") == "idea"


def test_get_candidate(tmp_path):
    """get_candidate returns candidate or None."""
    add_candidate("wf-y", root=tmp_path)
    c = get_candidate("wf-y", tmp_path)
    assert c is not None
    assert c.get("id") == "wf-y"
    assert get_candidate("nonexistent", tmp_path) is None


def test_set_promotion_decision(tmp_path):
    """set_promotion_decision updates candidate."""
    add_candidate("wf-z", root=tmp_path)
    c = set_promotion_decision("wf-z", "hold", root=tmp_path)
    assert c is not None
    assert c.get("promotion_decision") == "hold"


def test_mark_stage(tmp_path):
    """mark_stage updates stage."""
    add_candidate("wf-a", root=tmp_path)
    c = mark_stage("wf-a", "prototype", root=tmp_path)
    assert c is not None
    assert c.get("stage") == "prototype"


def test_attach_evidence(tmp_path):
    """attach_evidence appends ref."""
    add_candidate("wf-b", root=tmp_path)
    c = attach_evidence("wf-b", "eval-run-1", root=tmp_path)
    assert c is not None
    assert "eval-run-1" in c.get("evidence_refs", [])


def test_evaluate_gates(tmp_path):
    """evaluate_gates returns gates_passed, recommendation."""
    add_candidate("wf-c", stage="idea", root=tmp_path)
    result = evaluate_gates("wf-c", tmp_path)
    assert "gates_passed" in result
    assert "recommendation" in result
    assert result.get("recommendation") in ("promote", "hold", "reject")


def test_promotion_report(tmp_path):
    """promotion_report returns string."""
    add_candidate("wf-d", root=tmp_path)
    result = evaluate_gates("wf-d", tmp_path)
    report = promotion_report("wf-d", result, tmp_path)
    assert "wf-d" in report
    assert "Gates" in report or "Recommendation" in report
