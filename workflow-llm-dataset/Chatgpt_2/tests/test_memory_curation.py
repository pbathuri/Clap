"""
M44E–M44H: Memory curation — summarization, retention policies, forgetting candidates, archive, report.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.memory_curation.models import (
    SummarizedMemoryUnit,
    CompressionCandidate,
    ForgettingCandidate,
    RetentionPolicyCuration,
    ReviewRequiredDeletionCandidate,
    ArchivalState,
    RETENTION_SHORT,
    RETENTION_MEDIUM,
    RETENTION_LONG,
    RETENTION_PROTECTED,
)
from workflow_dataset.memory_curation.summarization import (
    summarize_repeated_events,
    summarize_session_history,
    summarize_operator_pattern,
    summarize_episode_chain,
    build_compression_candidates_from_sessions,
)
from workflow_dataset.memory_curation.retention import (
    get_default_policies,
    get_policy_by_id,
    get_protected_policies,
    retention_tier_requires_review,
)
from workflow_dataset.memory_curation.forgetting import generate_forgetting_candidates
from workflow_dataset.memory_curation.store import (
    load_summaries,
    save_summaries,
    append_summary,
    load_compression_candidates,
    save_compression_candidates,
    load_forgetting_candidates,
    save_forgetting_candidates,
    load_review_required,
    save_review_required,
    load_archival_states,
    save_archival_states,
)
from workflow_dataset.memory_curation.report import status, archive_report, next_action, mission_control_slice


# ----- Summarization / compression -----
def test_summarize_repeated_events(tmp_path):
    u = summarize_repeated_events(
        unit_ids=["u1", "u2", "u3"],
        session_ids=["s1", "s2"],
        summary_text="Three similar events.",
        repo_root=tmp_path,
    )
    assert isinstance(u, SummarizedMemoryUnit)
    assert u.summary_id.startswith("sum_")
    assert u.summary_text == "Three similar events."
    assert u.source_unit_ids == ["u1", "u2", "u3"]
    assert u.source_session_ids == ["s1", "s2"]
    assert u.source_kind == "repeated_events"


def test_summarize_session_history(tmp_path):
    u = summarize_session_history(
        session_id="sess_1",
        unit_ids=["u1", "u2"],
        summary_text="Session rollup.",
        repo_root=tmp_path,
    )
    assert u.source_kind == "session_history"
    assert u.source_session_ids == ["sess_1"]


def test_summarize_episode_chain(tmp_path):
    u = summarize_episode_chain(
        episode_refs=["ep1", "ep2"],
        unit_ids=["u1", "u2"],
        summary_text="Episode chain rollup.",
        repo_root=tmp_path,
    )
    assert u.source_kind == "episode_chain"
    assert "ep1" in u.keyword_tags or "ep2" in u.keyword_tags


def test_build_compression_candidates_from_sessions_empty(tmp_path):
    cands = build_compression_candidates_from_sessions(repo_root=tmp_path, limit=20)
    assert isinstance(cands, list)
    # With no outcome history, may be empty
    for c in cands:
        assert isinstance(c, CompressionCandidate)
        assert c.candidate_id.startswith("comp_")


def test_build_compression_candidates_with_history(tmp_path):
    """With outcome history present, candidates may be produced."""
    hist_dir = tmp_path / "data" / "local" / "outcomes"
    hist_dir.mkdir(parents=True)
    import json
    hist_file = hist_dir / "outcome_history.json"
    hist_file.write_text(json.dumps({
        "entries": [
            {"session_id": "s1", "timestamp": "2024-01-01T12:00:00Z"},
            {"session_id": "s1", "timestamp": "2024-01-01T12:01:00Z"},
            {"session_id": "s1", "timestamp": "2024-01-01T12:02:00Z"},
        ],
        "updated": "2024-01-01T12:00:00Z",
    }, indent=2), encoding="utf-8")
    cands = build_compression_candidates_from_sessions(repo_root=tmp_path, min_units=2, limit=20)
    assert isinstance(cands, list)


# ----- Retention policy -----
def test_get_default_policies():
    policies = get_default_policies()
    assert len(policies) >= 4
    ids = {p.policy_id for p in policies}
    assert "short_lived" in ids
    assert "medium_term" in ids
    assert "long_term" in ids
    assert "protected" in ids


def test_get_policy_by_id():
    p = get_policy_by_id("protected")
    assert p is not None
    assert p.protected is True
    assert get_policy_by_id("nonexistent") is None


def test_get_protected_policies():
    protected = get_protected_policies()
    assert all(p.protected for p in protected)
    assert any(p.policy_id == "protected" for p in protected)


def test_retention_tier_requires_review():
    assert retention_tier_requires_review(RETENTION_PROTECTED) is True
    assert retention_tier_requires_review(RETENTION_LONG) is True
    assert retention_tier_requires_review(RETENTION_SHORT) is False
    assert retention_tier_requires_review(RETENTION_MEDIUM) is False


# ----- Forgetting candidates -----
def test_generate_forgetting_candidates_short_lived():
    from datetime import datetime, timezone, timedelta
    old = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    entries = [
        {"unit_id": "u1", "created_at_utc": old, "retention_tier": RETENTION_SHORT, "source": "default"},
    ]
    candidates, review = generate_forgetting_candidates(entries)
    assert isinstance(candidates, list)
    assert isinstance(review, list)
    assert any(c.reason == "expired_short_lived" for c in candidates)


def test_generate_forgetting_candidates_protected_not_candidate():
    from datetime import datetime, timezone, timedelta
    old = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
    entries = [
        {"unit_id": "u_prot", "created_at_utc": old, "retention_tier": RETENTION_PROTECTED, "source": "default"},
    ]
    candidates, review = generate_forgetting_candidates(entries)
    assert not any("u_prot" in c.unit_ids for c in candidates)


def test_generate_forgetting_candidates_medium_term():
    from datetime import datetime, timezone, timedelta
    old = (datetime.now(timezone.utc) - timedelta(days=35)).isoformat()
    entries = [
        {"unit_id": "u_med", "created_at_utc": old, "retention_tier": RETENTION_MEDIUM, "source": "default"},
    ]
    candidates, review = generate_forgetting_candidates(entries)
    assert any(c.reason == "policy_medium_term" for c in candidates)
    assert any(r.forgetting_candidate_id for r in review)


# ----- Store round-trip -----
def test_store_summaries_roundtrip(tmp_path):
    u = summarize_repeated_events(["a", "b"], ["s1"], "Summary.", repo_root=tmp_path)
    save_summaries([u], repo_root=tmp_path)
    loaded = load_summaries(repo_root=tmp_path)
    assert len(loaded) == 1
    assert loaded[0].summary_id == u.summary_id
    assert loaded[0].source_unit_ids == ["a", "b"]


def test_append_summary(tmp_path):
    u = summarize_session_history("s1", ["u1"], "Rollup.", repo_root=tmp_path)
    append_summary(u, repo_root=tmp_path)
    loaded = load_summaries(repo_root=tmp_path)
    assert len(loaded) == 1
    append_summary(summarize_operator_pattern(["u2"], ["s2"], "Pattern.", repo_root=tmp_path), repo_root=tmp_path)
    loaded = load_summaries(repo_root=tmp_path)
    assert len(loaded) == 2


def test_store_forgetting_and_review_roundtrip(tmp_path):
    c = ForgettingCandidate(
        candidate_id="forget_1",
        unit_ids=["u1"],
        reason="expired_short_lived",
        created_at_utc="2024-01-01T00:00:00Z",
        review_required=False,
        applied=False,
    )
    save_forgetting_candidates([c], repo_root=tmp_path)
    loaded = load_forgetting_candidates(repo_root=tmp_path)
    assert len(loaded) == 1
    assert loaded[0].candidate_id == "forget_1"

    r = ReviewRequiredDeletionCandidate(
        candidate_id="review_1",
        forgetting_candidate_id="forget_2",
        unit_ids=["u2"],
        reason="policy_medium_term",
        high_value_hint=False,
        created_at_utc="2024-01-01T00:00:00Z",
        reviewed=False,
        approved_for_forget=False,
    )
    save_review_required([r], repo_root=tmp_path)
    rev_loaded = load_review_required(repo_root=tmp_path)
    assert len(rev_loaded) == 1
    assert rev_loaded[0].forgetting_candidate_id == "forget_2"


def test_store_archival_state_roundtrip(tmp_path):
    a = ArchivalState(
        archive_id="arch_1",
        unit_ids=["u1", "u2"],
        scope="session_history_old",
        archived_at_utc="2024-01-01T00:00:00Z",
        location="data/local/archives/session_history_old.json",
        retrievable=True,
    )
    save_archival_states([a], repo_root=tmp_path)
    loaded = load_archival_states(repo_root=tmp_path)
    assert len(loaded) == 1
    assert loaded[0].archive_id == "arch_1"
    assert loaded[0].retrievable is True


# ----- Report: status, archive_report, next_action, mission_control -----
def test_status_empty(tmp_path):
    st = status(repo_root=tmp_path)
    assert st["summaries_count"] == 0
    assert st["compression_candidates_count"] == 0
    assert "curation_dir" in st


def test_archive_report_empty(tmp_path):
    report = archive_report(repo_root=tmp_path)
    assert report["archives_count"] == 0
    assert "archives" in report


def test_next_action_none(tmp_path):
    nxt = next_action(repo_root=tmp_path)
    assert "action" in nxt
    assert nxt["action"] in ("none", "review_required", "summarize", "apply_forgetting")


def test_next_action_review_required(tmp_path):
    r = ReviewRequiredDeletionCandidate(
        candidate_id="review_1",
        forgetting_candidate_id="forget_1",
        unit_ids=["u1"],
        reason="policy",
        created_at_utc="2024-01-01T00:00:00Z",
        reviewed=False,
        approved_for_forget=False,
    )
    save_review_required([r], repo_root=tmp_path)
    nxt = next_action(repo_root=tmp_path)
    assert nxt["action"] == "review_required"
    assert nxt["count"] == 1


def test_mission_control_slice(tmp_path):
    mc = mission_control_slice(repo_root=tmp_path)
    assert "memory_growth_pressure" in mc
    assert mc["memory_growth_pressure"] in ("low", "medium", "high")
    assert "protected_memory_classes" in mc
    assert "next_action" in mc


# ----- M44H.1: Protection rules, review packs, archival policies, explanations -----
def test_protection_rules_default():
    from workflow_dataset.memory_curation.protection_rules import get_default_protection_rules
    rules = get_default_protection_rules()
    assert len(rules) >= 1
    ids = {r.rule_id for r in rules}
    assert "corrections" in ids or "trust" in ids


def test_match_unit_against_rules_corrections():
    from workflow_dataset.memory_curation.protection_rules import match_unit_against_rules, get_default_protection_rules
    rules = get_default_protection_rules()
    matched = match_unit_against_rules({"source": "corrections", "source_ref": "", "tags": []}, rules)
    assert any(r.rule_id == "corrections" for r in matched)


def test_explain_why_protected():
    from workflow_dataset.memory_curation.protection_rules import explain_why_protected, get_default_protection_rules
    expl = explain_why_protected({"source": "corrections"}, get_default_protection_rules())
    assert "protected" in expl.lower() or "correction" in expl.lower()


def test_explanations_forgettable():
    from workflow_dataset.memory_curation.explanations import build_forgettable_explanation
    s = build_forgettable_explanation("expired_short_lived")
    assert "short-lived" in s.lower() or "forget" in s.lower() or "7" in s


def test_explanations_compressible():
    from workflow_dataset.memory_curation.explanations import build_compressible_explanation
    s = build_compressible_explanation("session_history", item_count=5)
    assert "session" in s.lower() or "compress" in s.lower() or "5" in s


def test_review_pack_create_empty(tmp_path):
    from workflow_dataset.memory_curation.review_packs import create_review_pack
    pack = create_review_pack(repo_root=tmp_path)
    assert pack is None


def test_review_pack_create_with_pending(tmp_path):
    from workflow_dataset.memory_curation.review_packs import create_review_pack, get_review_pack
    from workflow_dataset.memory_curation.store import save_review_required
    from workflow_dataset.memory_curation.models import ReviewRequiredDeletionCandidate
    r = ReviewRequiredDeletionCandidate(
        candidate_id="review_1",
        forgetting_candidate_id="forget_1",
        unit_ids=["u1"],
        reason="policy_medium_term",
        created_at_utc="2024-01-01T00:00:00Z",
        reviewed=False,
        approved_for_forget=False,
    )
    save_review_required([r], repo_root=tmp_path)
    save_forgetting_candidates([
        ForgettingCandidate(candidate_id="forget_1", unit_ids=["u1"], reason="policy_medium_term", review_required=True),
    ], repo_root=tmp_path)
    pack = create_review_pack(repo_root=tmp_path)
    assert pack is not None
    assert len(pack.items) >= 1
    assert pack.items[0].kind == "forgetting"
    got = get_review_pack(pack.pack_id, repo_root=tmp_path)
    assert got is not None
    assert got.pack_id == pack.pack_id


def test_archival_policies_default():
    from workflow_dataset.memory_curation.archival_policies import get_default_archival_policies, get_archival_policy_by_id
    policies = get_default_archival_policies()
    assert len(policies) >= 1
    p = get_archival_policy_by_id("session_history_old")
    assert p is not None
    assert p.min_age_days >= 60
    assert p.require_review_before_archive is True


def test_store_protection_rules_roundtrip(tmp_path):
    from workflow_dataset.memory_curation.models import MemoryProtectionRule
    from workflow_dataset.memory_curation.store import save_protection_rules, load_protection_rules
    rules = [
        MemoryProtectionRule(rule_id="custom", label="Custom", protection_reason="Test reason.", active=True),
    ]
    save_protection_rules(rules, repo_root=tmp_path)
    loaded = load_protection_rules(repo_root=tmp_path)
    assert len(loaded) == 1
    assert loaded[0].rule_id == "custom"
    assert loaded[0].protection_reason == "Test reason."
