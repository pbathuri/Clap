"""
M24N–M24Q: Outcome capture, session memory, improvement signals.
Tests: persistence, pattern detection, repeated blocker reporting, session summary, recommendation generation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.outcomes.models import (
    SessionOutcome,
    TaskOutcome,
    BlockedCause,
    UsefulnessConfirmation,
)
from workflow_dataset.outcomes.store import (
    save_session_outcome,
    get_session_outcome,
    list_session_outcomes,
    load_outcome_history,
)
from workflow_dataset.outcomes.patterns import (
    repeated_block_patterns,
    repeated_success_patterns,
    most_useful_per_pack,
)
from workflow_dataset.outcomes.signals import generate_improvement_signals
from workflow_dataset.outcomes.bridge import (
    next_run_recommendations,
    pack_refinement_suggestions,
    outcome_to_correction_suggestions,
)
from workflow_dataset.outcomes.report import (
    format_session_outcome,
    format_patterns,
    format_recommend_improvements,
    format_pack_scorecard,
    format_improvement_backlog,
)
from workflow_dataset.outcomes.scorecard import build_pack_scorecard, build_improvement_backlog


@pytest.fixture
def tmp_repo(tmp_path):
    return tmp_path


def test_session_outcome_persistence(tmp_repo):
    so = SessionOutcome(
        session_id="sess_test_1",
        timestamp_start="2026-03-16T10:00:00Z",
        timestamp_end="2026-03-16T10:05:00Z",
        pack_id="pack_analyst",
        disposition="complete",
        task_outcomes=[
            TaskOutcome(
                task_id="t1",
                session_id="sess_test_1",
                source_type="job_run",
                source_ref="weekly_status",
                outcome_kind="success",
            ),
        ],
        blocked_causes=[BlockedCause(cause_code="approval_missing", source_ref="export_pdf")],
        usefulness_confirmations=[
            UsefulnessConfirmation(source_ref="weekly_status", usefulness_score=4, operator_confirmed=True),
        ],
        summary_text="Weekly status run completed; export blocked.",
    )
    path = save_session_outcome(so, tmp_repo)
    assert path.exists()
    loaded = get_session_outcome("sess_test_1", tmp_repo)
    assert loaded is not None
    assert loaded.session_id == "sess_test_1"
    assert loaded.pack_id == "pack_analyst"
    assert len(loaded.blocked_causes) == 1
    assert loaded.blocked_causes[0].cause_code == "approval_missing"
    assert len(loaded.usefulness_confirmations) == 1
    assert loaded.usefulness_confirmations[0].source_ref == "weekly_status"


def test_list_session_outcomes(tmp_repo):
    for i in range(3):
        so = SessionOutcome(
            session_id=f"sess_list_{i}",
            pack_id="pack_analyst" if i % 2 == 0 else "pack_founder",
        )
        save_session_outcome(so, tmp_repo)
    listed = list_session_outcomes(limit=10, repo_root=tmp_repo)
    assert len(listed) >= 3
    ids = {s.session_id for s in listed}
    assert "sess_list_0" in ids
    listed_pack = list_session_outcomes(limit=10, repo_root=tmp_repo, pack_id="pack_analyst")
    assert all(s.pack_id == "pack_analyst" for s in listed_pack)


def test_load_outcome_history(tmp_repo):
    so = SessionOutcome(session_id="sess_hist_1", pack_id="p1", blocked_causes=[BlockedCause(cause_code="timeout")])
    save_session_outcome(so, tmp_repo)
    history = load_outcome_history(tmp_repo, limit=50)
    assert len(history) >= 1
    entry = next((e for e in history if e.get("session_id") == "sess_hist_1"), None)
    assert entry is not None
    assert "timeout" in entry.get("blocked_causes", [])


def test_repeated_block_patterns(tmp_repo):
    for _ in range(3):
        so = SessionOutcome(
            session_id=f"sess_block_{_}",
            blocked_causes=[BlockedCause(cause_code="approval_missing", source_ref="export_pdf")],
        )
        save_session_outcome(so, tmp_repo)
    patterns = repeated_block_patterns(repo_root=tmp_repo, min_occurrences=2, limit=10)
    assert len(patterns) >= 1
    approval = next((p for p in patterns if p["cause_code"] == "approval_missing"), None)
    assert approval is not None
    assert approval["count"] >= 2


def test_repeated_success_patterns(tmp_repo):
    for i in range(3):
        so = SessionOutcome(
            session_id=f"sess_ok_{i}",
            pack_id="pack_analyst",
            usefulness_confirmations=[
                UsefulnessConfirmation(source_ref="weekly_status", usefulness_score=4, operator_confirmed=True),
            ],
            task_outcomes=[TaskOutcome(source_ref="weekly_status", outcome_kind="success")],
        )
        save_session_outcome(so, tmp_repo)
    patterns = repeated_success_patterns(repo_root=tmp_repo, min_occurrences=2, limit=10)
    assert len(patterns) >= 1
    refs = [p["source_ref"] for p in patterns]
    assert "weekly_status" in refs


def test_most_useful_per_pack(tmp_repo):
    so = SessionOutcome(
        session_id="sess_useful_1",
        pack_id="pack_analyst",
        usefulness_confirmations=[
            UsefulnessConfirmation(source_ref="weekly_status", usefulness_score=5, operator_confirmed=True),
        ],
    )
    save_session_outcome(so, tmp_repo)
    useful = most_useful_per_pack(repo_root=tmp_repo, top_n=5)
    assert len(useful) >= 1
    assert any(u["source_ref"] == "weekly_status" and u["pack_id"] == "pack_analyst" for u in useful)


def test_generate_improvement_signals(tmp_repo):
    for i in range(3):
        so = SessionOutcome(
            session_id=f"sess_sig_{i}",
            disposition="fix",
            blocked_causes=[BlockedCause(cause_code="approval_missing", source_ref="export_pdf")],
        )
        save_session_outcome(so, tmp_repo)
    signals = generate_improvement_signals(repo_root=tmp_repo, min_block_count=2)
    assert "recurring_blockers" in signals
    assert "signals_list" in signals
    assert len(signals["signals_list"]) >= 1
    assert any(s.get("signal_type") == "recurring_blocker" for s in signals["signals_list"])


def test_session_summary_report(tmp_repo):
    so = SessionOutcome(
        session_id="sess_report_1",
        pack_id="pack_analyst",
        summary_text="Test summary.",
    )
    save_session_outcome(so, tmp_repo)
    text = format_session_outcome(None, session_id="sess_report_1", repo_root=tmp_repo)
    assert "sess_report_1" in text
    assert "pack_analyst" in text
    assert "Test summary" in text


def test_format_patterns(tmp_repo):
    so = SessionOutcome(session_id="sess_pat_1", blocked_causes=[BlockedCause(cause_code="timeout")])
    save_session_outcome(so, tmp_repo)
    text = format_patterns(repo_root=tmp_repo)
    assert "Outcome patterns" in text
    assert "Repeated blocks" in text or "Repeated success" in text


def test_recommendation_generation(tmp_repo):
    so = SessionOutcome(
        session_id="sess_rec_1",
        pack_id="pack_analyst",
        usefulness_confirmations=[UsefulnessConfirmation(source_ref="weekly_status", usefulness_score=5, operator_confirmed=True)],
    )
    save_session_outcome(so, tmp_repo)
    recs = next_run_recommendations(repo_root=tmp_repo)
    pack_recs = pack_refinement_suggestions(repo_root=tmp_repo)
    corr = outcome_to_correction_suggestions(repo_root=tmp_repo, limit=5)
    assert isinstance(recs, list)
    assert isinstance(pack_recs, list)
    assert isinstance(corr, list)


def test_format_recommend_improvements(tmp_repo):
    text = format_recommend_improvements(repo_root=tmp_repo)
    assert "Improvement signals" in text
    assert "Next-run" in text or "recommendations" in text.lower()
    assert "Pack refinement" in text or "Correction" in text


def test_build_pack_scorecard(tmp_repo):
    so = SessionOutcome(
        session_id="sess_sc_1",
        pack_id="founder_ops_plus",
        disposition="complete",
        usefulness_confirmations=[UsefulnessConfirmation(source_ref="weekly_status", usefulness_score=4, operator_confirmed=True)],
    )
    save_session_outcome(so, tmp_repo)
    card = build_pack_scorecard("founder_ops_plus", tmp_repo)
    assert card["pack_id"] == "founder_ops_plus"
    assert "usefulness" in card
    assert "blockers" in card
    assert "readiness" in card
    assert "trusted_real_suitability" in card
    assert "session_reuse_strength" in card
    assert "improvement_backlog" in card
    assert card["session_reuse_strength"]["sessions_count"] >= 1
    assert isinstance(card["improvement_backlog"], list)


def test_format_pack_scorecard(tmp_repo):
    so = SessionOutcome(session_id="sess_fmt_1", pack_id="analyst_research_plus")
    save_session_outcome(so, tmp_repo)
    text = format_pack_scorecard(pack_id="analyst_research_plus", repo_root=tmp_repo)
    assert "Pack scorecard" in text
    assert "analyst_research_plus" in text
    assert "Usefulness" in text
    assert "Blockers" in text
    assert "Session reuse" in text or "Improvement backlog" in text


def test_build_improvement_backlog(tmp_repo):
    items = build_improvement_backlog(repo_root=tmp_repo)
    assert isinstance(items, list)
    items_pack = build_improvement_backlog(repo_root=tmp_repo, pack_id="founder_ops_plus")
    assert isinstance(items_pack, list)


def test_format_improvement_backlog(tmp_repo):
    text = format_improvement_backlog(repo_root=tmp_repo)
    assert "Improvement backlog" in text
    text_pack = format_improvement_backlog(repo_root=tmp_repo, pack_id="founder_ops_plus")
    assert "Improvement backlog" in text_pack
    assert "founder_ops_plus" in text_pack or "pack_id" in text_pack
