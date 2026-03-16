"""
Tests for M2 interpretation loop: routine detection, suggestion generation,
persistence, and CLI suggest. All use temp dirs; no file content read.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from workflow_dataset.observe.local_events import (
    ObservationEvent,
    EventSource,
    append_events,
    load_all_events,
)
from workflow_dataset.personal.routine_detector import detect_routines
from workflow_dataset.personal.work_graph import persist_routines
from workflow_dataset.personal.suggestion_engine import (
    generate_suggestions,
    persist_suggestions,
    load_suggestions,
    Suggestion,
)
from workflow_dataset.personal.graph_store import count_nodes, list_suggestions
from workflow_dataset.cli import app


def _file_event(path: str, project: str = "", extension: str = "", hour_utc: int = 12, ts: str = "2026-03-15T12:00:00Z") -> ObservationEvent:
    return ObservationEvent(
        event_id=f"evt_{path.replace('/', '_')}",
        source=EventSource.FILE,
        timestamp_utc=ts if hour_utc is None else ts[:11] + f"{hour_utc:02d}:00:00Z",
        payload={
            "path": path,
            "filename": Path(path).name,
            "extension": extension,
            "is_dir": False,
            "event_kind": "snapshot",
        },
    )


def test_routine_detection_from_synthetic_events(tmp_path: Path) -> None:
    """Routine detection produces deterministic routines from file-event fixtures."""
    events = [
        _file_event("/root/proj_a/f1.csv", project="proj_a", extension="csv", hour_utc=9),
        _file_event("/root/proj_a/f2.csv", project="proj_a", extension="csv", hour_utc=9),
        _file_event("/root/proj_a/f3.xlsx", project="proj_a", extension="xlsx", hour_utc=9),
        _file_event("/root/proj_a/f4.csv", project="proj_a", extension="csv", hour_utc=10),
        _file_event("/root/proj_b/doc.txt", project="proj_b", extension="txt", hour_utc=14),
        _file_event("/root/proj_b/other.txt", project="proj_b", extension="txt", hour_utc=14),
        _file_event("/root/proj_b/readme.txt", project="proj_b", extension="txt", hour_utc=14),
    ]
    root_paths = [Path("/root")]
    routines = detect_routines(events, root_paths=root_paths, min_project_touches=2, min_folder_touches=2)
    assert len(routines) >= 1
    types = {r["routine_type"] for r in routines}
    assert "frequent_project" in types or "repeated_extensions_by_project" in types
    proj_routines = [r for r in routines if r.get("routine_type") == "frequent_project"]
    if proj_routines:
        assert any(r.get("project") == "proj_a" for r in proj_routines)


def test_suggestion_generation_from_routines() -> None:
    """Suggestions are generated from inferred routines and are explainable."""
    routines = [
        {"routine_type": "frequent_project", "project": "ops", "touch_count": 10, "confidence": 0.8, "supporting_signals": ["project_touches=10"]},
        {"routine_type": "repeated_extensions_by_project", "project": "data", "extensions": ["csv", "xlsx"], "touch_count": 5, "confidence": 0.75, "supporting_signals": []},
        {"routine_type": "frequent_folder", "path": "/home/user/work/active", "touch_count": 4, "confidence": 0.7, "supporting_signals": []},
    ]
    suggestions = generate_suggestions(routines)
    assert len(suggestions) >= 2
    for s in suggestions:
        assert s.suggestion_id
        assert s.suggestion_type in ("focus_project", "operations_workflow", "named_project")
        assert s.title
        assert s.description
        assert 0 <= s.confidence_score <= 1
        assert s.status == "pending"
    titles = [s.title for s in suggestions]
    assert any("focus" in t.lower() or "pin" in t.lower() for t in titles)
    assert any("operations" in t.lower() or "workflow" in t.lower() for t in titles) or any("named" in t.lower() for t in titles)


def test_suggestion_persistence(tmp_path: Path) -> None:
    """Suggestions can be persisted and loaded from local store."""
    db = tmp_path / "graph.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    from workflow_dataset.personal.graph_store import init_store
    init_store(db)
    suggestions = [
        Suggestion(suggestion_id="sug_1", suggestion_type="focus_project", title="Pin X?", description="You often work in X.", confidence_score=0.8, supporting_signals=["a"], created_utc="2026-03-15T12:00:00Z", status="pending"),
        Suggestion(suggestion_id="sug_2", suggestion_type="named_project", title="Mark Y?", description="Active folder Y.", confidence_score=0.7, supporting_signals=[], created_utc="2026-03-15T12:00:00Z", status="pending"),
    ]
    persist_suggestions(db, suggestions)
    loaded = load_suggestions(db, status_filter="pending", limit=10)
    assert len(loaded) == 2
    ids = {s["suggestion_id"] for s in loaded}
    assert "sug_1" in ids and "sug_2" in ids
    one = next(s for s in loaded if s["suggestion_id"] == "sug_1")
    assert one["title"] == "Pin X?"
    assert one["confidence_score"] == 0.8


def test_cli_suggest_when_no_evidence(tmp_path: Path) -> None:
    """CLI suggest exits cleanly when no event log or no events."""
    config = tmp_path / "config.yaml"
    config.write_text(f"""
project:
  name: x
  version: v1
  output_excel: out.xlsx
  output_csv_dir: out/csv
  output_parquet_dir: out/pq
  qa_report_path: out/qa.md
runtime:
  timezone: UTC
paths:
  raw_official: data/raw
  raw_private: data/private
  interim: data/interim
  processed: data/processed
  prompts: prompts
  context: context
  sqlite_path: w.sqlite
  event_log_dir: {tmp_path / "event_log"}
  graph_store_path: {tmp_path / "graph.sqlite"}
  audit_log_path: {tmp_path / "audit.sqlite"}
agent:
  observation_enabled: false
  file_observer:
    root_paths: []
""")
    runner = CliRunner()
    result = runner.invoke(app, ["suggest", "--config", str(config)])
    assert result.exit_code == 0
    assert "no file events" in result.output.lower()


def test_cli_suggest_with_events(tmp_path: Path) -> None:
    """CLI suggest loads events, infers routines, generates and persists suggestions."""
    log_dir = tmp_path / "event_log"
    log_dir.mkdir(parents=True)
    graph_path = tmp_path / "graph.sqlite"
    events = [
        _file_event("/data/ops/f1.csv", project="ops", extension="csv"),
        _file_event("/data/ops/f2.csv", project="ops", extension="csv"),
        _file_event("/data/ops/f3.xlsx", project="ops", extension="xlsx"),
        _file_event("/data/ops/f4.csv", project="ops", extension="csv"),
    ]
    append_events(log_dir, events)
    config = tmp_path / "config.yaml"
    config.write_text(f"""
project:
  name: x
  version: v1
  output_excel: out.xlsx
  output_csv_dir: out/csv
  output_parquet_dir: out/pq
  qa_report_path: out/qa.md
runtime:
  timezone: UTC
paths:
  raw_official: data/raw
  raw_private: data/private
  interim: data/interim
  processed: data/processed
  prompts: prompts
  context: context
  sqlite_path: w.sqlite
  event_log_dir: {log_dir}
  graph_store_path: {graph_path}
  audit_log_path: {tmp_path / "audit.sqlite"}
agent:
  observation_enabled: true
  file_observer:
    root_paths: ["/data"]
""")
    runner = CliRunner()
    result = runner.invoke(app, ["suggest", "--config", str(config)])
    assert result.exit_code == 0
    assert "events_loaded=4" in result.output or "events_loaded=" in result.output
    assert graph_path.exists()
    conn = sqlite3.connect(str(graph_path))
    try:
        n_nodes = count_nodes(conn)
        suggs = list_suggestions(conn, status_filter="pending", limit=10)
        assert n_nodes >= 1
        assert len(suggs) >= 1
    finally:
        conn.close()


def test_no_suggestions_when_no_routine_evidence(tmp_path: Path) -> None:
    """When events are too few to form routines, no suggestions are produced."""
    events = [
        _file_event("/x/one.txt", project="x", extension="txt"),
    ]
    routines = detect_routines(events, min_project_touches=3, min_folder_touches=3)
    assert len(routines) == 0
    suggestions = generate_suggestions(routines)
    assert len(suggestions) == 0
