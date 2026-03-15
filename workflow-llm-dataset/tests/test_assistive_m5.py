"""Tests for M5 style-aware assistive loop: profiles, candidates, suggestions, drafts, graph, CLI."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from workflow_dataset.personal.assistive_models import StyleAwareSuggestion, DraftStructure
from workflow_dataset.personal.style_profiles import (
    StyleProfile,
    build_profiles_from_style_signals,
    save_style_profile,
    load_style_profiles,
)
from workflow_dataset.personal.imitation_candidates import (
    ImitationCandidate,
    collect_candidates_from_profiles,
)
from workflow_dataset.personal.style_suggestion_engine import (
    generate_style_aware_suggestions,
    persist_style_aware_suggestions,
    load_style_aware_suggestions,
)
from workflow_dataset.personal.draft_structure_engine import (
    generate_draft_structures,
    persist_draft_structures,
    load_draft_structures,
)
from workflow_dataset.personal.assistive_graph import (
    persist_style_profile_nodes,
    persist_imitation_candidate_nodes,
    persist_draft_structure_nodes,
    persist_style_aware_suggestion_nodes,
)
from workflow_dataset.personal.graph_store import init_store, count_nodes, count_edges
from workflow_dataset.personal.work_graph import NodeType


@pytest.fixture
def style_signal_records() -> list[dict]:
    return [
        {"pattern_type": "naming_convention", "value": "snake_case", "description": "Snake case", "confidence": 0.9, "evidence_paths": [], "session_id": "s1", "project_path": "/p"},
        {"pattern_type": "folder_layout", "value": "flat", "description": "Flat", "confidence": 0.7, "evidence_paths": [], "session_id": "s1", "project_path": "/p"},
    ]


@pytest.fixture
def assistive_context() -> dict:
    return {
        "projects": [{"node_id": "project_a", "label": "proj_a"}],
        "domains": [{"node_id": "dom_1", "label": "creative"}],
        "style_signals": [{"pattern_type": "naming", "value": "v1", "description": "Rev"}],
        "parsed_artifacts": [
            {"source_path": "/p/doc.txt", "artifact_family": "text_document", "title": "Doc", "summary": "S"},
            {"source_path": "/p/sheet.xlsx", "artifact_family": "spreadsheet_table", "title": "Sheet", "summary": "S2"},
        ],
    }


def test_build_profiles_from_style_signals(style_signal_records: list, tmp_path: Path) -> None:
    profiles = build_profiles_from_style_signals(style_signal_records, session_id="s1", project_id="p1")
    assert len(profiles) >= 1
    for p in profiles:
        assert p.profile_id
        assert p.profile_type or p.style_family
    save_style_profile(profiles[0], tmp_path)
    assert (tmp_path / f"{profiles[0].profile_id}.json").exists()
    loaded = load_style_profiles(tmp_path)
    assert len(loaded) == 1


def test_imitation_candidates_from_profiles(style_signal_records: list, tmp_path: Path) -> None:
    # Use multiple signals of same type so one profile has evidence_count >= 2 (required for candidate)
    signals = style_signal_records + [{"pattern_type": "naming_convention", "value": "v2", "description": "Also naming", "confidence": 0.8, "evidence_paths": [], "session_id": "s1", "project_path": ""}]
    profiles = build_profiles_from_style_signals(signals, session_id="s1", project_id="")
    for p in profiles:
        save_style_profile(p, tmp_path)
    candidates = collect_candidates_from_profiles(tmp_path)
    assert len(candidates) >= 1
    assert candidates[0].candidate_id
    assert candidates[0].confidence_score >= 0 or candidates[0].strength >= 0


def test_generate_style_aware_suggestions(assistive_context: dict, tmp_path: Path) -> None:
    profiles = build_profiles_from_style_signals(
        assistive_context["style_signals"],
        session_id="",
        project_id="",
    )
    for p in profiles:
        save_style_profile(p, tmp_path)
    profiles_loaded = load_style_profiles(tmp_path)
    candidates = collect_candidates_from_profiles(tmp_path)
    suggestions = generate_style_aware_suggestions(assistive_context, profiles_loaded, candidates, routines=[], max_per_category=3)
    assert len(suggestions) >= 1
    for s in suggestions:
        assert s.suggestion_id and s.suggestion_type and s.rationale
    persist_style_aware_suggestions(suggestions, tmp_path)
    assert (tmp_path / "suggestions.json").exists()
    loaded = load_style_aware_suggestions(tmp_path)
    assert len(loaded) == len(suggestions)


def test_generate_draft_structures(assistive_context: dict, tmp_path: Path) -> None:
    profiles = build_profiles_from_style_signals(assistive_context["style_signals"], session_id="", project_id="")
    drafts = generate_draft_structures(assistive_context, profiles, draft_types=["project_brief", "meeting_agenda", "reconciliation_checklist"])
    assert len(drafts) >= 2
    for d in drafts:
        assert d.draft_id and d.draft_type and d.structure_outline
    persist_draft_structures(drafts, tmp_path)
    assert (tmp_path / "draft_structures.json").exists()
    loaded = load_draft_structures(tmp_path)
    assert len(loaded) == len(drafts)


def test_assistive_graph_persistence(tmp_path: Path) -> None:
    db = tmp_path / "graph.sqlite"
    init_store(db)
    conn = sqlite3.connect(str(db))
    from workflow_dataset.personal.graph_store import add_node
    from workflow_dataset.personal.work_graph import PersonalWorkGraphNode
    proj_id = "project_test"
    add_node(conn, PersonalWorkGraphNode(node_id=proj_id, node_type=NodeType.PROJECT, label="Test", source="test", created_utc="", updated_utc=""))
    conn.commit()
    conn.close()
    profiles = [StyleProfile(profile_id="prof_1", profile_type="naming_style", domain="creative", confidence=0.8, project_paths=["Test"])]
    candidates = [ImitationCandidate(candidate_id="cand_1", candidate_type="report_style", domain="ops", source_patterns=["prof_1"])]
    drafts = [DraftStructure(draft_id="draft_1", draft_type="project_brief", title="Brief", structure_outline="# Brief", project_id="Test")]
    suggestions = [StyleAwareSuggestion(suggestion_id="sug_1", suggestion_type="organization", title="Template", rationale="Observed", confidence_score=0.7)]
    project_id_by_label = {"Test": proj_id}
    persist_style_profile_nodes(db, profiles, project_id_by_label)
    persist_imitation_candidate_nodes(db, candidates, project_id_by_label)
    persist_draft_structure_nodes(db, drafts, project_id_by_label)
    persist_style_aware_suggestion_nodes(db, suggestions, project_id_by_label)
    conn = sqlite3.connect(str(db))
    assert count_nodes(conn, NodeType.STYLE_PROFILE.value) >= 1
    assert count_nodes(conn, NodeType.IMITATION_CANDIDATE.value) >= 1
    assert count_nodes(conn, NodeType.DRAFT_STRUCTURE.value) >= 1
    assert count_nodes(conn, NodeType.STYLE_AWARE_SUGGESTION.value) >= 1
    assert count_edges(conn, "project_has_style_profile") >= 1
    conn.close()


def test_assist_suggest_cli(tmp_path: Path) -> None:
    import yaml
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    config = tmp_path / "settings.yaml"
    config.write_text(yaml.dump({
        "project": {"name": "t", "version": "1", "output_excel": "x", "output_csv_dir": "c", "output_parquet_dir": "p", "qa_report_path": "q"},
        "runtime": {"timezone": "UTC"},
        "paths": {"raw_official": "r", "raw_private": "r", "interim": "i", "processed": "p", "prompts": "pr", "context": "c", "sqlite_path": "s", "graph_store_path": str(tmp_path / "graph.sqlite")},
        "setup": {
            "setup_dir": str(tmp_path / "setup"),
            "parsed_artifacts_dir": str(tmp_path / "parsed"),
            "style_signals_dir": str(tmp_path / "style_signals"),
            "style_profiles_dir": str(tmp_path / "style_profiles"),
            "setup_reports_dir": str(tmp_path / "reports"),
            "suggestions_dir": str(tmp_path / "suggestions"),
            "draft_structures_dir": str(tmp_path / "draft_structures"),
        },
    }, default_flow_style=False))
    (tmp_path / "setup" / "sessions").mkdir(parents=True)
    (tmp_path / "setup" / "sessions" / "s1.json").write_text('{"session_id": "s1"}')
    (tmp_path / "parsed" / "s1").mkdir(parents=True)
    (tmp_path / "parsed" / "s1" / "a.json").write_text(json.dumps({"source_path": "/x/d.txt", "artifact_family": "text_document", "title": "T", "summary": "S", "error": ""}))
    (tmp_path / "style_signals" / "s1").mkdir(parents=True)
    (tmp_path / "style_signals" / "s1" / "signatures.json").write_text('[{"pattern_type": "naming", "value": "v1", "description": "D", "confidence": 0.8, "evidence_paths": [], "session_id": "s1", "project_path": ""}]')
    runner = CliRunner()
    result = runner.invoke(app, ["assist", "suggest", "--config", str(config), "--session-id", "s1"])
    assert result.exit_code == 0
    assert (tmp_path / "suggestions" / "suggestions.json").exists()


def test_assist_draft_cli(tmp_path: Path) -> None:
    import yaml
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    config = tmp_path / "settings.yaml"
    config.write_text(yaml.dump({
        "project": {"name": "t", "version": "1", "output_excel": "x", "output_csv_dir": "c", "output_parquet_dir": "p", "qa_report_path": "q"},
        "runtime": {"timezone": "UTC"},
        "paths": {"raw_official": "r", "raw_private": "r", "interim": "i", "processed": "p", "prompts": "pr", "context": "c", "sqlite_path": "s", "graph_store_path": str(tmp_path / "graph.sqlite")},
        "setup": {
            "setup_dir": str(tmp_path / "setup"),
            "parsed_artifacts_dir": str(tmp_path / "parsed"),
            "style_signals_dir": str(tmp_path / "style_signals"),
            "style_profiles_dir": str(tmp_path / "style_profiles"),
            "setup_reports_dir": str(tmp_path / "reports"),
            "suggestions_dir": str(tmp_path / "suggestions"),
            "draft_structures_dir": str(tmp_path / "draft_structures"),
        },
    }, default_flow_style=False))
    (tmp_path / "setup" / "sessions").mkdir(parents=True)
    (tmp_path / "setup" / "sessions" / "s1.json").write_text('{"session_id": "s1"}')
    (tmp_path / "parsed" / "s1").mkdir(parents=True)
    (tmp_path / "style_signals" / "s1").mkdir(parents=True)
    (tmp_path / "style_signals" / "s1" / "signatures.json").write_text('[]')
    runner = CliRunner()
    result = runner.invoke(app, ["assist", "draft", "--config", str(config), "--session-id", "s1"])
    assert result.exit_code == 0
    assert (tmp_path / "draft_structures" / "draft_structures.json").exists()


def test_corpus_from_assistive(tmp_path: Path) -> None:
    from workflow_dataset.personal.style_suggestion_engine import persist_style_aware_suggestions, load_style_aware_suggestions
    from workflow_dataset.personal.draft_structure_engine import persist_draft_structures, generate_draft_structures
    from workflow_dataset.llm.corpus_builder import build_personal_corpus_from_assistive, load_corpus
    suggestions = [StyleAwareSuggestion(suggestion_id="s1", suggestion_type="organization", title="T", rationale="R", confidence_score=0.8)]
    persist_style_aware_suggestions(suggestions, tmp_path / "sug")
    drafts = generate_draft_structures({"domains": [], "parsed_artifacts": []}, [], draft_types=["project_brief"])
    persist_draft_structures(drafts, tmp_path / "drafts")
    total, counts = build_personal_corpus_from_assistive(tmp_path / "sug", tmp_path / "drafts", tmp_path / "corpus_out")
    assert total >= 1
    assert (tmp_path / "corpus_out" / "personal_corpus_assistive.jsonl").exists()
    docs = load_corpus(tmp_path / "corpus_out" / "personal_corpus_assistive.jsonl")
    assert len(docs) >= 1


def test_sft_from_assistive(tmp_path: Path) -> None:
    from workflow_dataset.personal.style_suggestion_engine import persist_style_aware_suggestions
    from workflow_dataset.personal.draft_structure_engine import persist_draft_structures, generate_draft_structures
    from workflow_dataset.llm.sft_builder import build_personal_sft_from_assistive
    suggestions = [StyleAwareSuggestion(suggestion_id="s1", suggestion_type="style", title="Naming", rationale="Consistent", confidence_score=0.8)]
    persist_style_aware_suggestions(suggestions, tmp_path / "sug")
    drafts = generate_draft_structures({"domains": []}, [], draft_types=["project_brief"])
    persist_draft_structures(drafts, tmp_path / "drafts")
    n_train, n_val, n_test, counts = build_personal_sft_from_assistive(tmp_path / "sug", tmp_path / "drafts", tmp_path / "sft_out", max_examples_per_type=5)
    assert (tmp_path / "sft_out" / "train.jsonl").exists()
    assert "why_this_suggestion" in counts or "why_this_structure" in counts
    assert n_train + n_val + n_test >= 1
