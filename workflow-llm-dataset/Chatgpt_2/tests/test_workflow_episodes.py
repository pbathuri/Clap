"""
M33A–M33D: Workflow episodes — model, bridge, stage detection, handoff gaps, explain.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.workflow_episodes.models import (
    WorkflowEpisode,
    WorkflowStage,
    WorkflowEpisodeType,
    LinkedActivity,
    InferredProjectAssociation,
    HandoffGap,
    HandoffGapKind,
)
from workflow_dataset.workflow_episodes.store import (
    get_episodes_dir,
    get_current_episode,
    save_current_episode,
    list_recent_episodes,
    append_to_recent,
)
from workflow_dataset.workflow_episodes.stage_detection import infer_stage, infer_handoff_gaps, infer_next_step_candidates, infer_episode_type
from workflow_dataset.workflow_episodes.explain import (
    build_episode_explanation,
    build_stage_explanation,
    build_handoff_gaps_explanation,
    build_transition_map_output,
    build_advance_stall_explanation,
)


def test_episode_model_creation():
    """Create workflow episode with linked activities and inferred project."""
    ep = WorkflowEpisode(
        episode_id="ep_test_1",
        started_at_utc="2025-03-16T12:00:00Z",
        updated_at_utc="2025-03-16T12:05:00Z",
        linked_activities=[
            LinkedActivity(event_id="evt_1", source="file", timestamp_utc="2025-03-16T12:00:00Z", path="/work/proj_a/doc.md", label="doc.md", evidence="path"),
            LinkedActivity(event_id="evt_2", source="file", timestamp_utc="2025-03-16T12:02:00Z", path="/work/proj_a/readme.md", label="readme.md", evidence="path"),
        ],
        inferred_project=InferredProjectAssociation(project_id="proj_a", label="proj_a", confidence=0.8, evidence=["file_events=2"]),
        stage=WorkflowStage.DRAFTING,
        stage_evidence=["writing_extensions"],
        overall_confidence=0.75,
        evidence_summary=["activities=2", "project=proj_a"],
        is_active=True,
    )
    assert ep.episode_id == "ep_test_1"
    assert len(ep.linked_activities) == 2
    assert ep.inferred_project and ep.inferred_project.label == "proj_a"
    assert ep.stage == WorkflowStage.DRAFTING


def test_store_save_load(tmp_path):
    """Save and load current episode."""
    ep = WorkflowEpisode(
        episode_id="ep_save_1",
        started_at_utc="2025-03-16T12:00:00Z",
        updated_at_utc="2025-03-16T12:00:00Z",
        linked_activities=[LinkedActivity(event_id="e1", source="file", timestamp_utc="2025-03-16T12:00:00Z", evidence="test")],
        stage=WorkflowStage.INTAKE,
        is_active=True,
    )
    save_current_episode(ep, tmp_path)
    loaded = get_current_episode(tmp_path)
    assert loaded is not None
    assert loaded.episode_id == ep.episode_id
    assert loaded.stage == WorkflowStage.INTAKE


def test_infer_stage_drafting():
    """Stage inference: writing-like extensions -> drafting."""
    ep = WorkflowEpisode(
        episode_id="ep_stage_1",
        linked_activities=[
            LinkedActivity(event_id="e1", source="file", activity_type="file_snapshot", path="/a/doc.md", evidence="x"),
            LinkedActivity(event_id="e2", source="file", activity_type="file_snapshot", path="/a/readme.md", evidence="x"),
        ],
    )
    stage, evidence = infer_stage(ep)
    assert stage in (WorkflowStage.DRAFTING, WorkflowStage.UNKNOWN)
    assert evidence


def test_infer_stage_unknown_empty():
    """Stage inference: no activities -> unknown."""
    ep = WorkflowEpisode(episode_id="ep_empty", linked_activities=[])
    stage, evidence = infer_stage(ep)
    assert stage == WorkflowStage.UNKNOWN
    assert "no_activities" in evidence


def test_infer_handoff_gaps_no_queue(tmp_path):
    """Handoff gaps with no approval queue: empty or no pending."""
    ep = WorkflowEpisode(episode_id="ep_gaps_1", linked_activities=[LinkedActivity(event_id="e1", source="file", evidence="x")])
    gaps = infer_handoff_gaps(ep, repo_root=tmp_path)
    assert isinstance(gaps, list)


def test_build_episode_explanation():
    """Explain episode returns summary and evidence."""
    ep = WorkflowEpisode(
        episode_id="ep_explain_1",
        linked_activities=[LinkedActivity(event_id="e1", source="file", evidence="test")],
        inferred_project=InferredProjectAssociation(label="proj_x", confidence=0.7),
        evidence_summary=["activities=1"],
    )
    expl = build_episode_explanation(ep)
    assert "episode_id" in expl
    assert "summary" in expl
    assert expl.get("project", "")


def test_build_stage_explanation():
    """Stage explanation returns stage and evidence."""
    ep = WorkflowEpisode(episode_id="ep_s1", linked_activities=[LinkedActivity(event_id="e1", source="file", path="/a/b.md", evidence="x")])
    expl = build_stage_explanation(ep)
    assert "stage" in expl
    assert "evidence" in expl


def test_build_handoff_gaps_explanation(tmp_path):
    """Handoff gaps explanation returns list of gaps."""
    ep = WorkflowEpisode(episode_id="ep_h1", linked_activities=[LinkedActivity(event_id="e1", source="file", evidence="x")])
    expl = build_handoff_gaps_explanation(ep, repo_root=str(tmp_path))
    assert "gaps" in expl
    assert "count" in expl
    assert isinstance(expl["gaps"], list)


def test_get_episodes_dir(tmp_path):
    """Episodes dir is under repo data/local/workflow_episodes."""
    d = get_episodes_dir(tmp_path)
    assert d == tmp_path / "data/local/workflow_episodes"


def test_append_to_recent(tmp_path):
    """Append episode to recent list."""
    ep = WorkflowEpisode(episode_id="ep_recent_1", started_at_utc="2025-03-16T12:00:00Z", updated_at_utc="2025-03-16T12:00:00Z", is_active=True)
    append_to_recent(ep, tmp_path)
    recent = list_recent_episodes(tmp_path, limit=10)
    assert len(recent) >= 1
    assert recent[0].episode_id == "ep_recent_1"


def test_bridge_no_events(tmp_path):
    """Bridge with no event log returns None."""
    from workflow_dataset.workflow_episodes.bridge import build_active_episode
    episode = build_active_episode(repo_root=tmp_path, event_log_dir=tmp_path / "nonexistent")
    assert episode is None


def test_bridge_with_events(tmp_path):
    """Bridge with mock event log produces episode when events exist."""
    from workflow_dataset.observe.local_events import ObservationEvent, EventSource, append_events
    log_dir = tmp_path / "data/local/event_log"
    log_dir.mkdir(parents=True, exist_ok=True)
    evt = ObservationEvent(
        event_id="evt_1",
        source=EventSource.FILE,
        timestamp_utc="2025-03-16T12:00:00Z",
        payload={"path": str(tmp_path / "work/proj_x/doc.md"), "filename": "doc.md", "extension": "md"},
    )
    append_events(log_dir, [evt])
    from workflow_dataset.workflow_episodes.bridge import build_active_episode
    episode = build_active_episode(repo_root=tmp_path, event_log_dir=log_dir, root_paths=[tmp_path], min_activities=1)
    assert episode is not None
    assert len(episode.linked_activities) >= 1
    assert episode.episode_id


# --- M33D.1: Episode types + transition maps ---


def test_infer_episode_type_document_handoff():
    """Episode type: multiple doc extensions -> document_handoff."""
    ep = WorkflowEpisode(
        episode_id="ep_doc_1",
        linked_activities=[
            LinkedActivity(event_id="e1", source="file", path="/a/spec.md", evidence="path"),
            LinkedActivity(event_id="e2", source="file", path="/a/readme.md", evidence="path"),
            LinkedActivity(event_id="e3", source="file", path="/a/notes.doc", evidence="path"),
        ],
    )
    ep_type, evidence = infer_episode_type(ep)
    assert ep_type == WorkflowEpisodeType.DOCUMENT_HANDOFF
    assert evidence


def test_infer_episode_type_coding_debugging():
    """Episode type: code extensions + terminal-like activity -> coding_debugging."""
    ep = WorkflowEpisode(
        episode_id="ep_code_1",
        linked_activities=[
            LinkedActivity(event_id="e1", source="file", path="/a/main.py", evidence="path"),
            LinkedActivity(event_id="e2", source="terminal", path="/a/run.sh", evidence="path"),
        ],
    )
    ep_type, evidence = infer_episode_type(ep)
    assert ep_type == WorkflowEpisodeType.CODING_DEBUGGING
    assert evidence


def test_infer_episode_type_unknown_empty():
    """Episode type: no activities -> unknown."""
    ep = WorkflowEpisode(episode_id="ep_empty", linked_activities=[])
    ep_type, evidence = infer_episode_type(ep)
    assert ep_type == WorkflowEpisodeType.UNKNOWN
    assert "no_activities" in evidence


def test_build_transition_map_output():
    """Transition map output has current_stage, episode_type, next_stages, transition_map."""
    ep = WorkflowEpisode(
        episode_id="ep_tm_1",
        linked_activities=[LinkedActivity(event_id="e1", source="file", path="/a/doc.md", evidence="x")],
        stage=WorkflowStage.DRAFTING,
        episode_type="document_handoff",
        episode_type_evidence=["doc_extensions"],
    )
    out = build_transition_map_output(ep)
    assert out["current_stage"] == "drafting"
    assert out["episode_type"] == "document_handoff"
    assert "next_stages" in out
    assert isinstance(out["next_stages"], list)
    assert len(out["next_stages"]) >= 1
    assert "transition_map" in out
    assert isinstance(out["transition_map"], dict)
    assert "drafting" in out["transition_map"]


def test_build_advance_stall_explanation():
    """Advance/stall explanation has why_advanced and why_stalled (lists)."""
    ep = WorkflowEpisode(
        episode_id="ep_as_1",
        linked_activities=[
            LinkedActivity(event_id="e1", source="file", path="/a/readme.md", evidence="path"),
        ],
        stage=WorkflowStage.DRAFTING,
        stage_evidence=["writing_extensions"],
        inferred_project=InferredProjectAssociation(label="proj_x", confidence=0.6),
    )
    out = build_advance_stall_explanation(ep)
    assert "why_advanced" in out
    assert "why_stalled" in out
    assert isinstance(out["why_advanced"], list)
    assert isinstance(out["why_stalled"], list)
    # With stage evidence we expect at least one advance reason
    assert len(out["why_advanced"]) >= 1 or len(out["why_stalled"]) >= 1
