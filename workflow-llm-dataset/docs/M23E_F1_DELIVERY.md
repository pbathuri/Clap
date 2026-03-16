# M23E-F1 — Task Demonstration Capture + Replay Skeleton — Delivery

## 1. Files modified

| File | Change |
|------|--------|
| `workflow-llm-dataset/src/workflow_dataset/cli.py` | Added tasks_group: tasks define (--from-file, --task-id + --step, --notes), tasks replay (--task-id, --simulate required), tasks list, tasks show. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M23E_F1_READ_FIRST.md` | Pre-coding: adapter/discovery state, gap, file plan, risk. |
| `docs/M23E_F1_DELIVERY.md` | This file. |
| `src/workflow_dataset/task_demos/__init__.py` | Package exports. |
| `src/workflow_dataset/task_demos/models.py` | TaskDefinition (task_id, steps[], notes), TaskStep (adapter_id, action_id, params, notes). |
| `src/workflow_dataset/task_demos/store.py` | data/local/task_demonstrations; list_tasks, get_task, save_task; YAML persist. |
| `src/workflow_dataset/task_demos/replay.py` | replay_task_simulate(task_id, repo_root?) → (TaskDefinition|None, list[SimulateResult]); run_simulate only. |
| `src/workflow_dataset/task_demos/report.py` | format_task_manifest(task), format_replay_report(task, results). |
| `tests/test_task_demos.py` | Save/load, list, get missing, replay simulate, format manifest/report. |

## 3. Sample task definition

File `examples/task_demo.yaml` (or any path passed to --from-file):

```yaml
task_id: demo_inspect_and_open
notes: "Inspect a path then open a URL (simulate only)."
steps:
  - adapter_id: file_ops
    action_id: inspect_path
    params:
      path: /tmp
  - adapter_id: browser_open
    action_id: open_url
    params:
      url: https://example.com
```

Or define from CLI without a file:

```bash
workflow-dataset tasks define --task-id demo1 --step "file_ops inspect_path path=/tmp" --step "browser_open open_url url=https://example.com"
```

## 4. Sample replay output

```bash
workflow-dataset tasks replay --task-id demo1 --simulate
```

Output (excerpt):

```
# Replay (simulate): demo1

## Step 1: file_ops inspect_path — ok
[Simulate] adapter=file_ops action=inspect_path
  path=/tmp
  Would inspect path metadata (exists, is_file, is_dir, size, mtime)...

## Step 2: browser_open open_url — ok
[Simulate] adapter=browser_open action=open_url
  url=https://example.com
  Validation: ok (category=https)
  Would open URL in browser (simulate only; F3)...
```

## 5. CLI usage

```bash
# Define from YAML file
workflow-dataset tasks define --from-file examples/task_demo.yaml

# Define from CLI (task id + steps)
workflow-dataset tasks define --task-id demo1 --step "file_ops inspect_path path=/tmp" --step "browser_open open_url url=https://example.com"
workflow-dataset tasks define --task-id notes_task --step "notes_document read_text path=./notes.txt" --notes "Read my notes"

# List tasks
workflow-dataset tasks list

# Show one task (manifest)
workflow-dataset tasks show --task-id demo1

# Replay in simulate mode (F1: only mode)
workflow-dataset tasks replay --task-id demo1 --simulate
workflow-dataset tasks replay --task-id demo1   # --simulate is default True

# Replay without --simulate is rejected in F1
workflow-dataset tasks replay --task-id demo1 --no-simulate   # exits with error
```

## 6. Tests run

```bash
cd workflow-llm-dataset
pytest tests/test_task_demos.py -v
```

**7 tests:** save and load task, list tasks, get_task missing returns None, replay_task_simulate success, replay unknown task returns None and empty results, format_task_manifest, format_replay_report. All passed.

## 7. Remaining weaknesses (F1 only)

- **Simulate only:** Replay does not call run_execute; no real execution.
- **No versioning:** Task definitions are overwritten on save; no history.
- **No validation:** define does not validate adapter_id/action_id against registry before save.
- **Step parsing:** CLI --step is space-separated; param values with spaces need quoting or file-based define.
