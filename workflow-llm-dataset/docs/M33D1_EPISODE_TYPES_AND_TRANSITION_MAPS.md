# M33D.1 — Workflow Episode Types + Transition Maps

First-draft support for workflow episode types, transition maps between stages, and clearer advance/stall explanations.

## 1. Files modified

- `src/workflow_dataset/cli.py` — In `workflow-episodes now`: call `infer_episode_type`, set `episode.episode_type` and `episode.episode_type_evidence`; new command `workflow-episodes transition-map`; `workflow-episodes stage` extended with episode type and advance/stall in JSON and human output.
- `src/workflow_dataset/workflow_episodes/__init__.py` — Exports: `WorkflowEpisodeType`, `infer_episode_type`, `build_transition_map_output`, `build_advance_stall_explanation`, `get_transition_map`.
- `tests/test_workflow_episodes.py` — Tests for episode type inference, transition map output, advance/stall explanation.

## 2. Files created

- `src/workflow_dataset/workflow_episodes/transition_map.py` — `STAGE_TRANSITIONS`, `get_transition_map`, `get_next_stages`, `get_advance_reasons`, `get_stall_reasons`, `build_transition_map_output`, `build_advance_stall_explanation`.
- `docs/M33D1_EPISODE_TYPES_AND_TRANSITION_MAPS.md` — This document.

(Models and stage_detection/explain changes were done in the prior step; see conversation summary.)

## 3. Sample workflow episode type

Example: **document_handoff** — multiple document files (e.g. spec, readme, notes) indicate handoff or collaboration on docs.

```json
{
  "episode_type": "document_handoff",
  "episode_type_evidence": ["doc_extensions=3"],
  "episode_id": "ep_doc_1",
  "stage": "drafting",
  "linked_activities": [
    {"path": "/a/spec.md", "source": "file"},
    {"path": "/a/readme.md", "source": "file"},
    {"path": "/a/notes.doc", "source": "file"}
  ]
}
```

Episode types supported: `unknown`, `document_handoff`, `approval_cycle`, `research_synthesis`, `coding_debugging`, `meeting_followup`.

## 4. Sample transition-map output

From `workflow-episodes transition-map --json` (or `build_transition_map_output(episode)`):

```json
{
  "current_stage": "drafting",
  "episode_type": "document_handoff",
  "next_stages": [
    {"to_stage": "review", "description": "Send for review or self-review"},
    {"to_stage": "execution_followup", "description": "Run or test (e.g. terminal)"}
  ],
  "transition_map": {
    "unknown": [
      {"to_stage": "intake", "description": "Start gathering or discovery"},
      {"to_stage": "drafting", "description": "Start creating or editing"}
    ],
    "intake": [
      {"to_stage": "drafting", "description": "Move to creating/editing"},
      {"to_stage": "review", "description": "Move to reviewing gathered material"}
    ],
    "drafting": [
      {"to_stage": "review", "description": "Send for review or self-review"},
      {"to_stage": "execution_followup", "description": "Run or test (e.g. terminal)"}
    ],
    "review": [
      {"to_stage": "approval_decision", "description": "Request or give approval"},
      {"to_stage": "drafting", "description": "Return to editing after feedback"}
    ],
    "approval_decision": [
      {"to_stage": "handoff_wrapup", "description": "Complete and hand off"},
      {"to_stage": "execution_followup", "description": "Execute after approval"}
    ],
    "execution_followup": [
      {"to_stage": "handoff_wrapup", "description": "Wrap up and hand off"},
      {"to_stage": "drafting", "description": "Return to edit after run"}
    ],
    "handoff_wrapup": [
      {"to_stage": "intake", "description": "Start next workflow"}
    ]
  },
  "advance_stall": {
    "why_advanced": [
      "Current stage 'drafting' inferred from: writing_extensions, path_extensions.",
      "Project context: proj_x (confidence 0.60)."
    ],
    "why_stalled": []
  }
}
```

## 5. Exact tests run

From repo root (e.g. `workflow-llm-dataset/`):

```bash
pytest tests/test_workflow_episodes.py -v
```

Test names added for M33D.1:

- `test_infer_episode_type_document_handoff` — Episode type: multiple doc extensions → document_handoff.
- `test_infer_episode_type_coding_debugging` — Episode type: code extensions + terminal → coding_debugging.
- `test_infer_episode_type_unknown_empty` — Episode type: no activities → unknown.
- `test_build_transition_map_output` — Transition map output has current_stage, episode_type, next_stages, transition_map.
- `test_build_advance_stall_explanation` — Advance/stall explanation has why_advanced and why_stalled (lists).

Full suite:

```bash
cd workflow-llm-dataset && pytest tests/test_workflow_episodes.py -v
```

## 6. Next recommended step for the pane

- **Integrate transition map into the UI**: surface “Current stage”, “Episode type”, “Next stages”, and “Why advanced / Why stalled” in the workflow-episodes pane (e.g. after “stage” or “explain”), so users see why the system thinks the workflow has advanced or stalled without running CLI.
- **Optional**: persist `advance_stall` (or a summary) with the episode so the pane can show it from stored state.
- **Optional**: add one more episode type (e.g. “planning” or “retrospective”) and a test if product needs it.
