# M23C–M23F — Desktop Operator Bridge — Final Pane Summary

This document summarizes the completed sequential build (M23C-F1 through M23F-F1) that bridges the current local ops/reporting operator product toward the personal desktop/work operator vision.

---

## 1. Completed sub-steps

| Step | Deliverable | Status |
|------|-------------|--------|
| **M23C-F1** | Desktop action adapter contracts + registry; simulate-first model; file_ops, notes_document, browser_open, app_launch contracts; CLI adapters list/show/simulate | Done |
| **M23C-F2** | Local file/folder adapter (inspect_path, list_directory, snapshot_to_sandbox); notes adapter (read_text, summarize_text_for_workflow, propose_status_from_notes); execute layer + provenance; CLI adapters run | Done |
| **M23C-F3** | Browser/open-url simulation (URL validation, preview); app-launch simulation (approved app resolution, preview); availability checks; simulate-only for browser/app | Done |
| **M23D-F1** | Capability discovery model; approval registry (approved_paths, approved_apps, approved_action_scopes); profile report; CLI capabilities scan/report, approvals list | Done |
| **M23E-F1** | Task demonstration schema; local task store (data/local/task_demonstrations); simulate-only replay; task manifest/report; CLI tasks define, tasks replay --simulate, tasks list, tasks show | Done |
| **M23F-F1** | Cross-app coordination graph (advisory); schema + mapping from task steps to nodes/edges; graph summary/export/inspect; optional mission-control visibility hook | Done |

---

## 2. Integrated command surface added

All commands are under `workflow-dataset` (no new top-level binary). New groups and commands:

| Group | Commands |
|-------|----------|
| **adapters** | `list`, `show --id`, `simulate --id --action --param`, `run --id --action --param [--sandbox]` |
| **capabilities** | `scan`, `report [--output]`, `approvals` |
| **approvals** | `list` |
| **tasks** | `define (--from-file \| --task-id + --step)`, `replay --task-id --simulate`, `list`, `show --task-id` |
| **graph** | `from-task --task-id [--artifacts]`, `summary`, `export --task-id --output`, `inspect --task-id` |

**Exact CLI usage (copy-paste):**

```bash
# Adapters (M23C)
workflow-dataset adapters list
workflow-dataset adapters show --id file_ops
workflow-dataset adapters simulate --id browser_open --action open_url --param url=https://example.com
workflow-dataset adapters run --id file_ops --action inspect_path --param path=/tmp
workflow-dataset adapters run --id notes_document --action read_text --param path=./notes.txt

# Capabilities & approvals (M23D)
workflow-dataset capabilities scan
workflow-dataset capabilities report
workflow-dataset capabilities report --output capability_report.md
workflow-dataset approvals list

# Tasks (M23E)
workflow-dataset tasks define --task-id demo1 --step "file_ops inspect_path path=/tmp" --step "browser_open open_url url=https://example.com"
workflow-dataset tasks list
workflow-dataset tasks show --task-id demo1
workflow-dataset tasks replay --task-id demo1 --simulate

# Coordination graph (M23F)
workflow-dataset graph from-task --task-id demo1
workflow-dataset graph summary
workflow-dataset graph export --task-id demo1 --output graph_demo1.json
workflow-dataset graph inspect --task-id demo1
```

---

## 3. How this advances the product toward the personal desktop/work operator goal

- **Safe adapter layer:** Typed contracts (file, notes, browser, app) with explicit simulate vs real-execution flags, expected inputs/outputs, failure modes, and approval requirements. The product can now *describe* desktop actions in a uniform way without executing them unsafely.
- **First useful execution (read-only/sandbox):** File and notes adapters support real read-only actions and sandbox-only snapshot. Operators can inspect paths, list directories, snapshot to sandbox, read/summarize notes, and propose status—all local and inspectable.
- **Simulate-only browser/app:** URL validation and approved-app resolution give a clear “what would open/launch” preview without any browser automation or app launch. Keeps the door open for future gated execution without adding risk now.
- **Capability and approval visibility:** Capability scan and approval registry make it explicit which adapters, paths, apps, and action scopes are available and approved. Supports operator decisions and future gating.
- **User task capture and replay:** Tasks can be defined (from file or CLI), stored locally, and replayed in simulate-only mode. This is the first user-specific task-learning scaffold and feeds the coordination graph.
- **Advisory coordination graph:** Task steps are mapped to a cross-app graph (file, notes, browser, app, artifact). Mission control can show a coordination summary. No autonomous execution or hidden scheduling—purely advisory.

The existing ops/reporting surface (dashboard, mission control, templates, chain lab, intake, edge readiness) is unchanged. The bridge is additive: adapters, capability discovery, task demos, and graph sit alongside current workflows and can later feed a desktop work operator without replacing or weakening them.

---

## 4. How local inference/runtime remains backend-agnostic

- **No LLM in this pane:** M23C–M23F do not call any LLM or inference API. Adapters, capability discovery, task store, replay, and coordination graph are deterministic and local (files, YAML, in-memory registry). No model loading, no inference backend.
- **Execution paths are explicit:** `run_simulate` and `run_execute` are pure function calls; no hidden “agent” or “planner” process. Any future use of local inference (for suggestions, next action, or task refinement) can be plugged in behind a thin interface (e.g. “suggest next step given task + context”) that this pane does not define or implement.
- **Config and data stay local:** Approval registry, task definitions, and graph export live under `data/local/`. No runtime dependency on a specific inference backend. The design allows:
  - Current local LLM path (if any) to remain as-is.
  - An optional future local inference backend (e.g. llama.cpp-backed) to be added behind an adapter or “suggestions” module without rewriting adapters, tasks, or graph.

---

## 5. Where llama.cpp could fit as an optional local inference backend later

- **Not required for this pane:** No code in M23C–M23F depends on llama.cpp or any specific inference engine. The repo is not a llama.cpp integration project.
- **Compatibility target:** The external reference `https://github.com/ggml-org/llama.cpp` can be used as an optional local inference and compatibility target. For example:
  - A future “desktop operator suggestions” or “next-step” module could call a local inference API (current stack or a llama.cpp-based server) to propose the next task step or refine a task definition. The adapter/task/graph layer would consume *results* (e.g. suggested adapter/action/params), not the backend itself.
  - Capability discovery and approval registry already describe what is allowed; any backend (including a future llama.cpp-backed one) could be constrained to suggest only approved adapters, actions, and paths.
- **Recommendation:** Keep the desktop-agent layer backend-agnostic. Introduce a small “suggestions” or “next action” interface when adding LLM-backed behavior; implement one or more backends (current local path, optional llama.cpp, etc.) behind that interface so M23C–M23F remain unchanged.

---

## 6. Exact recommended next phase after M23F-F1

- **Wire approval into execution (optional):** Before running any real execution (already limited to file_ops/notes_document), check the capability approval registry (approved_paths, approved_action_scopes) and refuse or prompt if not approved. Keeps safety explicit.
- **Optional real browser/open and app launch:** If product requirements later allow, add gated execution for browser_open and app_launch (e.g. user confirmation, allowlist) using the existing contracts and URL/app validation. No change to simulate-first default.
- **Task replay with real execution (gated):** Extend task replay with an explicit “run for real” mode that calls `run_execute` only for steps whose adapter/action support it and only after approval/sandbox checks. Default remains simulate-only.
- **Coordination graph in mission-control next action:** Use the graph (and task list) in mission control’s “recommended next action” to suggest, for example, “Replay task X in simulate” or “Define a task for Y.” Advisory only; no auto-replay or auto-execution.
- **Multi-task / desktop workflow map:** Aggregate coordination graphs across tasks into a single “desktop workflow map” (e.g. shared nodes by adapter/action type) for operator visibility. Export (e.g. Mermaid/DOT) for diagrams.
- **Backend-agnostic suggestions (when adding LLM):** When introducing local inference for suggestions or next-step proposals, add a thin interface and keep M23C–M23F unchanged; optionally support llama.cpp or other backends behind that interface.

---

## 7. Tests run (all passing)

```bash
cd workflow-llm-dataset
pytest tests/test_desktop_adapters.py tests/test_capability_discovery.py tests/test_task_demos.py tests/test_coordination_graph.py -v
```

**Result:** 58 passed (38 desktop_adapters, 8 capability_discovery, 7 task_demos, 5 coordination_graph).

---

## 8. Files modified (across all sub-steps)

- **cli.py:** Added adapters, capabilities, approvals, tasks, graph groups and their commands.
- **mission_control/state.py:** Added coordination_graph_summary and task_demonstrations in local_sources.
- **mission_control/report.py:** Added [Coordination graph] line when summary present.

## 9. Files created (by sub-step)

- **M23C-F1:** `desktop_adapters/` (contracts, registry, simulate, `__init__`); docs M23C_F1_READ_FIRST, M23C_F1_DELIVERY; tests/test_desktop_adapters.py (initial).
- **M23C-F2:** `desktop_adapters/sandbox_config.py`, `file_runner.py`, `notes_runner.py`, `execute.py`; updated contracts/simulate/__init__; docs M23C_F2_READ_FIRST, M23C_F2_DELIVERY; extended test_desktop_adapters.
- **M23C-F3:** `desktop_adapters/url_validation.py`, `app_allowlist.py`; updated contracts/simulate/__init__; docs M23C_F3_READ_FIRST, M23C_F3_DELIVERY; extended test_desktop_adapters.
- **M23D-F1:** `capability_discovery/` (models, approval_registry, discovery, report, `__init__`); docs M23D_F1_READ_FIRST, M23D_F1_DELIVERY; tests/test_capability_discovery.py.
- **M23E-F1:** `task_demos/` (models, store, replay, report, `__init__`); docs M23E_F1_READ_FIRST, M23E_F1_DELIVERY; tests/test_task_demos.py.
- **M23F-F1:** `coordination_graph/` (models, build, report, export, `__init__`); docs M23F_F1_READ_FIRST, M23F_F1_DELIVERY; tests/test_coordination_graph.py.

All of the above preserve sandbox-only and approval-gated semantics; no cloud-first logic, no hidden background agents, and no requirement for llama.cpp or any specific inference backend.
