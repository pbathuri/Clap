# M23F-F1 — Cross-App Coordination Graph (advisory only) — Read First

## 1. Current adapter / discovery / task state

- **Adapters:** file_ops, notes_document, browser_open, app_launch. run_simulate, run_execute (file_ops/notes_document only). Contracts define adapter_id, action_id, params.
- **Capability discovery:** run_scan → CapabilityProfile; approval registry; capabilities scan/report, approvals list.
- **Task demos:** TaskDefinition (task_id, steps[], notes), TaskStep (adapter_id, action_id, params, notes). Stored under data/local/task_demonstrations; replay_task_simulate (simulate only). CLI: tasks define, tasks replay --simulate, tasks list, tasks show.
- **No graph view:** Tasks are linear step lists; no representation of how a task flows across file/notes/browser/app/artifact domains or of cross-app coordination.

## 2. Exact gap to multi-app desktop work

- **No coordination model:** Need a graph that represents flow across local files, notes, browser, app-launch, and (advisory) generated artifacts.
- **No mapping from tasks to graph:** Task steps are adapter/action refs; need nodes (per step or per domain) and edges (sequence, or uses/produces) for advisory visualization and reporting.
- **No graph summary or export:** No way to inspect or export this graph for operators or downstream tooling.
- **No mission-control visibility:** Mission control does not yet surface task/coordination state.

## 3. File plan

| Item | Path | Content |
|------|------|--------|
| Pre-coding doc | docs/M23F_F1_READ_FIRST.md | This file. |
| Schema | coordination_graph/models.py | CoordinationGraph (nodes[], edges[]), GraphNode (id, type=file\|notes\|browser\|app\|artifact, label, adapter_id?, action_id?, step_index?), GraphEdge (source_id, target_id, edge_type=sequence). |
| Mapping | coordination_graph/build.py | task_definition_to_graph(TaskDefinition) → CoordinationGraph; one node per step, type from adapter_id; edges step_i → step_i+1 (sequence). Optional artifact node between steps (advisory). |
| Report | coordination_graph/report.py | format_graph_summary(graph) → str; optional format for export. |
| Export | coordination_graph/export.py | graph_to_dict(graph) for JSON export; write to file. |
| Package init | coordination_graph/__init__.py | Exports. |
| CLI | cli.py | graph_group: graph from-task --task-id, graph summary (all tasks), graph export --task-id --output. |
| Mission-control | mission_control/state.py, report.py | Optional: add coordination_graph_summary (task_count, graph_stats); one line in report if present. |
| Tests | tests/test_coordination_graph.py | Build from task, summary, export. |
| Delivery doc | docs/M23F_F1_DELIVERY.md | Files, sample output, CLI, tests, next phase. |

## 4. Safety note

- **Advisory only:** Graph is for visualization and reporting; no autonomous multi-app execution.
- **No hidden scheduling:** Graph is derived from stored task definitions; no background scheduler or automation.
- **No execution:** Building or exporting the graph does not run adapters or replay tasks.
- **Read-only:** Graph build reads task definitions only; no writes except explicit export to file.
