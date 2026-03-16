# M23I — Desktop Task Benchmark + Trusted Automation Harness — Final Output

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `desktop_bench_group` and commands: list, run, run-suite, trusted-actions, board, compare, report, smoke, seed. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/desktop_bench/__init__.py` | Package exports. |
| `src/workflow_dataset/desktop_bench/config.py` | get_desktop_bench_root, get_cases_dir, get_runs_dir, get_suites_dir (data/local/desktop_bench). |
| `src/workflow_dataset/desktop_bench/schema.py` | DesktopBenchmarkCase, load_case, list_cases, load_suite, get_case; benchmark case schema (benchmark_id, title, task_category, required_adapters, required_approvals, simulation_expected_outcome, real_mode_eligibility, expected_artifacts, safety_notes, scoring_notes, steps, task_id). |
| `src/workflow_dataset/desktop_bench/harness.py` | run_benchmark(case_id, mode, repo_root, sandbox_root), run_suite(suite_name, mode, repo_root); mode explicit (simulate \| real); no silent fallback; records approvals_checked, adapters_used, outcome, errors, timing. |
| `src/workflow_dataset/desktop_bench/trusted_actions.py` | TRUSTED_ADAPTER_ACTIONS (file_ops + notes_document real actions), get_trusted_real_actions(repo_root), list_trusted_actions_report(repo_root). |
| `src/workflow_dataset/desktop_bench/scoring.py` | score_run(run_path), compute_trust_status(manifest, scores); dimensions: approval_correctness, simulate_correctness, real_run_correctness, artifact_completeness, provenance_completeness; trust status: trusted \| usable_with_simulation_only \| approval_missing \| experimental \| regression_detected. |
| `src/workflow_dataset/desktop_bench/board.py` | list_runs, get_run, compare_runs, board_report, format_board_report. |
| `src/workflow_dataset/desktop_bench/seed_cases.py` | seed_default_cases, seed_default_suite; writes inspect_folder_basic, snapshot_notes_safe, simulate_browser_open, replay_task_simulate and suite desktop_bridge_core. |
| `docs/M23I_READ_FIRST.md` | Pre-coding analysis (current state, gap, file plan, safety). |
| `docs/M23I_DESKTOP_BENCH_OPERATOR.md` | Operator guide: what is benchmarked, simulate-only, trusted actions, approvals, board/report, smoke. |
| `docs/M23I_FINAL_OUTPUT.md` | This file. |
| `tests/test_desktop_bench.py` | Tests: seed/list, get_case, run simulate, real requires registry, run_suite, trusted_actions, score_run, board_report, compare_runs, invalid mode, real eligibility refused. |

## 3. Exact CLI usage

```bash
workflow-dataset desktop-bench list [--repo-root PATH]
workflow-dataset desktop-bench run --id <case_id> --mode simulate|real [--repo-root PATH]
workflow-dataset desktop-bench run-suite --suite <suite_name> --mode simulate|real [--repo-root PATH]
workflow-dataset desktop-bench trusted-actions [--repo-root PATH]
workflow-dataset desktop-bench board [--suite NAME] [--repo-root PATH]
workflow-dataset desktop-bench compare --run <run_a> --run <run_b> [--repo-root PATH]
workflow-dataset desktop-bench report --suite <suite_name> [--repo-root PATH]
workflow-dataset desktop-bench smoke [--repo-root PATH]
workflow-dataset desktop-bench seed [--repo-root PATH]
```

## 4. Sample benchmark case

```yaml
benchmark_id: inspect_folder_basic
title: Inspect local folder and summarize contents
task_category: inspect_folder
required_adapters: [file_ops]
required_approvals: []
simulation_expected_outcome: success
real_mode_eligibility: true
expected_artifacts: []
safety_notes: Read-only; path should be under approved_paths for real mode.
scoring_notes: Pass if inspect_path and list_directory succeed.
steps:
  - adapter_id: file_ops
    action_id: inspect_path
    params:
      path: data/local
  - adapter_id: file_ops
    action_id: list_directory
    params:
      path: data/local
task_id: ""
```

## 5. Sample benchmark run output

```
Run 3e1474e003106cae6db4 outcome=pass mode=simulate
  run_path: .../data/local/desktop_bench/runs/3e1474e003106cae6db4
```

Run manifest (run_manifest.json) contains: run_id, run_path, benchmark_id, mode, outcome, approvals_checked, adapters_used, output_artifacts, errors, timing_seconds, timestamp, case_result.steps. After scoring: scores, trust_status.

## 6. Sample trusted real-action report

```
Trusted real actions (narrow safe subset)
  registry: .../data/local/capability_discovery/approvals.yaml
  registry_exists: False
  approved_paths: 0
  approved_action_scopes: 0
  ready_for_real: True
  trusted_actions:
    - file_ops.inspect_path
    - file_ops.list_directory
    - file_ops.snapshot_to_sandbox
    - notes_document.read_text
    - notes_document.summarize_text_for_workflow
    - notes_document.propose_status_from_notes
```

## 7. Sample benchmark board output

```
=== Desktop benchmark board (M23I) ===

Latest run: 3e1474e003106cae6db4  2026-03-16T18:30:14+00:00
Outcome: pass  Trust status: usable_with_simulation_only
Simulate-only coverage: 1.0  Trusted real coverage: 0

Recommended next action: run desktop-bench run-suite --suite desktop_bridge_core --mode simulate
```

## 8. Exact tests run

```bash
pytest tests/test_desktop_bench.py -v
```

All 11 tests passed: test_seed_and_list_cases, test_get_case, test_run_benchmark_simulate, test_run_benchmark_real_requires_registry, test_run_suite_simulate, test_trusted_actions, test_score_run, test_board_report, test_compare_runs, test_run_benchmark_invalid_mode, test_run_benchmark_real_eligibility_refused.

## 9. What remains simulate-only

- **browser_open**, **app_launch:** No real execution; benchmark cases that use them (e.g. simulate_browser_open) run in simulate only.
- **Task replay:** Cases with `task_id` set (e.g. replay_task_simulate) run via replay_task_simulate; simulate only.
- **write_file, create_note, append_to_note:** Contract simulate-only; not in benchmark steps for real.

## 10. Exact recommended next phase after M23I

- **Optional:** Integrate desktop benchmark board summary into mission control or dashboard (e.g. one line: latest desktop-bench outcome and trust status) if it can be done without a broad UI rewrite.
- **Optional:** Add more benchmark cases (e.g. multi-step notes_document flows, coordination-graph shape checks) and a regression gate in CI that runs `desktop-bench run-suite --suite desktop_bridge_core --mode simulate` and fails on aggregate_outcome fail.
- **Continue:** Use the harness in operator workflows; keep trusted real-action subset narrow and approval-gated; do not broaden into uncontrolled desktop automation.
