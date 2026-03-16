# M23I — Desktop Task Benchmark + Trusted Automation Harness — Read First

## 1. Current desktop-bridge state

- **Adapters:** file_ops, notes_document, browser_open, app_launch (registry, contracts, simulate, execute).
- **Execution:** `run_simulate` for all; `run_execute` only for file_ops and notes_document (read-only or sandbox copy), gated by `check_execution_allowed` when approval registry exists.
- **Capability discovery:** `run_scan`, format_report; approval_registry load/save; approval_check gates run_execute.
- **Task demos:** store (list_tasks, get_task, save_task); replay (replay_task_simulate only — no run_execute in replay path).
- **Coordination graph:** task_definition_to_graph, summary/export/inspect; mission control state includes coordination_graph_summary and desktop_bridge.
- **Mission control:** desktop_bridge (adapters_count, approvals_path, approvals_file_exists, tasks_count, etc.); next_action can recommend replay_task.

## 2. Simulate-only vs real-executable

| Adapter / area | Simulate | Real (when allowed) |
|----------------|----------|---------------------|
| file_ops (inspect_path, list_directory, snapshot_to_sandbox) | ✓ | ✓ (gated) |
| notes_document (read_text, summarize_text_for_workflow, propose_status_from_notes) | ✓ | ✓ (gated) |
| browser_open, app_launch | ✓ | No (simulate only) |
| write_file, create_note, append_to_note | ✓ (preview) | No |
| Task replay | ✓ (run_simulate per step) | No |

## 3. What approvals currently gate

- **Registry file:** `data/local/capability_discovery/approvals.yaml`.
- **When present:** (1) `approved_action_scopes` (if non-empty): (adapter_id, action_id) must appear with `executable: true`. (2) `approved_paths` (if non-empty): path-using actions must have path under an approved prefix.
- **Refusal:** Clear message; no silent bypass. CLI and run_execute return failure with message.

## 4. What can be benchmarked immediately

- Single-step **simulate:** any adapter/action via run_simulate; success, preview, real_execution_supported.
- Single-step **real:** file_ops and notes_document actions when approval allows (or no registry); success, output, provenance.
- Multi-step: task replay in **simulate** (replay_task_simulate); per-step SimulateResult.
- Outcomes: success/failure, output/preview, errors/refusals, timing.
- Approval: presence of registry, scope/path checks, refusal message when denied.

## 5. Exact gap to trusted automation harness

- **No benchmark task schema** for desktop (eval/ is for workflow/LLM cases).
- **No harness** that runs desktop benchmark cases in simulate vs real with recorded mode, approvals, outcomes, timings.
- **No explicit "trusted real-action" list** or CLI (trusted-actions).
- **No scoring** for approval correctness, simulate correctness, real-run correctness, simulate/real parity, artifact/provenance completeness, or trust signal.
- **No desktop benchmark board/report** (eval/board is for workflow runs).
- **No operator doc or smoke** for desktop automation harness.

## 6. File plan

| Module | Files | Purpose |
|--------|-------|--------|
| B — Schema | desktop_bench/schema.py, desktop_bench/config.py | Benchmark case model (id, title, category, required_adapters, required_approvals, simulation_expected, real_eligibility, expected_artifacts, safety_notes, scoring_notes). Config: data/local/desktop_bench/{cases,runs,suites}. |
| C — Harness | desktop_bench/harness.py | run_benchmark(case_id, mode=simulate|real, repo_root), run_suite(suite_name, mode), record run_manifest (benchmark_id, mode, approvals_checked, adapters_used, outcome, artifacts, errors, timing). No silent fallback real→simulate. |
| D — Trusted | desktop_bench/trusted_actions.py | List actions approved for real execution (from registry + adapter contracts); require approvals for real; refuse clearly; record what was done. |
| E — Scoring | desktop_bench/scoring.py | approval_correctness, simulate_correctness, real_run_correctness, parity, artifact_completeness, provenance_completeness; trust status: trusted | usable_with_simulation_only | approval_missing | experimental | regression_detected. Transparent. |
| F — Board | desktop_bench/board.py | list_runs, get_run, board_report (latest, pass/fail, simulate-only coverage, trusted real coverage, missing approvals, regressions, top safe/risky adapters, next action). |
| G — Docs + smoke | docs/M23I_DESKTOP_BENCH_OPERATOR.md | What is benchmarked, simulate-only, trusted real, how approvals checked, how to read board/report; smoke: adapters, approvals, harness healthy, trusted subset ready. |
| H — Tests | tests/test_desktop_bench*.py | Schema load, run one benchmark simulate, run suite simulate, trusted_actions list, scoring, board. |
| CLI | cli.py | desktop-bench list, run --id X --mode simulate|real, run-suite --suite Y --mode, trusted-actions, board, compare, report, smoke. |

## 7. Safety/risk note

- **No silent fallback:** Mode (simulate vs real) is explicit; never switch real→simulate without operator visibility.
- **Real only when allowed:** Harness requires approval check for real mode; refuse clearly when approval or capability missing.
- **All local:** Run artifacts under data/local/desktop_bench; no hidden network.
- **Trusted list narrow:** Only file_ops (inspect_path, list_directory, snapshot_to_sandbox) and notes_document (read_text, summarize_text_for_workflow, propose_status_from_notes). No browser/app real in M23I.
- **Simulate success ≠ safe real:** Scoring and trust signals must not treat simulate pass as proof of safe real without explicit approval and real run.
