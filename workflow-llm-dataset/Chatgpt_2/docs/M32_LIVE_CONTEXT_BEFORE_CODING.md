# M32A–M32D — Active Work Context Fusion + Live Session Detector: Before-Coding Analysis

## 1. What observation and personal-context pieces already exist

- **observe/**  
  - Event envelope: `ObservationEvent` (event_id, source, timestamp_utc, payload), `EventSource` (file, app, browser, terminal, calendar, teaching).  
  - Normalized view: `activity_type`, `project_hint`, `session_hint`, `redaction_marker`, `provenance` in payload / `normalized_view()`.  
  - `load_events()`, `load_all_events()` from event log (JSONL per day).  
  - File collector implemented; others stubs. Sources, boundaries, state, profiles, retention.

- **personal/**  
  - Work graph: `NodeType` (PROJECT, FOLDER, ROUTINE, FILE_REF, etc.), `PersonalWorkGraphNode`, ingest from file events, persist in SQLite.  
  - `graph_store`: `list_nodes(conn, node_type, limit)`, `get_node()`, `count_nodes()`, `list_edges()`.  
  - `routine_detector`: `detect_routines(events, root_paths)` → routine_type, label, project, touch_count, confidence, supporting_signals (frequent_folder, frequent_project, repeated_extensions_by_project, work_hours).

- **session/**  
  - `Session` model: session_id, value_pack_id, active_tasks, active_job_ids, state (open/closed/archived), created_at, updated_at.  
  - Storage, board, report, templates, cadence. No “current session from observation” fusion.

- **context/**  
  - `WorkState`: snapshot of jobs, intake, workspaces, approvals, copilot, task demos (product/ops focused).  
  - `build_work_state()`, snapshot save/load, drift, triggers. Not “what is the user doing right now?” from observation.

- **mission_control/**  
  - `observation_state`: enabled_sources, recent_events_count, next_recommended. No fused “active work context” or session transitions.

---

## 2. What is missing for a live active-work context detector

- **Explicit active-context model**: No single “current active work context” with inferred project, task family, work mode, focus target, confidence, evidence, source contributions.  
- **Fusion of observation + graph + session**: No component that takes recent observation events + graph projects/routines + session hints and produces a current context and ranked candidates.  
- **Session transition detection**: No session_start, project_switch, deep_work_continuation, interruption, return_to_work events or state.  
- **Live context state**: No persisted “last known context” and “recent transitions” for other layers to query.  
- **CLI and mission control**: No `live-context now`, `explain`, `recent`, `session-state`, or mission-control slice for current project/task/mode and evidence.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| **Create** | `src/workflow_dataset/live_context/__init__.py` — exports. |
| **Create** | `src/workflow_dataset/live_context/models.py` — ActiveWorkContext, FocusTarget, InferredProject, InferredTaskFamily, WorkMode, SourceContribution, SessionTransitionEvent, decay/stale. |
| **Create** | `src/workflow_dataset/live_context/fusion.py` — fuse recent events + graph/session priors → current context, ranked candidates, confidence, evidence. |
| **Create** | `src/workflow_dataset/live_context/session_detector.py` — first-draft session transition detection (start, project_switch, deep_work, interruption, return). |
| **Create** | `src/workflow_dataset/live_context/state.py` — read/write live context state (current context, recent transitions) under data/local/live_context. |
| **Modify** | `src/workflow_dataset/cli.py` — add `live_context_group` with commands: now, explain, recent, session-state. |
| **Modify** | `src/workflow_dataset/mission_control/state.py` — add `live_context_state` (current project/task/mode, confidence, recent shifts, next assist opportunity). |
| **Modify** | `src/workflow_dataset/mission_control/report.py` — add [Live context] section. |
| **Create** | `docs/M32_LIVE_CONTEXT.md` — model, fusion, session detection, CLI, samples, gaps. |
| **Create** | `tests/test_live_context.py` — context model, fusion, conflicting signals, session transitions, stale behavior, confidence output. |

---

## 4. Safety/risk note

- **Risk**: Live context could be used to infer sensitive activity or enable surveillance-style features.  
- **Mitigation**: (1) All inputs are already consent-bounded (observation sources, graph, session). (2) No new data collection; only fusion of existing local signals. (3) Output is explicit and inspectable (explain, evidence). (4) No cloud; state and transitions stay on-device. (5) No raw content—only metadata and inferred labels.  
- **Residual**: Heuristics (e.g. “project switch”) may be wrong; treat as advisory only.

---

## 5. Privacy / retention / consent guardrails

- **Inputs**: Only observation events and graph/session data that the user has already enabled (observation_enabled, allowed_sources, graph store).  
- **Retention**: Live context state and transition log follow same local retention as event log; no new exfiltration.  
- **Consent**: No new observation; fusion uses only data produced under existing observation and graph consent.  
- **Inspectability**: `live-context explain` and evidence fields make inferences auditable.

---

## 6. What this block will NOT do

- Will **not** add new observation collectors or new data collection.  
- Will **not** perform hidden or continuous background monitoring; fusion runs on demand or on explicit refresh.  
- Will **not** send context or transitions off-device.  
- Will **not** replace or rebuild observe, personal graph, or session systems; it consumes their outputs.  
- Will **not** auto-execute actions based on context; it only provides a queryable substrate for assist layers.
