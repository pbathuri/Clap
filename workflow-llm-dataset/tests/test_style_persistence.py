"""Tests for style signal persistence (setup → style_signals/<session_id>/)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.setup.style_persistence import (
    StyleSignalRecord,
    persist_style_signals,
    load_style_signals,
)


def test_persist_and_load_style_signals(tmp_path: Path) -> None:
    """Style signals are written under session_id and loadable."""
    session_id = "sess_abc"
    signals = [
        {"pattern_type": "naming_convention", "value": "snake_case", "confidence": 0.9, "evidence_paths": ["/a/b/c.txt"], "description": "Snake case names"},
        {"pattern_type": "folder_layout", "value": "flat", "confidence": 0.7, "description": "Flat layout"},
    ]
    out_path = persist_style_signals(session_id, signals, tmp_path)
    assert out_path == tmp_path / session_id / "signatures.json"
    assert out_path.exists()
    loaded = load_style_signals(session_id, tmp_path)
    assert len(loaded) == 2
    assert loaded[0].pattern_type == "naming_convention"
    assert loaded[0].value == "snake_case"
    assert loaded[1].pattern_type == "folder_layout"


def test_load_style_signals_empty_when_missing(tmp_path: Path) -> None:
    """load_style_signals returns [] when session dir or file is missing."""
    assert load_style_signals("nonexistent", tmp_path) == []
    (tmp_path / "sess_x").mkdir()
    assert load_style_signals("sess_x", tmp_path) == []


def test_style_signal_record_roundtrip() -> None:
    """StyleSignalRecord serializes and deserializes."""
    r = StyleSignalRecord(
        pattern_type="export_pattern",
        value="v1_final",
        confidence=0.8,
        evidence_paths=["/p/export_v1_final.png"],
        session_id="s1",
        project_path="/p",
        description="Export with version and final",
    )
    d = r.model_dump()
    r2 = StyleSignalRecord.model_validate(d)
    assert r2.pattern_type == r.pattern_type and r2.value == r.value
