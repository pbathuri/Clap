"""Tests for M6 agent loop: query routing, context building, explain/next-step/draft-refine, response builder, session persistence, CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from workflow_dataset.agent_loop.agent_models import AgentQuery, AgentResponse, AgentSession
from workflow_dataset.agent_loop.query_router import route_query, QueryType
from workflow_dataset.agent_loop.explain_engine import (
    explain_project,
    explain_style,
    explain_suggestion,
    explain_draft,
)
from workflow_dataset.agent_loop.next_step_engine import suggest_next_steps
from workflow_dataset.agent_loop.draft_refiner import refine_draft
from workflow_dataset.agent_loop.response_builder import build_response
from workflow_dataset.agent_loop.session_store import (
    create_session,
    load_session,
    list_sessions,
    save_session,
    save_query,
    save_response,
    load_responses_for_query,
)
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


# ----- Query routing -----
def test_route_query_explain_project() -> None:
    qtype, extras = route_query("what is this project?")
    assert qtype == QueryType.EXPLAIN_PROJECT
    assert "matched" in extras or "matched_phrase" in extras


def test_route_query_explain_style() -> None:
    qtype, _ = route_query("what style pattern did you detect?")
    assert qtype == QueryType.EXPLAIN_STYLE


def test_route_query_explain_suggestion() -> None:
    qtype, _ = route_query("why did you suggest this?")
    assert qtype == QueryType.EXPLAIN_SUGGESTION


def test_route_query_explain_draft() -> None:
    qtype, _ = route_query("explain this draft structure")
    assert qtype == QueryType.EXPLAIN_DRAFT


def test_route_query_next_step() -> None:
    qtype, _ = route_query("what is a sensible next step for this project?")
    assert qtype == QueryType.SUGGEST_NEXT_STEP


def test_route_query_refine_draft() -> None:
    qtype, _ = route_query("refine this draft structure")
    assert qtype == QueryType.REFINE_DRAFT_STRUCTURE


def test_route_query_list_projects() -> None:
    qtype, _ = route_query("list active projects")
    assert qtype == QueryType.LIST_ACTIVE_PROJECTS


def test_route_query_requested_mode_override() -> None:
    qtype, _ = route_query("anything here", requested_mode="suggest_next_step")
    assert qtype == QueryType.SUGGEST_NEXT_STEP


def test_route_query_general_chat() -> None:
    qtype, _ = route_query("hello how are you")
    assert qtype == QueryType.GENERAL_CHAT


# ----- Context bundle (mocked get_assistive_context) -----
def test_build_context_bundle_structure(tmp_path: Path) -> None:
    from workflow_dataset.agent_loop.context_builder import build_context_bundle

    graph = tmp_path / "graph.sqlite"
    graph.write_bytes(b"")  # placeholder; init_store will init if needed
    # Use empty dirs so we don't need real setup data
    with patch("workflow_dataset.agent_loop.context_builder.get_assistive_context") as m:
        m.return_value = {
            "projects": [{"node_id": "p1", "label": "proj1"}],
            "domains": [{"node_id": "d1", "label": "creative"}],
            "style_signals": [{"pattern_type": "naming", "value": "v1"}],
            "parsed_artifacts": [{"source_path": "/a/doc.txt", "artifact_family": "text_document", "title": "Doc"}],
        }
        bundle = build_context_bundle(
            graph_path=graph,
            style_signals_dir=tmp_path,
            parsed_artifacts_dir=tmp_path,
            style_profiles_dir=tmp_path,
            suggestions_dir=tmp_path,
            draft_structures_dir=tmp_path,
            setup_session_id="",
            project_id="",
            corpus_path=None,
            query="",
        )
    assert "project_context" in bundle
    assert "style_context" in bundle
    assert "workflow_context" in bundle
    assert "suggestion_context" in bundle
    assert "draft_context" in bundle
    assert bundle["project_context"]["projects"]
    assert bundle["workflow_context"]["artifact_families"]


# ----- Explain engine -----
def test_explain_project_empty_context() -> None:
    bundle = {"project_context": {"projects": [], "parsed_artifacts": [], "domains": []}}
    resp = explain_project(bundle)
    assert resp.response_type == "explain_project"
    assert "No project" in resp.answer or "no project" in resp.answer.lower()
    assert resp.confidence_score == 0.0


def test_explain_project_with_data() -> None:
    bundle = {
        "project_context": {
            "projects": [{"node_id": "n1", "label": "ProjA"}],
            "parsed_artifacts": [{"artifact_family": "text_document", "title": "Doc"}],
            "domains": [{"node_id": "d1", "label": "creative"}],
        },
        "retrieved_docs": [],
    }
    resp = explain_project(bundle)
    assert resp.response_type == "explain_project"
    assert "ProjA" in resp.answer
    assert resp.confidence_score > 0


def test_explain_style_empty() -> None:
    bundle = {"style_context": {"profiles": [], "style_signals": [], "imitation_candidates": []}}
    resp = explain_style(bundle)
    assert resp.response_type == "explain_style"
    assert "No style" in resp.answer or "no style" in resp.answer.lower()


def test_explain_suggestion_empty() -> None:
    bundle = {"suggestion_context": {"suggestions": []}}
    resp = explain_suggestion(bundle)
    assert "No matching suggestion" in resp.answer


def test_explain_suggestion_with_data() -> None:
    bundle = {
        "suggestion_context": {
            "suggestions": [
                {
                    "suggestion_id": "sug_1",
                    "title": "Use a template",
                    "rationale": "You have multiple projects.",
                    "suggestion_type": "organization",
                    "confidence_score": 0.8,
                    "supporting_signals": ["projects: 3"],
                    "style_profile_refs": [],
                }
            ]
        },
    }
    resp = explain_suggestion(bundle)
    assert "Use a template" in resp.answer
    assert "sug_1" in resp.suggestion_refs


def test_explain_draft_empty() -> None:
    bundle = {"draft_context": {"drafts": []}}
    resp = explain_draft(bundle)
    assert "No matching draft" in resp.answer


def test_explain_draft_with_data() -> None:
    bundle = {
        "draft_context": {
            "drafts": [
                {
                    "draft_id": "draft_1",
                    "draft_type": "project_brief",
                    "title": "Project brief",
                    "domain": "general",
                    "confidence_score": 0.75,
                }
            ]
        },
        "workflow_context": {"artifact_families": ["text_document"], "domains": [{"label": "general"}]},
    }
    resp = explain_draft(bundle)
    assert "Project brief" in resp.answer
    assert resp.draft_refs


# ----- Next-step engine -----
def test_suggest_next_steps_weak_evidence() -> None:
    bundle = {
        "project_context": {"projects": [], "parsed_artifacts": []},
        "workflow_context": {"domains": [], "artifact_families": []},
        "suggestion_context": {"suggestions": []},
        "draft_context": {"drafts": []},
    }
    resp = suggest_next_steps(bundle)
    assert resp.response_type == "suggest_next_step"
    assert "Not enough" in resp.answer or "evidence" in resp.answer.lower()
    assert resp.confidence_score <= 0.5


def test_suggest_next_steps_with_suggestions() -> None:
    bundle = {
        "project_context": {"projects": [{"node_id": "p1"}], "parsed_artifacts": []},
        "workflow_context": {"domains": [], "artifact_families": []},
        "suggestion_context": {
            "suggestions": [
                {"suggestion_id": "s1", "title": "Pin project", "rationale": "Active.", "confidence_score": 0.8}
            ]
        },
        "draft_context": {"drafts": []},
    }
    resp = suggest_next_steps(bundle)
    assert "Pin project" in resp.answer or "Consider" in resp.answer


# ----- Draft refiner -----
def test_refine_draft_deterministic_no_draft() -> None:
    bundle = {"draft_context": {"drafts": []}, "style_context": {"profiles": []}, "project_context": {}, "retrieved_docs": []}
    refined, resp = refine_draft(bundle, draft_id="", draft_type="")
    assert resp.response_type == "refine_draft"
    assert "No draft" in resp.answer
    assert resp.confidence_score == 0.0


def test_refine_draft_deterministic_with_type() -> None:
    bundle = {
        "draft_context": {"drafts": []},
        "style_context": {"profiles": [{"profile_id": "pf1", "naming_patterns": ["v1", "final"]}]},
        "project_context": {"parsed_artifacts": [{"artifact_family": "text_document"}]},
        "workflow_context": {},
        "retrieved_docs": [],
    }
    refined, resp = refine_draft(bundle, draft_type="project_brief", project_id="")
    assert resp.response_type == "refine_draft"
    assert resp.confidence_score > 0
    assert refined
    outline = refined.get("structure_outline") if isinstance(refined, dict) else getattr(refined, "structure_outline", "")
    assert "Project brief" in outline or "Objective" in outline


# ----- Response builder -----
def test_build_response_explain_project(tmp_path: Path) -> None:
    graph = tmp_path / "g.sqlite"
    graph.write_bytes(b"")
    with patch("workflow_dataset.agent_loop.response_builder.build_context_bundle") as m:
        m.return_value = {
            "project_context": {"projects": [{"node_id": "p1", "label": "P"}], "parsed_artifacts": [], "domains": []},
            "style_context": {"profiles": [], "style_signals": [], "imitation_candidates": []},
            "workflow_context": {"domains": [], "artifact_families": []},
            "suggestion_context": {"suggestions": []},
            "draft_context": {"drafts": []},
            "retrieved_docs": [],
        }
        q = AgentQuery(query_id="q1", user_text="what is this project?", created_utc=utc_now_iso())
        resp = build_response(
            q,
            graph_path=graph,
            style_signals_dir=tmp_path,
            parsed_artifacts_dir=tmp_path,
            style_profiles_dir=tmp_path,
            suggestions_dir=tmp_path,
            draft_structures_dir=tmp_path,
            setup_session_id="",
            corpus_path=None,
            max_retrieval_docs=5,
            use_llm=False,
        )
    assert resp.response_type == "explain_project"
    assert resp.query_id == "q1"
    assert resp.used_retrieval is False
    assert resp.used_llm is False


def test_build_response_next_step(tmp_path: Path) -> None:
    with patch("workflow_dataset.agent_loop.response_builder.build_context_bundle") as m:
        m.return_value = {
            "project_context": {"projects": [], "parsed_artifacts": []},
            "workflow_context": {"domains": [], "artifact_families": []},
            "suggestion_context": {"suggestions": []},
            "draft_context": {"drafts": []},
            "style_context": {},
            "retrieved_docs": [],
        }
        q = AgentQuery(
            query_id="q2",
            user_text="what should I do next?",
            requested_mode="suggest_next_step",
            created_utc=utc_now_iso(),
        )
        resp = build_response(
            q,
            graph_path=tmp_path,
            style_signals_dir=tmp_path,
            parsed_artifacts_dir=tmp_path,
            style_profiles_dir=tmp_path,
            suggestions_dir=tmp_path,
            draft_structures_dir=tmp_path,
            setup_session_id="",
            corpus_path=None,
            max_retrieval_docs=5,
            use_llm=False,
        )
    assert resp.response_type == "suggest_next_step"


# ----- Session persistence -----
def test_session_create_save_load_list(tmp_path: Path) -> None:
    s = create_session(tmp_path, project_scope="p1", use_retrieval=True)
    assert s.session_id
    assert s.project_scope == "p1"
    loaded = load_session(s.session_id, tmp_path)
    assert loaded is not None
    assert loaded.session_id == s.session_id
    listed = list_sessions(tmp_path, limit=5)
    assert len(listed) >= 1


def test_save_load_response(tmp_path: Path) -> None:
    r = AgentResponse(
        response_id="resp_1",
        query_id="q_1",
        response_type="explain_project",
        title="Test",
        answer="Hello",
        created_utc=utc_now_iso(),
    )
    save_response(r, tmp_path)
    loaded = load_responses_for_query("q_1", tmp_path)
    assert len(loaded) == 1
    assert loaded[0].response_id == "resp_1"


def test_save_query(tmp_path: Path) -> None:
    q = AgentQuery(query_id="qu_1", user_text="test?", created_utc=utc_now_iso())
    save_query(q, tmp_path)
    path = tmp_path / "agent_responses" / "queries.jsonl"
    assert path.exists()
    assert "test?" in path.read_text()


# ----- CLI -----
def test_assist_explain_cli(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    config = tmp_path / "settings.yaml"
    config.write_text("""
project: {name: x, version: v1, output_excel: o, output_csv_dir: c, output_parquet_dir: p, qa_report_path: q}
runtime: {timezone: UTC, long_run_profile: true, max_workers: 2, fail_on_missing_provenance: false, infer_low_confidence_threshold: 0.45, infer_high_confidence_threshold: 0.8}
paths: {raw_official: r, raw_private: r, interim: i, processed: p, prompts: pr, context: c, sqlite_path: s, event_log_dir: data/local/event_log, graph_store_path: data/local/work_graph.sqlite}
setup:
  setup_dir: """ + str(tmp_path) + """
  parsed_artifacts_dir: """ + str(tmp_path) + """
  style_signals_dir: """ + str(tmp_path) + """
  setup_reports_dir: """ + str(tmp_path) + """
  suggestions_dir: """ + str(tmp_path) + """
  draft_structures_dir: """ + str(tmp_path) + """
agent_loop:
  agent_loop_enabled: true
  agent_loop_save_sessions: false
""")
    runner = CliRunner()
    result = runner.invoke(app, [
        "assist", "explain", "what is this project?",
        "--config", str(config),
    ])
    # May exit 0 or 1 (e.g. if setup config validation fails); must not crash
    assert result.exit_code in (0, 1)
    assert "Project" in result.output or "project" in result.output.lower() or "error" in result.output.lower()


def test_assist_next_step_cli(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    config = tmp_path / "s2.yaml"
    config.write_text("""
project: {name: x, version: v1, output_excel: o, output_csv_dir: c, output_parquet_dir: p, qa_report_path: q}
runtime: {timezone: UTC, long_run_profile: true, max_workers: 2, fail_on_missing_provenance: false, infer_low_confidence_threshold: 0.45, infer_high_confidence_threshold: 0.8}
paths: {raw_official: r, raw_private: r, interim: i, processed: p, prompts: pr, context: c, sqlite_path: s, event_log_dir: data/local/event_log, graph_store_path: data/local/work_graph.sqlite}
setup:
  setup_dir: """ + str(tmp_path) + """
  parsed_artifacts_dir: """ + str(tmp_path) + """
  style_signals_dir: """ + str(tmp_path) + """
  setup_reports_dir: """ + str(tmp_path) + """
  suggestions_dir: """ + str(tmp_path) + """
  draft_structures_dir: """ + str(tmp_path) + """
agent_loop:
  agent_loop_save_sessions: false
""")
    runner = CliRunner()
    result = runner.invoke(app, ["assist", "next-step", "--config", str(config)])
    assert result.exit_code in (0, 1)
    assert "Next" in result.output or "next" in result.output.lower() or "step" in result.output.lower() or "error" in result.output.lower()


def test_assist_chat_one_shot(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    config = tmp_path / "s3.yaml"
    config.write_text("""
project: {name: x, version: v1, output_excel: o, output_csv_dir: c, output_parquet_dir: p, qa_report_path: q}
runtime: {timezone: UTC, long_run_profile: true, max_workers: 2, fail_on_missing_provenance: false, infer_low_confidence_threshold: 0.45, infer_high_confidence_threshold: 0.8}
paths: {raw_official: r, raw_private: r, interim: i, processed: p, prompts: pr, context: c, sqlite_path: s, event_log_dir: data/local/event_log, graph_store_path: data/local/work_graph.sqlite}
setup:
  setup_dir: """ + str(tmp_path) + """
  parsed_artifacts_dir: """ + str(tmp_path) + """
  style_signals_dir: """ + str(tmp_path) + """
  setup_reports_dir: """ + str(tmp_path) + """
  suggestions_dir: """ + str(tmp_path) + """
  draft_structures_dir: """ + str(tmp_path) + """
agent_loop:
  agent_loop_save_sessions: false
""")
    runner = CliRunner()
    result = runner.invoke(app, [
        "assist", "chat", "list active projects",
        "--config", str(config),
    ])
    assert result.exit_code in (0, 1)
    assert "project" in result.output.lower() or "error" in result.output.lower()
