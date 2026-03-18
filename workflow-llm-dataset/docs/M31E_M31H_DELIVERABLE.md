# M31E–M31H Personal Work Graph Builder + Routine Mining — Deliverable

## 1. Files modified

| File | Changes |
|------|--------|
| `src/workflow_dataset/personal/work_graph.py` | Added `NodeType.ARTIFACT_PATTERN`. |
| `src/workflow_dataset/personal/graph_store.py` | Added `list_edges(conn, from_id=None, to_id=None, relation_type=None, limit=5000)`. |
| `src/workflow_dataset/cli.py` | Added `personal_group` with commands: `personal graph` (status \| ingest \| explain), `personal routines`, `personal patterns`. |
| `src/workflow_dataset/mission_control/state.py` | Added block 9b: `personal_graph_summary` (graph_exists, nodes/edges/routines/projects/tool_apps counts, recently_learned_routines, strongest_patterns_count, uncertain_patterns_count, next_action). |
| `src/workflow_dataset/mission_control/report.py` | Added `[Personal graph]` section to mission control report (exists, nodes, edges, routines, strong_patterns, uncertain, recent_routines, next). |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/personal/graph_models.py` | Edge/provenance conventions: `ATTR_SOURCE_EVENT_IDS`, `ProvenanceMarker`, `merge_provenance_into_attributes`, relation type constants. |
| `src/workflow_dataset/personal/graph_builder.py` | `ingest_events(store_path, events, root_paths)` — file + app events → nodes/edges with provenance; `build_graph_from_recent_events(store_path, log_dir, ...)` — load from event log and ingest. |
| `src/workflow_dataset/personal/pattern_mining.py` | `task_sequence_patterns`, `file_flow_patterns`, `session_shape_patterns`, `repeated_block_patterns_personal`, `repeated_success_patterns_personal`, `all_routines_from_events`, `all_patterns`; confidence caps and min_occurrences. |
| `src/workflow_dataset/personal/graph_reports.py` | `graph_status`, `list_recent_routines`, `list_strong_patterns`, `uncertain_patterns`, `explain_node`. |
| `tests/test_personal_graph_builder.py` | Tests for list_edges, provenance merge, ingest_events (file + app), pattern mining (task_sequence, file_flow, session_shape, blocks, success), graph_status, list_recent_routines, explain_node. |
| `docs/M31E_M31H_PERSONAL_WORK_GRAPH_BEFORE_CODING.md` | Pre-coding analysis: existing logic, gaps, file plan, safety, what this block does not do. |
| `docs/M31E_M31H_PERSONAL_WORK_GRAPH.md` | Short doc: purpose, data flow, CLI, mission control, constraints. |
| `docs/M31E_M31H_DELIVERABLE.md` | This deliverable. |

## 3. Exact CLI usage

```bash
# Status (default)
workflow-dataset personal graph status
workflow-dataset personal graph status --json

# Ingest from event log (recent events)
workflow-dataset personal graph ingest
workflow-dataset personal graph ingest --source recent
workflow-dataset personal graph ingest --source file
workflow-dataset personal graph ingest --repo-root /path/to/repo

# Explain a node
workflow-dataset personal graph explain --node routine_abc123
workflow-dataset personal graph explain --node node_xyz --json

# List routines and patterns
workflow-dataset personal routines
workflow-dataset personal routines --limit 30 --json
workflow-dataset personal patterns
workflow-dataset personal patterns --min-confidence 0.6 --limit 20 --json
```

## 4. Sample graph node/edge output

**Node (from graph_store / explain):**

```json
{
  "node_id": "routine_abc123",
  "node_type": "routine",
  "label": "User frequently works in project 'my_project'",
  "source": "observation",
  "confidence": 0.8,
  "created_utc": "2025-03-16T12:00:00Z",
  "updated_utc": "2025-03-16T12:00:00Z",
  "source_event_ids": ["evt_1", "evt_2"],
  "attributes_summary": {"routine_type": "frequent_project", "touch_count": 5, "project": "my_project"}
}
```

**Edge (from list_edges):**

```json
{"from_id": "routine_abc123", "to_id": "project_my_project", "relation_type": "routine_in_project"}
```

**graph_status:**

```json
{
  "graph_path": "/repo/data/local/work_graph.sqlite",
  "exists": true,
  "nodes_total": 42,
  "edges_total": 58,
  "nodes_by_type": {"file_ref": 20, "folder": 10, "project": 3, "routine": 5, "tool_app": 2},
  "routines_count": 5,
  "projects_count": 3,
  "tool_apps_count": 2
}
```

## 5. Sample routine/pattern inference

**Routine (from list_recent_routines / detect_routines + persist_routines):**

```json
{
  "node_id": "routine_xyz",
  "label": "User often works in folder src",
  "attributes": {"routine_type": "frequent_folder", "touch_count": 8, "path": "/repo/src", "confidence": 0.7}
}
```

**Pattern (from list_strong_patterns / pattern_mining):**

```json
{
  "pattern_type": "task_sequence",
  "sequence": ["job_1", "job_2", "macro_1"],
  "count": 3,
  "confidence": 0.7,
  "supporting_signals": ["session_count=3", "length=3"],
  "sample_session_ids": ["sess_1", "sess_2"]
}
```

```json
{
  "pattern_type": "repeated_block",
  "cause_code": "approval_missing",
  "source_ref": "job_42",
  "count": 2,
  "confidence": 0.6,
  "supporting_signals": ["block_count=2"]
}
```

## 6. Sample provenance/explanation output

**explain_node (human-oriented):**

```
Node routine_abc123  type=routine  label=User frequently works in project 'my_project'
  source=observation  confidence=0.8  events=2
  -> project_my_project (routine_in_project)
```

**explain_node (JSON):**

```json
{
  "node_id": "routine_abc123",
  "node_type": "routine",
  "label": "User frequently works in project 'my_project'",
  "source": "observation",
  "confidence": 0.8,
  "source_event_ids": ["evt_1", "evt_2"],
  "source_event_count": 2,
  "out_edges": [{"to_id": "project_my_project", "relation_type": "routine_in_project"}],
  "in_edges": [],
  "attributes_summary": {"routine_type": "frequent_project", "touch_count": 5}
}
```

## 7. Exact tests run

```bash
cd workflow-llm-dataset
pip install -e ".[dev]"   # or ensure pydantic + deps installed
python3 -m pytest tests/test_personal_graph_builder.py -v
```

Tests: `test_list_edges_empty`, `test_list_edges_after_add`, `test_provenance_merge`, `test_ingest_events_file_only`, `test_ingest_events_app`, `test_event_helpers`, `test_task_sequence_patterns_empty`, `test_file_flow_patterns_empty`, `test_file_flow_patterns_with_events`, `test_session_shape_patterns_empty`, `test_repeated_block_patterns_personal`, `test_repeated_success_patterns_personal`, `test_all_routines_from_events_empty`, `test_all_patterns_no_events`, `test_graph_status_no_graph`, `test_graph_status_with_graph`, `test_list_recent_routines_empty`, `test_explain_node_not_found`, `test_explain_node_found`.

## 8. Remaining gaps for later refinement

- **App/terminal/browser events**: Ingestion supports app (payload app_id/app_name); terminal/browser not yet wired (no collectors in observe yet). When available, extend graph_builder for terminal/browser and add relation types (e.g. uses_tool for terminal session).
- **Session/pack linkage**: Edges to session or value_pack nodes (e.g. associated_session) not created during ingest; can be added when current_session_id or pack context is passed in.
- **Project-case alignment**: Graph PROJECT nodes are inferred from paths; optional sync with project_case store (same project_id) and edges to project_case artifacts.
- **ARTIFACT_PATTERN nodes**: Node type added; population from file_flow_patterns or repeated artifact paths can be added (persist pattern as node + pattern_in_project edge).
- **Confidence tuning**: Min_occurrences and MAX_CONFIDENCE_FROM_WEAK are first-draft; can be made configurable or data-driven.
- **Operator confirmation UX**: uncertain_patterns are exposed in mission control; no CLI flow yet to “confirm” or “dismiss” a pattern (could write to a small state file or graph attribute).
