# M23I — Desktop benchmark operator guide

What is benchmarked, what is simulate-only, trusted real actions, how to interpret board/report, and how this differs from uncontrolled desktop automation.

---

## 1. What is benchmarked

The desktop benchmark harness runs **benchmark cases** that exercise the desktop bridge in a narrow, safe way:

- **inspect_folder_basic:** file_ops inspect_path + list_directory (data/local). Eligible for real mode when approvals allow.
- **snapshot_notes_safe:** file_ops snapshot_to_sandbox + notes_document read_text. Real-mode eligible; requires approvals.
- **simulate_browser_open:** browser_open open_url (simulate only). Not real-mode eligible.
- **replay_task_simulate:** Replay task `cli_demo` in simulate mode only.

Cases are stored under `data/local/desktop_bench/cases/` (YAML). Suites (e.g. `desktop_bridge_core`) list case ids under `data/local/desktop_bench/suites/`.

---

## 2. What is still simulate-only

- **browser_open**, **app_launch:** No real execution; benchmark steps that use them run in simulate mode only.
- **Task replay:** Cases with `task_id` set run via task-demo replay, which is simulate-only.
- **Benchmarks with `real_mode_eligibility: false`:** Only run with `--mode simulate`.

Real mode is **opt-in** and only for cases marked `real_mode_eligibility: true` and only when the approval registry exists and allows the actions.

---

## 3. Trusted real-action subset

The **trusted real actions** are a fixed, narrow list:

- **file_ops:** inspect_path, list_directory, snapshot_to_sandbox  
- **notes_document:** read_text, summarize_text_for_workflow, propose_status_from_notes  

No browser or app launch. The command `workflow-dataset desktop-bench trusted-actions` shows which of these are currently approved (when registry exists and lists them in `approved_action_scopes` with `executable: true`).

---

## 4. How approvals are checked

- **Simulate:** No approval check; all cases can run in simulate mode.
- **Real:** The harness requires `data/local/capability_discovery/approvals.yaml` to exist. If it does not exist, real-mode run is refused with a clear message. If it exists, each step is gated by the same approval_check used by `adapters run` (approved_paths for path-using actions, approved_action_scopes for (adapter_id, action_id)).

There is **no silent fallback** from real to simulate; mode is always explicit.

---

## 5. How to interpret board / report

- **desktop-bench board:** Shows latest run id, outcome (pass/fail), trust status (trusted | usable_with_simulation_only | approval_missing | experimental | regression_detected), simulate-only coverage, trusted real coverage, missing approval blockers, regressions, recommended next action.
- **Trust status:**
  - **trusted:** Real run, outcome pass, approval present, real_run_correctness and approval_correctness 1.0.
  - **usable_with_simulation_only:** Simulate run passed; no real execution.
  - **approval_missing:** Real run requested but registry missing.
  - **experimental:** Run had failures or partial success.
  - **regression_detected:** Used when comparing two runs (e.g. compare --run latest --run previous) and the newer run fails where the older passed.

Scoring (approval_correctness, simulate_correctness, real_run_correctness, artifact_completeness, provenance_completeness) is written into the run manifest and is transparent/inspectable.

---

## 6. How this differs from uncontrolled desktop automation

- **Narrow:** Only the listed adapters/actions; no arbitrary scripts or system calls.
- **Measurable:** Every run produces a manifest (run_id, mode, outcome, approvals_checked, errors, timing).
- **Approval-gated:** Real mode requires registry and respects approved_paths and approved_action_scopes.
- **Local:** All artifacts under `data/local/desktop_bench/runs/`; no hidden network.
- **Explicit mode:** Simulate vs real is chosen by the operator; no automatic escalation to real.

---

## 7. Smoke suite

Run:

```bash
workflow-dataset desktop-bench seed
workflow-dataset desktop-bench smoke
```

Smoke checks: adapters available, approvals file present/missing, benchmark cases count, trusted real actions count and ready_for_real, and one benchmark run in simulate mode. Use it to verify the harness is healthy before running suites.

---

## 8. CLI reference

| Command | Purpose |
|--------|--------|
| `desktop-bench list` | List benchmark case ids |
| `desktop-bench run --id <id> --mode simulate \| real` | Run one case |
| `desktop-bench run-suite --suite desktop_bridge_core --mode simulate \| real` | Run a suite |
| `desktop-bench trusted-actions` | List actions approved for real execution |
| `desktop-bench board` | Show benchmark board (latest, trust status, next action) |
| `desktop-bench compare --run latest --run previous` | Compare two runs |
| `desktop-bench report --suite <name>` | Report for suite (latest run summary) |
| `desktop-bench smoke` | Smoke check (adapters, approvals, cases, harness) |
| `desktop-bench seed` | Seed default cases and desktop_bridge_core suite |
