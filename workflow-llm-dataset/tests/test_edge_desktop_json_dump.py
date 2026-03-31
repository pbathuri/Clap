"""Edge-desktop snapshot JSON must parse with strict json.loads (json.tool)."""

from __future__ import annotations

import json
import math

from workflow_dataset.edge_desktop.json_dump import dumps_snapshot_json, sanitize_snapshot_for_json
from workflow_dataset.edge_desktop.snapshot import build_edge_desktop_snapshot


def test_dumps_snapshot_json_strict_parse() -> None:
    snap = {
        "generated_at": "t",
        "repo_root": "/r",
        "nested": {"x": float("nan"), "y": float("inf"), "z": 1.5},
        "text": "line\x00break\x01",
        "arr": [1, 2, 3],
    }
    text = dumps_snapshot_json(snap)
    parsed = json.loads(text)
    assert parsed["nested"]["x"] is None
    assert parsed["nested"]["y"] is None
    assert parsed["nested"]["z"] == 1.5
    assert " " in parsed["text"] or parsed["text"] == "line break"


def test_sanitize_preserves_normal_strings() -> None:
    assert sanitize_snapshot_for_json({"a": "hello"}) == {"a": "hello"}


def test_minimal_snapshot_roundtrip() -> None:
    text = dumps_snapshot_json({"k": "v"})
    assert json.loads(text) == {"k": "v"}


def test_supervised_task_run_survives_strict_json_dump() -> None:
    """Edge snapshot sanitizer must emit strict JSON for supervised_task_run subtree."""
    snap = {
        "supervised_task_run": {
            "total_stored": 2,
            "recent": [{"run_id": "r1", "status": "completed"}],
            "last_task_run": {
                "run_id": "r2",
                "workflow_pattern": "inspect_status_report",
                "steps_preview": [{"step_id": "list_directory", "step_status": "completed"}],
            },
        },
        "nested_bad": {"x": float("nan")},
    }
    text = dumps_snapshot_json(snap)
    parsed = json.loads(text)
    assert parsed["supervised_task_run"]["total_stored"] == 2
    assert parsed["nested_bad"]["x"] is None


def test_edge_desktop_snapshot_includes_supervised_task_run(tmp_path) -> None:
    """Shallow task-run surface for desktop shell (full detail still under local_operator_summary)."""
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs" / "settings.yaml").write_text("release: {}", encoding="utf-8")
    snap = build_edge_desktop_snapshot(tmp_path)
    assert "supervised_task_run" in snap
    surface = snap["supervised_task_run"]
    assert "last_task_run" in surface
    assert "recent" in surface
    assert "total_stored" in surface
    assert isinstance(surface["recent"], list)
