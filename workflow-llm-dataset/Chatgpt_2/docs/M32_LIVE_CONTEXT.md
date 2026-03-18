# M32 — Active Work Context Fusion + Live Session Detector

First-draft live work context layer: fuses bounded observation + personal graph + session into “what is the user doing right now?”, with session transition detection and inspectable evidence.

## Purpose

- **Fuse** observation events, graph projects/routines, and session hints into a single **active work context** (inferred project, task family, work mode, focus, confidence, evidence).
- **Detect** session transitions: session start, project switch, deep-work continuation, interruption, return-to-work.
- **Persist** current context and recent transitions so assist layers and mission control can query them.
- **Stay local**: no new data collection; only fusion of existing consent-bounded signals.

## Models (Phase A)

- **ActiveWorkContext**: context_id, timestamp_utc, focus_target, inferred_project, inferred_task_family, work_mode, overall_confidence, evidence_summary, source_contributions, is_stale, last_signal_utc, session_hint, project_hint.
- **FocusTarget**: kind (path | app | domain | task_label), value, display_name.
- **InferredProject** / **InferredTaskFamily**: id, label, confidence, evidence.
- **WorkMode**: unknown, focused, switching, interrupted, returning, idle.
- **SourceContribution**: source, weight, evidence_summary, signals_count.
- **SessionTransitionEvent**: transition_id, kind, timestamp_utc, from_project, to_project, evidence, confidence.
- **SessionTransitionKind**: session_start, project_switch, deep_work_continuation, interruption, return_to_work.
- **Context decay**: context considered stale if no signal within `CONTEXT_STALE_SECONDS` (15 min).

## Fusion (Phase B)

- **Inputs**: recent observation events (e.g. last 200), optional root_paths, optional graph projects/routines, optional session_hint/project_hint.
- **Logic**: project from file events (path under root or payload project_hint); rank by count; best project + confidence; task family from graph routine match; work_mode from project distribution and recency; source contributions from file/graph/session.
- **Output**: ActiveWorkContext (and optionally ranked candidates in future).

## Session detection (Phase C)

- **session_start**: no previous context and current has project/focus.
- **project_switch**: previous and current project differ.
- **deep_work_continuation**: same project, work_mode focused.
- **interruption**: previous focused, current switching or idle.
- **return_to_work**: previous idle/unknown, current has project and focused/switching.

## CLI (Phase D)

- `workflow-dataset live-context now` — compute context, persist, detect transitions, print summary.
- `workflow-dataset live-context explain` — full evidence and source contributions.
- `workflow-dataset live-context recent [--limit N]` — recent session transitions.
- `workflow-dataset live-context session-state` — current persisted context and recent transitions.

## Mission control

- **live_context_state**: current_project, current_task_family, current_work_mode, confidence, is_stale, recent_transitions_count, recent_transition_kinds, next_assist_opportunity.
- Report section: `[Live context] project=… task=… mode=… confidence=… stale=… transitions=… next: …`

## Sample active-context record

```json
{
  "context_id": "ctx_abc123",
  "timestamp_utc": "2025-03-16T14:00:00Z",
  "focus_target": { "kind": "path", "value": "/work/proj_x/doc.md", "display_name": "doc.md" },
  "inferred_project": { "project_id": "proj_x", "label": "proj_x", "confidence": 0.75, "evidence": ["file_events=12", "total_file_events=15"] },
  "inferred_task_family": null,
  "work_mode": "focused",
  "overall_confidence": 0.6,
  "evidence_summary": ["projects_ranked=['proj_x', 'proj_y']", "work_mode=focused"],
  "source_contributions": [{ "source": "file", "weight": 0.24, "evidence_summary": "12 file events", "signals_count": 12 }],
  "is_stale": false,
  "last_signal_utc": "2025-03-16T13:58:00Z",
  "session_hint": "",
  "project_hint": ""
}
```

## Sample context explanation output

From `live-context explain`:

- **context_id**, **timestamp_utc**
- **inferred_project**: full dict (project_id, label, confidence, evidence)
- **inferred_task_family**: full dict or null
- **work_mode**, **overall_confidence**
- **is_stale**, **last_signal_utc**
- **evidence_summary**: list of strings
- **source_contributions**: per source (file, graph, session) with weight and evidence_summary

## Sample session-transition output

From `live-context recent`:

- Each line: `timestamp_utc  kind  from=…  to=…`
- Example: `2025-03-16T14:00:00Z  project_switch  from=proj_a  to=proj_b`

## Tests

Run: `pytest workflow-llm-dataset/tests/test_live_context.py -v`

Covers: context model creation, fusion from events, conflicting signals, no events, parse project from file event, session transition detection, session start when no previous, stale/no-signal behavior, state save/load, append/get transitions, confidence/evidence output.

## Remaining gaps (later refinement)

- **Ranked candidate contexts**: return multiple (project, task) candidates with scores.
- **App/browser/terminal** signals in fusion when those collectors exist.
- **Time-window tuning**: configurable staleness and window size.
- **Session layer integration**: pass current session id and project from session store into fusion.
- **Explain per-source**: more granular evidence (e.g. which file paths contributed to project).
