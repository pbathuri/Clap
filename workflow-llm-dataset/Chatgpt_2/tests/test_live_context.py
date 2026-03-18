"""
Tests for M32 live work context: models, fusion, session detection, state.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.live_context.models import (
    ActiveWorkContext,
    ActivityMode,
    FocusStateKind,
    FocusTarget,
    InferredProject,
    InferredTaskFamily,
    WorkMode,
    SourceContribution,
    SessionTransitionEvent,
    SessionTransitionKind,
    CONTEXT_STALE_SECONDS,
)
from workflow_dataset.live_context.fusion import fuse_active_context, _parse_project_from_file_event
from workflow_dataset.live_context.session_detector import detect_transitions
from workflow_dataset.live_context.state import (
    get_live_context_state,
    save_live_context_state,
    get_recent_transitions,
    append_transition,
    get_live_context_state_dir,
)
from workflow_dataset.observe.local_events import ObservationEvent, EventSource


def _make_file_event(
    path: str,
    project_hint: str | None = None,
    ts: str = "2025-01-01T12:00:00Z",
    extension: str | None = None,
) -> ObservationEvent:
    p = Path(path)
    payload = {"path": path, "filename": p.name, "event_kind": "snapshot", "is_dir": False}
    if project_hint:
        payload["project_hint"] = project_hint
    if extension is not None:
        payload["extension"] = extension
    elif p.suffix:
        payload["extension"] = p.suffix.lstrip(".").lower()
    return ObservationEvent(
        event_id="evt_test",
        source=EventSource.FILE,
        timestamp_utc=ts,
        payload=payload,
    )


def test_context_model_creation() -> None:
    ctx = ActiveWorkContext(
        context_id="ctx_1",
        timestamp_utc="2025-01-01T12:00:00Z",
        inferred_project=InferredProject(project_id="proj_a", label="proj_a", confidence=0.8, evidence=["file_events=10"]),
        work_mode=WorkMode.FOCUSED,
        overall_confidence=0.7,
        is_stale=False,
    )
    assert ctx.work_mode == WorkMode.FOCUSED
    assert ctx.inferred_project and ctx.inferred_project.label == "proj_a"


def test_fusion_from_events() -> None:
    root = Path("/workspace")
    events = [
        _make_file_event("/workspace/proj_a/file1.txt", ts="2025-01-01T12:00:00Z"),
        _make_file_event("/workspace/proj_a/file2.txt", ts="2025-01-01T12:01:00Z"),
        _make_file_event("/workspace/proj_b/other.txt", ts="2025-01-01T11:00:00Z"),
    ]
    ctx = fuse_active_context(events, root_paths=[root], max_events=10)
    assert ctx.inferred_project is not None
    assert ctx.inferred_project.label == "proj_a"
    assert ctx.work_mode in (WorkMode.FOCUSED, WorkMode.SWITCHING, WorkMode.UNKNOWN, WorkMode.IDLE)
    assert ctx.source_contributions
    file_contrib = next((c for c in ctx.source_contributions if c.source == "file"), None)
    assert file_contrib is not None and file_contrib.signals_count == 3


def test_fusion_conflicting_signals() -> None:
    """Two projects with similar counts -> lower confidence or switching."""
    root = Path("/workspace")
    events = [
        _make_file_event("/workspace/A/f.txt", ts="2025-01-01T12:00:00Z"),
        _make_file_event("/workspace/B/g.txt", ts="2025-01-01T12:01:00Z"),
        _make_file_event("/workspace/A/h.txt", ts="2025-01-01T12:02:00Z"),
    ]
    ctx = fuse_active_context(events, root_paths=[root], max_events=10)
    assert ctx.inferred_project is not None
    assert ctx.inferred_project.label in ("A", "B")
    assert ctx.work_mode in (WorkMode.SWITCHING, WorkMode.FOCUSED, WorkMode.UNKNOWN, WorkMode.IDLE)


def test_fusion_no_events() -> None:
    ctx = fuse_active_context([], max_events=10)
    assert ctx.inferred_project is None or ctx.inferred_project.label == ""
    assert ctx.work_mode == WorkMode.IDLE or ctx.is_stale


def test_parse_project_from_file_event() -> None:
    root = Path("/workspace")
    evt = _make_file_event("/workspace/my_proj/src/a.py")
    assert _parse_project_from_file_event(evt, [root]) == "my_proj"
    evt2 = _make_file_event("/other/path", project_hint="hint_proj")
    assert _parse_project_from_file_event(evt2, [root]) == "hint_proj"


def test_session_transition_detection() -> None:
    prev = ActiveWorkContext(
        context_id="ctx_0",
        timestamp_utc="2025-01-01T11:00:00Z",
        inferred_project=InferredProject(project_id="A", label="A", confidence=0.8, evidence=[]),
        work_mode=WorkMode.FOCUSED,
    )
    curr = ActiveWorkContext(
        context_id="ctx_1",
        timestamp_utc="2025-01-01T12:00:00Z",
        inferred_project=InferredProject(project_id="B", label="B", confidence=0.8, evidence=[]),
        work_mode=WorkMode.FOCUSED,
    )
    transitions = detect_transitions(curr, prev)
    kinds = [t.kind for t in transitions]
    assert SessionTransitionKind.PROJECT_SWITCH in kinds


def test_session_start_when_no_previous() -> None:
    curr = ActiveWorkContext(
        context_id="ctx_1",
        timestamp_utc="2025-01-01T12:00:00Z",
        inferred_project=InferredProject(project_id="P", label="P", confidence=0.7, evidence=[]),
    )
    transitions = detect_transitions(curr, None)
    assert any(t.kind == SessionTransitionKind.SESSION_START for t in transitions)


def test_stale_no_signal_behavior() -> None:
    ctx = fuse_active_context([], max_events=10)
    assert ctx.is_stale or ctx.work_mode == WorkMode.IDLE


def test_state_save_and_load(tmp_path: Path) -> None:
    ctx = ActiveWorkContext(
        context_id="ctx_save",
        timestamp_utc="2025-01-01T12:00:00Z",
        inferred_project=InferredProject(project_id="X", label="X", confidence=0.9, evidence=[]),
        work_mode=WorkMode.FOCUSED,
    )
    save_live_context_state(ctx, repo_root=tmp_path)
    loaded = get_live_context_state(repo_root=tmp_path)
    assert loaded is not None
    assert loaded.context_id == ctx.context_id
    assert loaded.inferred_project and loaded.inferred_project.label == "X"


def test_append_and_get_transitions(tmp_path: Path) -> None:
    t = SessionTransitionEvent(
        transition_id="tr_1",
        kind=SessionTransitionKind.PROJECT_SWITCH,
        timestamp_utc="2025-01-01T12:00:00Z",
        from_project="A",
        to_project="B",
        evidence=[],
        confidence=0.8,
    )
    append_transition(t, repo_root=tmp_path)
    recent = get_recent_transitions(repo_root=tmp_path, limit=5)
    assert len(recent) >= 1
    assert recent[0].kind == SessionTransitionKind.PROJECT_SWITCH
    assert recent[0].to_project == "B"


def test_confidence_evidence_output() -> None:
    events = [
        _make_file_event("/w/proj/x.txt", ts="2025-01-01T12:00:00Z"),
        _make_file_event("/w/proj/y.txt", ts="2025-01-01T12:01:00Z"),
    ]
    ctx = fuse_active_context(events, root_paths=[Path("/w")], max_events=10)
    assert ctx.overall_confidence >= 0
    assert ctx.evidence_summary
    assert any("project" in e.lower() or "work_mode" in e.lower() for e in ctx.evidence_summary)


def test_activity_mode_coding() -> None:
    """Coding mode inferred from .py/.ts file events."""
    events = [
        _make_file_event("/w/proj/main.py", extension="py", ts="2025-01-01T12:00:00Z"),
        _make_file_event("/w/proj/utils.py", extension="py", ts="2025-01-01T12:01:00Z"),
        _make_file_event("/w/proj/types.ts", extension="ts", ts="2025-01-01T12:02:00Z"),
    ]
    ctx = fuse_active_context(events, root_paths=[Path("/w")], max_events=10)
    assert ctx.activity_mode == ActivityMode.CODING
    assert ctx.activity_mode_reason
    assert "code" in ctx.activity_mode_reason.lower() or "coding" in ctx.activity_mode_reason.lower()


def test_activity_mode_writing() -> None:
    """Writing mode inferred from .md/.txt file events."""
    events = [
        _make_file_event("/w/proj/readme.md", extension="md", ts="2025-01-01T12:00:00Z"),
        _make_file_event("/w/proj/notes.txt", extension="txt", ts="2025-01-01T12:01:00Z"),
    ]
    ctx = fuse_active_context(events, root_paths=[Path("/w")], max_events=10)
    assert ctx.activity_mode == ActivityMode.WRITING
    assert ctx.activity_mode_reason
    assert "document" in ctx.activity_mode_reason.lower() or "writing" in ctx.activity_mode_reason.lower() or "prose" in ctx.activity_mode_reason.lower()


def test_focus_state_single_file() -> None:
    """Single file or two files in same dir -> single_file or multi_file_same_dir."""
    events = [
        _make_file_event("/w/proj/a.py", ts="2025-01-01T12:00:00Z"),
        _make_file_event("/w/proj/a.py", ts="2025-01-01T12:01:00Z"),
    ]
    ctx = fuse_active_context(events, root_paths=[Path("/w")], max_events=10)
    assert ctx.focus_state is not None
    assert ctx.focus_state.kind in (FocusStateKind.SINGLE_FILE, FocusStateKind.MULTI_FILE_SAME_DIR)
    assert ctx.focus_state_reason
    assert "single" in ctx.focus_state_reason.lower() or "same directory" in ctx.focus_state_reason.lower() or "one " in ctx.focus_state_reason.lower()


def test_focus_state_scattered() -> None:
    """Multiple dirs in different projects -> scattered or project_browse."""
    events = [
        _make_file_event("/w/proj_a/foo.py", ts="2025-01-01T12:00:00Z"),
        _make_file_event("/w/proj_b/bar.py", ts="2025-01-01T12:01:00Z"),
        _make_file_event("/w/proj_c/baz.py", ts="2025-01-01T12:02:00Z"),
    ]
    ctx = fuse_active_context(events, root_paths=[Path("/w")], max_events=10)
    assert ctx.focus_state is not None
    assert ctx.focus_state.kind in (FocusStateKind.SCATTERED, FocusStateKind.PROJECT_BROWSE, FocusStateKind.UNKNOWN)
    assert ctx.focus_state_reason


def test_activity_mode_and_focus_reason_present() -> None:
    """Fusion always sets activity_mode_reason and focus_state_reason when there are file events."""
    events = [
        _make_file_event("/w/p/x.md", ts="2025-01-01T12:00:00Z"),
    ]
    ctx = fuse_active_context(events, root_paths=[Path("/w")], max_events=10)
    assert ctx.activity_mode_reason or ctx.activity_mode == ActivityMode.UNKNOWN
    assert ctx.focus_state_reason
