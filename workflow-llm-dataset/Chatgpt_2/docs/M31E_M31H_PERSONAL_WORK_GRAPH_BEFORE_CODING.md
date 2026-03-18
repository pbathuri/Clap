# M31E–M31H Personal Work Graph Builder + Routine Mining — Before Coding

## 1. What personal/work-graph-like logic already exists

- **personal/work_graph.py**: `NodeType` enum (USER_PROFILE, PROJECT, FOLDER, RECURRING_TASK, FILE_REF, TOOL_APP, ROUTINE, WORKFLOW_CHAIN, PREFERENCE, PAIN_POINT, GOAL, APPROVAL_BOUNDARY, artifact/style/apply/generation node types, etc.), `PersonalWorkGraphNode` (node_id, node_type, label, attributes, source, created_utc, updated_utc, confidence). `ingest_file_events(store_path, events, root_paths)` creates FILE_REF/FOLDER/PROJECT nodes and file_in_folder / file_in_project edges from **file** events only. `persist_routines(store_path, routines)` writes ROUTINE nodes and routine_in_project edges. `add_node` / `get_node` delegate to graph_store.
- **personal/graph_store.py**: SQLite-backed `nodes` (node_id, node_type, label, attributes, source, created_utc, updated_utc, confidence) and `edges` (from_id, to_id, relation_type). `init_store`, `add_node`, `get_node`, `add_edge`, `count_nodes`, `count_edges`, `list_nodes`, `save_suggestion`, `list_suggestions`. No `list_edges` or list-by-relation.
- **personal/routine_detector.py**: File-only. `detect_routines(events, root_paths, ...)` returns list of routine dicts: frequent_folder, frequent_project, repeated_extensions_by_project, work_period_by_hour, path_cluster. Each has routine_type, label, touch_count, path/project, extensions, hours, confidence, supporting_signals.
- **observe/local_events.py**: `ObservationEvent` (event_id, source, timestamp_utc, device_id, tier, payload), `EventSource` (FILE, APP, BROWSER, TERMINAL, CALENDAR, TEACHING). `append_events`, `load_events`, `load_all_events`.
- **observe/file_activity.py**: `collect_file_events(...)` produces file snapshot events; payload has path, filename, extension, is_dir, etc.
- **project_case**: Project/Goal models and store (data/local/project_case); separate from graph.
- **session**: Session model and storage (data/local/session); session_id, value_pack_id, active_tasks, active_job_ids, active_routine_ids, etc.
- **outcomes**: SessionOutcome, TaskOutcome, repeated_block_patterns, repeated_success_patterns (outcome-history-based).
- **mission_control/state.py**: Aggregates product, evaluation, development, incubator, copilot (routines_count from copilot/routines = YAML job bundles), daily inbox, trust; **no** personal graph or inferred-routine summary yet.
- **CLI**: `observe` → collect_file_events, append_events, ingest_file_events; `suggest` → load_all_events (file), detect_routines, persist_routines, generate_suggestions. No dedicated `personal graph` or `personal routines`/`personal patterns` commands.
- **docs/schemas/PERSONAL_WORK_GRAPH.md**: Describes entities (user profile, projects, recurring tasks, files, tools, collaborators, routines, workflow chains, time patterns, preferences, pain points, goals, approval boundaries), fields (IDs, timestamps, source, confidence), relationships as edges.

## 2. What is missing for a real personal work graph builder

- **Explicit graph models** for: person/work profile node (single “me” node or attributes on USER_PROFILE), **artifact pattern** node (repeated file/doc pattern), **app/tool usage** node (TOOL_APP exists but no ingestion from app events), **dependency/sequence edge** (e.g. precedes, uses_tool, produces_artifact), **confidence/evidence** on edges and in attributes, **source-event provenance** (event_id or event_id list in attributes).
- **Event-to-graph ingestion** beyond file: consume **normalized** events (all sources); map to existing graph entities (project, session, pack) where possible; create/update TOOL_APP from app events; create artifact_pattern nodes from repeated file flows; record provenance (event_ids) and confidence.
- **Routine/pattern mining** beyond file heuristics: **task sequences** (order of jobs/routines/macros in sessions), **app/tool transitions** (A→B within session/time window), **file/document flows** (create/edit path patterns), **session patterns** (repeated session shapes), **repeated approvals/blockers** (from outcomes), **repeated artifact creation paths**. Bounded and explainable (min counts, confidence thresholds).
- **Graph query/explain**: `list_edges` / list edges by from_id or relation_type; **explain node** (why this routine/pattern exists: which events, confidence, supporting_signals).
- **CLI**: `workflow-dataset personal graph status`, `personal graph ingest --source recent`, `personal routines`, `personal patterns`, `personal graph explain --node <id>`.
- **Mission control**: Add block for **personal graph summary**: recently learned routines, strongest repeated patterns, inferred project/work associations, weak/uncertain patterns needing operator confirmation.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/personal/graph_models.py` — Explicit node/edge/provenance models (profile, project, routine, artifact_pattern, tool_app, dependency/sequence edge, confidence, source_event_ids). Extend or reference existing NodeType/PersonalWorkGraphNode where possible. |
| Create | `src/workflow_dataset/personal/graph_builder.py` — Event-to-graph ingestion: load normalized events (observe), map to projects/sessions where possible, create/update nodes (file_ref, folder, project, tool_app, routine, artifact_pattern) and edges (file_in_folder, file_in_project, uses_tool, precedes, produces_artifact, routine_in_project), record provenance and confidence. |
| Create | `src/workflow_dataset/personal/pattern_mining.py` — Routine/pattern mining: task sequences (from session/outcomes), app transitions (from app events), file flows (from file events), session patterns, repeated blocks/approvals (from outcomes); return structured patterns with evidence and confidence; no high-confidence from weak evidence. |
| Extend | `src/workflow_dataset/personal/graph_store.py` — Add `list_edges(conn, from_id=None, to_id=None, relation_type=None, limit=…)`, optional `provenance` table or store event_ids in node attributes. |
| Extend | `src/workflow_dataset/personal/work_graph.py` — Optional: add any new NodeTypes if needed (e.g. ARTIFACT_PATTERN), and a thin `build_graph_from_events(repo_root, events, …)` that calls graph_builder. |
| Create | `src/workflow_dataset/personal/graph_reports.py` — `graph_status(repo_root)`, `list_recent_routines(repo_root)`, `list_strong_patterns(repo_root)`, `explain_node(repo_root, node_id)` using graph_store + pattern_mining. |
| Extend | `src/workflow_dataset/cli.py` — Add `personal_group` with commands: `personal graph status`, `personal graph ingest --source recent`, `personal routines`, `personal patterns`, `personal graph explain --node <id>`. |
| Extend | `src/workflow_dataset/mission_control/state.py` — Add `personal_graph_summary` (or similar) block: recent routines, strong patterns, inferred associations, uncertain patterns. |
| Create | `tests/test_personal_graph_builder.py` — Tests: ingestion creates/updates nodes and edges; routine/pattern mining returns bounded results; provenance/confidence present; explain returns structure. |
| Create | `docs/M31E_M31H_PERSONAL_WORK_GRAPH.md` — Short doc: purpose, data flow (events → graph, mining → routines/patterns), CLI, mission control, constraints. |

## 4. Safety/risk note

- **Local-only**: All ingestion and mining stay on-device; no cloud graph. Reuse existing observation event log and graph store path; no new network.
- **No high-confidence from weak evidence**: Pattern mining must use minimum counts and cap confidence so weak evidence does not produce “strong” routines. Prefer false negatives over false positives.
- **Provenance**: Store source (observation/teaching/import) and event_ids where possible so any inference can be explained and audited.
- **Privacy**: Do not read file content; only metadata and event payloads already defined in LOCAL_OBSERVATION_EVENTS. Do not add hidden analytics; operator can inspect graph and patterns via CLI and mission control.

## 5. What this block will NOT do

- Will **not** rebuild or replace existing personal/*, observe/*, projects (project_case), sessions, outcomes, teaching, job_packs, value_packs, mission_control.
- Will **not** implement new OS-level app/browser/terminal collectors; will consume whatever normalized events exist in the event log (today: mainly file).
- Will **not** do cross-device sync or cloud graph.
- Will **not** infer routines with high confidence from a single or very few occurrences; thresholds and caps are enforced.
- Will **not** hide provenance; explain and status are first-class.
