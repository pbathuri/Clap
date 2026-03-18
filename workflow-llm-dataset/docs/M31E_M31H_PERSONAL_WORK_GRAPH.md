# M31E–M31H Personal Work Graph Builder + Routine Mining

## Purpose

Local-first personal work memory and routine layer that:
- Ingests normalized observation events (file, app) into a persistent graph
- Maps events to projects/sessions where possible
- Mines repeated routines and patterns (task sequences, file flows, session shapes, blocks, success)
- Exposes status, routines, patterns, and explain-node via CLI and mission control

## Data flow

1. **Events** — From `observe` (file_activity, local_events). Stored in event log (e.g. `data/local/events/events_*.jsonl`).
2. **Ingestion** — `graph_builder.ingest_events()` or `build_graph_from_recent_events()` creates/updates nodes (file_ref, folder, project, tool_app) and edges (file_in_folder, file_in_project, uses_tool), with `source_event_ids` in node attributes.
3. **Routines** — Existing `routine_detector.detect_routines()` (file-based) + `work_graph.persist_routines()`; graph_reports lists routine nodes from the graph.
4. **Pattern mining** — `pattern_mining`: task_sequence_patterns, file_flow_patterns, session_shape_patterns, repeated_block_patterns_personal, repeated_success_patterns_personal. Confidence capped; min_occurrences enforced.
5. **Reports** — `graph_reports`: graph_status, list_recent_routines, list_strong_patterns, uncertain_patterns, explain_node.

## CLI

- `workflow-dataset personal graph status` — Graph path, exists, node/edge counts, routines/projects/tools counts.
- `workflow-dataset personal graph ingest [--source recent|file|app]` — Load recent events from log and ingest into graph.
- `workflow-dataset personal graph explain --node <node_id>` — Explain node: type, label, edges, provenance (source_event_ids), confidence.
- `workflow-dataset personal routines [--limit N]` — List routine nodes from graph.
- `workflow-dataset personal patterns [--min-confidence 0.5] [--limit N]` — List strong patterns (task_sequence, file_flow, session_shape, repeated_block, repeated_success).

## Mission control

State includes `personal_graph_summary`:
- graph_exists, nodes_total, edges_total, routines_count, projects_count, tool_apps_count
- recently_learned_routines (labels), strongest_patterns_count, strong_pattern_types
- uncertain_patterns_count, uncertain_needing_confirmation
- next_action

Report section: `[Personal graph] exists=... nodes=... routines=... strong_patterns=... uncertain=...`

## Constraints

- No high confidence from weak evidence (confidence caps and min_occurrences in pattern_mining).
- Provenance stored in node attributes (`source_event_ids`); explain exposes it.
- Local-only; no cloud graph. All data under repo/local paths.
- Does not rebuild existing personal/*, observe/*, project_case, session, outcomes; extends them.
