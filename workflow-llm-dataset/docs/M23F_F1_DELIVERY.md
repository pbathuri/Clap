# M23F-F1 — Cross-App Coordination Graph (advisory only) — Delivery

## 1. Files modified

| File | Change |
|------|--------|
| `workflow-llm-dataset/src/workflow_dataset/cli.py` | Added graph_group: graph from-task, graph summary, graph export, graph inspect. |
| `workflow-llm-dataset/src/workflow_dataset/mission_control/state.py` | Added coordination_graph_summary (tasks_count, total_nodes, total_edges); local_sources task_demonstrations. |
| `workflow-llm-dataset/src/workflow_dataset/mission_control/report.py` | Added [Coordination graph] line when coordination_graph_summary present. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M23F_F1_READ_FIRST.md` | Pre-coding: state, gap, file plan, safety. |
| `docs/M23F_F1_DELIVERY.md` | This file. |
| `src/workflow_dataset/coordination_graph/__init__.py` | Exports. |
| `src/workflow_dataset/coordination_graph/models.py` | CoordinationGraph, GraphNode (id, type=file\|notes\|browser\|app\|artifact, label, adapter_id, action_id, step_index), GraphEdge (source_id, target_id, edge_type). |
| `src/workflow_dataset/coordination_graph/build.py` | task_definition_to_graph(task, include_artifact_nodes?) → CoordinationGraph; one node per step, type from adapter_id; sequence edges. |
| `src/workflow_dataset/coordination_graph/report.py` | format_graph_summary(graph) → str. |
| `src/workflow_dataset/coordination_graph/export.py` | graph_to_dict(graph) → dict for JSON. |
| `tests/test_coordination_graph.py` | Build from task, with/without artifacts, format summary, graph_to_dict, from stored task. |

## 3. Sample graph output

For a task with steps: file_ops inspect_path, browser_open open_url:

```bash
workflow-dataset graph from-task --task-id demo1
```

```
# Coordination graph: demo1

  nodes: 2  edges: 1

## Nodes (by type)
  browser: browser_open:open_url
  file: file_ops:inspect_path

## Edges (sequence)
  step_0 -> step_1 (sequence)
```

## 4. CLI usage

```bash
# Build and print graph from a task
workflow-dataset graph from-task --task-id demo1
workflow-dataset graph from-task --task-id demo1 --artifacts

# Summary of all tasks' graphs
workflow-dataset graph summary

# Export graph to JSON
workflow-dataset graph export --task-id demo1 --output graph_demo1.json
workflow-dataset graph export --task-id demo1 -o graph.json --artifacts

# Inspect (same as from-task without --artifacts)
workflow-dataset graph inspect --task-id demo1
```

## 5. Tests run

```bash
cd workflow-llm-dataset
pytest tests/test_coordination_graph.py -v
```

**5 tests:** task_definition_to_graph simple (2 nodes, 1 edge, file + browser types), with artifact nodes (≥3 nodes), format_graph_summary, graph_to_dict, graph from stored task. All passed.

## 6. Next recommended phase

- **M23F-F2 (optional):** Use coordination graph in mission_control next_action (e.g. “suggest replaying task X” when graph exists). Keep advisory; no auto-replay.
- **Multi-task graph:** Aggregate multiple tasks into one graph (e.g. shared nodes by adapter/action type) for a “desktop workflow map” view.
- **Export formats:** Add Mermaid or DOT export for diagram tools; keep JSON for tooling.
- **Artifact semantics:** Define optional “produces”/“consumes” edges when params (e.g. path) link steps; still advisory only.
- **No change to execution:** Graph remains read-only; no autonomous multi-app execution or hidden scheduling.
