# M33A–M33D Deliverable — Workflow Episode Tracker + Cross-App Context Bridge

## 1. Files modified

- `src/workflow_dataset/cli.py` — Added `workflow_episodes_group` and commands: `workflow-episodes now`, `recent`, `explain`, `stage`.
- `src/workflow_dataset/mission_control/state.py` — Added `workflow_episodes` slice (current episode, stage, handoff gaps, recent transitions).
- `src/workflow_dataset/mission_control/report.py` — Added `[Workflow episodes]` section.

## 2. Files created

- `src/workflow_dataset/workflow_episodes/__init__.py` — Package exports.
- `src/workflow_dataset/workflow_episodes/models.py` — WorkflowEpisode, WorkflowStage, LinkedActivity, InferredProjectAssociation, CurrentTaskHypothesis, HandoffGap, HandoffGapKind, NextStepCandidate, EpisodeTransitionEvent, EpisodeCloseReason.
- `src/workflow_dataset/workflow_episodes/store.py` — get_episodes_dir, get_current_episode, save_current_episode, list_recent_episodes, append_to_recent, append_episode_transition, load_recent_transitions.
- `src/workflow_dataset/workflow_episodes/bridge.py` — build_active_episode (from observe events + optional live context).
- `src/workflow_dataset/workflow_episodes/stage_detection.py` — infer_stage, infer_handoff_gaps, infer_next_step_candidates.
- `src/workflow_dataset/workflow_episodes/explain.py` — build_episode_explanation, build_stage_explanation, build_handoff_gaps_explanation.
- `tests/test_workflow_episodes.py` — Episode model, store save/load, infer_stage, explain, handoff_gaps, bridge (no events / with mock events).
- `docs/M33A_M33D_WORKFLOW_EPISODES_BEFORE_CODING.md` — Before-coding analysis.
- `docs/M33A_M33D_WORKFLOW_EPISODES.md` — Overview, model, bridge, stage, CLI, mission control, privacy.
- `docs/M33A_M33D_DELIVERABLE.md` — This file.

## 3. Exact CLI usage

```bash
# Build and show current workflow episode (from recent events)
workflow-dataset workflow-episodes now
workflow-dataset workflow-episodes now --json

# List recent episodes
workflow-dataset workflow-episodes recent
workflow-dataset workflow-episodes recent --limit 20 --json

# Explain current or specified episode
workflow-dataset workflow-episodes explain --latest
workflow-dataset workflow-episodes explain --id ep_abc123 --json

# Show stage and handoff gaps for current or specified episode
workflow-dataset workflow-episodes stage --latest
workflow-dataset workflow-episodes stage --id ep_abc123 --json

# Override repo root
workflow-dataset workflow-episodes now --repo-root /path/to/repo
```

## 4. Sample workflow episode record

```json
{
  "episode_id": "ep_abc123",
  "started_at_utc": "2025-03-16T12:00:00Z",
  "updated_at_utc": "2025-03-16T12:10:00Z",
  "linked_activities": [
    {
      "event_id": "evt_1",
      "source": "file",
      "timestamp_utc": "2025-03-16T12:00:00Z",
      "activity_type": "file_snapshot",
      "path": "/work/proj_x/doc.md",
      "label": "doc.md",
      "evidence": "source=file project_hint=proj_x"
    }
  ],
  "inferred_project": {
    "project_id": "proj_x",
    "label": "proj_x",
    "confidence": 0.85,
    "evidence": ["file_events=5", "total=6", "live_context_hint=proj_x"]
  },
  "stage": "drafting",
  "stage_evidence": ["writing_extensions=3", "file_events"],
  "handoff_gaps": [],
  "next_step_candidates": [
    {"label": "Run or test in terminal", "context": "terminal", "confidence": 0.5, "evidence": ["stage=drafting", "no_terminal_activity_yet"]}
  ],
  "overall_confidence": 0.85,
  "evidence_summary": ["activities=5", "project=proj_x", "project_confidence=0.85"],
  "is_active": true,
  "closed_at_utc": "",
  "close_reason": ""
}
```

## 5. Sample stage explanation output

```json
{
  "stage": "drafting",
  "evidence": ["writing_extensions=3", "file_events"],
  "summary": "Current workflow stage: drafting. Evidence: writing_extensions=3, file_events"
}
```

## 6. Sample missing-handoff output

```json
{
  "gaps": [
    {
      "kind": "missing_approval",
      "summary": "Pending items in approval queue; review or approve to continue.",
      "evidence": ["pending_count=2"],
      "suggested_action": "workflow-dataset review-studio inbox or agent-loop status"
    }
  ],
  "count": 1
}
```

## 7. Exact tests run

```bash
cd workflow-llm-dataset
pip install -e .
python3 -m pytest tests/test_workflow_episodes.py -v --tb=short
```

Tests: test_episode_model_creation, test_store_save_load, test_infer_stage_drafting, test_infer_stage_unknown_empty, test_infer_handoff_gaps_no_queue, test_build_episode_explanation, test_build_stage_explanation, test_build_handoff_gaps_explanation, test_get_episodes_dir, test_append_to_recent, test_bridge_no_events, test_bridge_with_events. (Requires pydantic and project deps.)

## 8. Exact remaining gaps for later refinement

- **App/browser/terminal events**: Bridge currently uses file events; when observe has real app/browser/terminal collectors, extend bridge to include them in linked_activities and evidence.
- **Episode lifecycle**: Transition events (episode_start, stage_change, episode_close) are modeled but not yet appended in CLI; add append_episode_transition when stage changes or episode closes.
- **Stale / no-episode**: Explicitly close episode when no signals for N minutes or single isolated action; persist close_reason.
- **Conflicting signals**: When events point to multiple projects, candidate_episode_associations (multiple candidates with evidence) not yet returned; currently single best project.
- **Missing-artifact heuristic**: Handoff gap “missing_artifact” not yet inferred (e.g. drafting with no recent save); only missing_approval from queue is implemented.
- **Time-window filtering**: Bridge uses all loaded events up to max_events; could restrict to last N minutes for “current” episode.
- **Mission control order**: workflow_episodes block runs after action_cards; order is fixed in state/report.
