# M23E-F1 — Task Demonstration Capture + Replay Skeleton — Read First

## 1. Current adapter / discovery state

- **Adapters:** file_ops, notes_document, browser_open, app_launch. run_simulate(adapter_id, action_id, params) → SimulateResult; run_execute only for file_ops/notes_document (read-only/sandbox).
- **Capability discovery:** run_scan → CapabilityProfile (adapters, approved_paths, approved_apps, action_scopes); approval registry at data/local/capability_discovery/approvals.yaml; CLI capabilities scan/report, approvals list.
- **No task or demonstration concept:** No schema for a multi-step task, no capture format, no replay of a step sequence.

## 2. Exact gap to user-specific task learning

- **No task schema:** Need task id, step sequence, adapter/action refs per step, params, notes.
- **No persistence:** Need a local store for task definitions (e.g. data/local/task_demonstrations/).
- **No replay:** Need replay that runs steps in order using run_simulate only (no run_execute in F1).
- **No manifest/report:** Need to list tasks and show one task’s definition.
- **No CLI surface:** Need `tasks define` and `tasks replay --simulate`.

## 3. File plan

| Item | Path | Content |
|------|------|--------|
| Pre-coding doc | docs/M23E_F1_READ_FIRST.md | This file. |
| Schema | task_demos/models.py | TaskDefinition (task_id, steps[], notes?), TaskStep (adapter_id, action_id, params, notes?). |
| Store | task_demos/store.py | Tasks under data/local/task_demonstrations; list_tasks(), get_task(id), save_task(task). |
| Replay | task_demos/replay.py | replay_task_simulate(task_id, repo_root?) → list[SimulateResult]; run_simulate only. |
| Report | task_demos/report.py | format_task_manifest(task) or task_report; list tasks for manifest. |
| Package init | task_demos/__init__.py | Exports. |
| CLI | cli.py | tasks_group: tasks define (e.g. --from-file), tasks replay --task-id X --simulate (required). |
| Tests | tests/test_task_demos.py | Define, save, load, replay simulate only. |
| Delivery doc | docs/M23E_F1_DELIVERY.md | Files, sample task, sample replay output, CLI, tests. |

## 4. Risk note

- **No uncontrolled replay:** Replay runs only run_simulate (no run_execute); --simulate is the only mode in F1.
- **No real execution by default:** Task replay does not call run_execute; no file/URL/app changes.
- **No broad model-based planning:** F1 is capture + replay skeleton only; no LLM or autonomous planning.
- **Local persistence only:** Task definitions stored under data/local/; no cloud.
