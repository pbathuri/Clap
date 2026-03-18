"""
Tests for M1 vertical slice: file observer, event log, personal graph, CLI gating.
All use temp directories; no file content is read.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.observe.file_activity import (
    collect_file_events,
    file_snapshot_payload,
)
from workflow_dataset.observe.local_events import (
    ObservationEvent,
    EventSource,
    append_events,
    load_events,
)
from workflow_dataset.personal.work_graph import ingest_file_events
import sqlite3

from workflow_dataset.personal.graph_store import count_edges, count_nodes, init_store


def test_file_observer_emits_metadata_only(tmp_path: Path) -> None:
    """File observer emits events with metadata only; no content field."""
    (tmp_path / "a.txt").write_text("secret content")
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "c.csv").write_text("data")
    events = collect_file_events(
        [tmp_path],
        max_files_per_scan=100,
    )
    assert len(events) >= 3
    for evt in events:
        assert evt.source == EventSource.FILE
        assert "payload" in evt.model_dump()
        payload = evt.payload
        assert "path" in payload
        assert "filename" in payload
        assert "event_kind" in payload
        assert payload["event_kind"] == "snapshot"
        assert "content" not in payload
        assert "body" not in payload
    paths = {evt.payload["path"] for evt in events}
    assert str(tmp_path / "a.txt") in paths or any("a.txt" in p for p in paths)
    for p in (evt.payload for evt in events):
        assert "secret content" not in str(p) and "secret content" not in json.dumps(p)


def test_file_snapshot_payload_no_content(tmp_path: Path) -> None:
    """file_snapshot_payload does not read file contents."""
    f = tmp_path / "x.txt"
    f.write_text("never read")
    payload = file_snapshot_payload(f, None, "2025-01-01T12:00:00Z")
    assert "path" in payload
    assert "filename" in payload
    assert "size" in payload
    assert "event_kind" in payload
    assert "snapshot" == payload["event_kind"]
    assert "never read" not in str(payload)
    assert "content" not in payload


def test_event_log_write_and_reload(tmp_path: Path) -> None:
    """Events can be appended and loaded back from JSONL."""
    from workflow_dataset.utils.dates import utc_now_iso
    evt1 = ObservationEvent(
        event_id="evt_abc",
        source=EventSource.FILE,
        timestamp_utc=utc_now_iso(),
        payload={"path": "/tmp/a", "filename": "a", "event_kind": "snapshot"},
    )
    evt2 = ObservationEvent(
        event_id="evt_def",
        source=EventSource.FILE,
        timestamp_utc=utc_now_iso(),
        payload={"path": "/tmp/b", "filename": "b", "event_kind": "snapshot"},
    )
    log_dir = tmp_path / "log"
    path = append_events(log_dir, [evt1, evt2])
    assert path.exists()
    assert path.suffix == ".jsonl"
    loaded = load_events(log_dir)
    assert len(loaded) == 2
    ids = {e.event_id for e in loaded}
    assert "evt_abc" in ids and "evt_def" in ids
    for e in loaded:
        assert e.source == EventSource.FILE
        assert e.payload.get("event_kind") == "snapshot"


def test_personal_graph_updates_from_file_events(tmp_path: Path) -> None:
    """Ingesting file events creates file_ref, folder, project nodes and edges."""
    root = tmp_path / "work"
    root.mkdir()
    (root / "proj1").mkdir()
    (root / "proj1" / "doc.txt").write_text("x")
    (root / "proj1" / "sheet.csv").write_text("y")
    events = collect_file_events([root], max_files_per_scan=100)
    assert len(events) >= 3
    graph_path = tmp_path / "graph.sqlite"
    nodes_delta, edges_delta = ingest_file_events(
        graph_path,
        events,
        root_paths=[root],
    )
    assert nodes_delta >= 3
    assert edges_delta >= 2
    conn = sqlite3.connect(str(graph_path))
    try:
        n_nodes = count_nodes(conn)
        n_edges = count_edges(conn)
        assert n_nodes >= 3
        assert n_edges >= 2
        # Should have file_in_folder and/or file_in_project
        n_file_in = count_edges(conn, "file_in_folder") + count_edges(conn, "file_in_project")
        assert n_file_in >= 2
    finally:
        conn.close()


def test_cli_observe_respects_config_gating(tmp_path: Path) -> None:
    """CLI observe exits without writing when observation disabled or file not allowed."""
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    runner = CliRunner()
    # Config with observation_enabled: false
    config_off = tmp_path / "config_off.yaml"
    config_off.write_text("""
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
  event_log_dir: data/local/event_log
  graph_store_path: data/local/graph.sqlite
  audit_log_path: data/local/audit.sqlite
agent:
  observation_enabled: false
  observation_tier: 1
  allowed_observation_sources: [file]
  file_observer:
    root_paths: [.]
    max_files_per_scan: 100
    graph_update_enabled: true
""")
    result = runner.invoke(app, ["observe", "run", "--config", str(config_off)])
    assert result.exit_code == 0
    assert "observation disabled" in result.output.lower() or "false" in result.output.lower()
    assert not (tmp_path / "data" / "local" / "event_log").exists()


def test_cli_observe_runs_and_writes_when_enabled(tmp_path: Path) -> None:
    """When observation enabled and file allowed and root_paths set, observe writes events and graph."""
    from typer.testing import CliRunner

    from workflow_dataset.cli import app

    scan_root = tmp_path / "scan_me"
    scan_root.mkdir()
    (scan_root / "f1.txt").write_text("meta only")
    log_dir = tmp_path / "event_log"
    graph_path = tmp_path / "graph.sqlite"
    audit_path = tmp_path / "audit.sqlite"
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
  audit_log_path: {audit_path}
agent:
  observation_enabled: true
  observation_tier: 1
  allowed_observation_sources: [file]
  file_observer:
    root_paths: [\"{scan_root.as_posix()}\"]
    max_files_per_scan: 100
    graph_update_enabled: true
""")
    runner = CliRunner()
    result = runner.invoke(app, ["observe", "run", "--config", str(config)])
    assert result.exit_code == 0
    assert log_dir.exists()
    jsonl_files = list(log_dir.glob("events_*.jsonl"))
    assert len(jsonl_files) >= 1
    assert graph_path.exists()
    conn = sqlite3.connect(str(graph_path))
    try:
        assert count_nodes(conn) >= 1
    finally:
        conn.close()
