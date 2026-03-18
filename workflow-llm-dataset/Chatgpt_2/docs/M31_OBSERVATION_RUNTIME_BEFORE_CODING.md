# M31A–M31D — Local Observation Runtime: Before-Coding Analysis

## 1. What observation-related code already exists

- **observe/**  
  - `local_events.py`: `ObservationEvent` (event_id, source, timestamp_utc, device_id, tier, payload), `EventSource` enum (file, app, browser, terminal, calendar, teaching), `create_event_id`, `append_events`, `load_events`, `load_all_events` (JSONL per day).  
  - `file_activity.py`: `collect_file_events` (metadata-only scan), `file_snapshot_payload`; no file content.  
  - `app_activity.py`, `browser_activity.py`, `terminal_activity.py`, `calendar_metadata.py`: payload builders + `collect_*` stubs returning `[]` (no real OS integrations).  
  - `__init__.py`: exports `ObservationEvent`, `EventSource`.

- **Settings**  
  - `AgentSettings`: `observation_enabled`, `observation_tier`, `allowed_observation_sources`, `file_observer` (FileObserverSettings: root_paths, max_files_per_scan, exclude_dirs, allowed_extensions, graph_update_enabled).  
  - `PathSettings`: `event_log_dir`, `graph_store_path`.

- **CLI**  
  - Single top-level `observe` command: requires `agent.observation_enabled` and `"file" in agent.allowed_observation_sources`; runs file scan, appends to event log, optionally updates personal graph.

- **Tests**  
  - `tests/test_observe_m1.py`: file metadata-only, event log write/load, personal graph ingest, CLI gating (observation_enabled / allowed_observation_sources).

- **Docs**  
  - `docs/OBSERVATION_PHASES.md`, `docs/schemas/LOCAL_OBSERVATION_EVENTS.md`, `docs/CAPABILITY_RUNTIME_BOUNDARIES.md`, `docs/ARCHITECTURE_OVERVIEW.md`, `docs/EDGE_DEVICE_PLAN.md`.

---

## 2. What is missing for a first-draft observation runtime

- **Explicit source model**: No per-source definition of allowed scope, consent requirement, collection mode, redaction rules, retention expectations, trust notes.  
- **Normalized event shape**: No coarse `activity_type`, project/session hint, redaction/sensitivity marker, or provenance in the stream.  
- **Consent/boundary enforcement**: No first-class “enabled/disabled per source”, allowed scopes/paths/apps, observe-only vs richer mode, retention boundaries, or source health/blocked state.  
- **CLI surface**: No `observe sources`, `observe enable --source X`, `observe status`, `observe recent`, `observe boundaries`, `observe health`.  
- **Mission control**: No observation slice (enabled sources, blocked/unhealthy, activity counts, consent posture, next recommended action).

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| **Create** | `src/workflow_dataset/observe/sources.py` — source registry and per-source model (scope, consent, mode, redaction, retention, trust). |
| **Create** | `src/workflow_dataset/observe/boundaries.py` — consent/boundary state, enable/disable per source, scope checks, retention, source health/blocked. |
| **Modify** | `src/workflow_dataset/observe/local_events.py` — add optional normalized fields: activity_type, project_hint, session_hint, redaction_marker, provenance (in payload or as optional fields). |
| **Create** | `src/workflow_dataset/observe/runtime.py` — run collection respecting boundaries; dispatch to existing collectors. |
| **Modify** | `src/workflow_dataset/cli.py` — add `observe_group` with commands: sources, enable, status, recent, boundaries, health; move current `observe` to `observe run` (or keep as alias). |
| **Modify** | `src/workflow_dataset/mission_control/state.py` — add `observation_state` (enabled sources, blocked, recent counts, consent posture). |
| **Modify** | `src/workflow_dataset/mission_control/report.py` — add observation section; `recommend_next_action` may consider observation. |
| **Modify** | `src/workflow_dataset/observe/__init__.py` — export new public types from sources/boundaries. |
| **Create** | `docs/M31_OBSERVATION_RUNTIME.md` — first-draft observation runtime: sources, stream, boundaries, CLI, mission control. |
| **Create** | `tests/test_observe_m31.py` — source registration, enable/disable, boundary enforcement, event normalization, blocked source, redaction/retention signaling. |

---

## 4. Safety/risk note

- **Risk**: Observation could be misused to capture sensitive data or bypass user intent.  
- **Mitigation**: (1) All collection gated by `observation_enabled` and per-source allow-list. (2) No raw content in file events; metadata only. (3) Source definitions and boundaries are explicit and inspectable. (4) Data stays local; no exfiltration. (5) Retention and redaction are part of the source model and boundary checks.  
- **Residual**: Real app/browser/terminal/calendar collectors are still stubs; when implemented later, they must adhere to the same consent and redaction rules defined in the source model.

---

## 5. Explicit privacy/consent boundaries

- **Global**: Observation is off unless `agent.observation_enabled` is true.  
- **Per-source**: A source collects only if it is in `agent.allowed_observation_sources` and not blocked (e.g. scope violation or health failure).  
- **Scope**: File observer limited to `file_observer.root_paths` and exclusions; other sources have allowed_scopes (paths/apps/domains) defined in the source model and enforced in boundaries.  
- **Modes**: “observe_only” (minimal metadata) vs “rich_metadata” (e.g. domain vs full URL); default observe_only.  
- **Retention**: Per-source retention_days or max_events; enforced when writing or rotating logs.  
- **Redaction**: Sources that may contain sensitive data (terminal, browser URL) have redaction rules; events can carry a redaction_marker.  
- **No cloud**: Event stream and boundaries are local-only; no telemetry or cloud upload in this block.

---

## 6. What this block will NOT do

- Will **not** implement real OS/browser/terminal/calendar collectors (only file has a real collector; others remain stubs).  
- Will **not** add hidden or automatic background exfiltration.  
- Will **not** capture raw file content, page body, or form data.  
- Will **not** change trust/approval flows for execution; observation remains separate from action approval.  
- Will **not** add cloud sync or telemetry; all data remains on-device and inspectable.
