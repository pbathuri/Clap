# M18–M20 execution summary (verification pass)

Evidence from running the narrow release + pilot stack in the repo-local venv. No architecture changes; one minor report-wording fix applied.

---

## 1. Verification summary of M18–M20 presence

| Item | Status |
|------|--------|
| docs/FIRST_NARROW_RELEASE.md | Present |
| docs/RELEASE_USER_JOURNEY.md | Present |
| docs/FOUNDER_DEMO_FLOW.md | Present |
| docs/NOT_YET_SUPPORTED.md | Present |
| docs/PILOT_SCOPE.md | Present |
| docs/RELIABILITY_TRIAGE.md | Present |
| docs/PILOT_OPERATOR_GUIDE.md | Present |
| docs/M20_DECISION_OUTPUT.md | Present |
| configs/release_narrow.yaml | Present |
| src/workflow_dataset/pilot/health.py | Present |
| release commands (verify, run, demo, package, report) in cli.py | Present |
| pilot commands (verify, status, latest-report) in cli.py | Present |
| console pilot view (P) in ui/ | Present |
| data/local/work_graph.sqlite | Present |
| data/local/llm/runs (successful adapter) | Present (e.g. 20260315_171057) |
| data/local/trials/latest_feedback_report.md | Present |
| data/local/release/release_readiness_report.md | Present |
| data/local/pilot/pilot_readiness_report.md | Present |
| data/local/pilot/reliability_issues.json | Present |

---

## 2. Exact commands run

All commands used the **repo-local venv**:

- `.venv/bin/python -c "import workflow_dataset.cli; ..."`
- `.venv/bin/workflow-dataset --help`
- `.venv/bin/workflow-dataset release --help`
- `.venv/bin/workflow-dataset pilot --help`
- `.venv/bin/workflow-dataset release verify --config configs/settings.yaml --release-config configs/release_narrow.yaml`
- `.venv/bin/workflow-dataset release run --config configs/settings.yaml --release-config configs/release_narrow.yaml`
- `.venv/bin/workflow-dataset release demo --config configs/settings.yaml --release-config configs/release_narrow.yaml`
- `.venv/bin/workflow-dataset pilot verify --config configs/settings.yaml --release-config configs/release_narrow.yaml`
- `.venv/bin/workflow-dataset pilot status`
- `.venv/bin/workflow-dataset pilot status --json`
- `.venv/bin/workflow-dataset pilot latest-report`
- `.venv/bin/python -c "from workflow_dataset.ui ...; assert Screen.PILOT ..."` (console/pilot import check)
- `.venv/bin/python -m pytest tests/test_pilot.py tests/test_release.py tests/test_feedback.py tests/test_trial_cli.py -v`

---

## 3. Files modified during debugging

- **src/workflow_dataset/pilot/health.py:** One wording fix only. Line that wrote `**Degraded mode:** False (no adapter; base model only)` now writes `(adapter available)` when `degraded` is False and `(no adapter; base model only)` when True. No behavior change; report text only.

---

## 4. Release verify / run / demo results

- **release verify:** Exit 0. Output: Release scope: Operations reporting assistant; Graph: OK; Setup dir, Parsed artifacts, Style signals: OK; LLM adapter: OK; Trials (ops): 4.
- **release run:** Exit 0. Completed three ops trials (ops_summarize_reporting, ops_scaffold_status, ops_next_steps) with task=0.90 each; results in data/local/trials.
- **release demo:** Exit 0. Ran 3 prompts; model produced short generic answers (no user context passed into the demo prompts in this run). No crash; commands behave as implemented.

---

## 5. Pilot verify / status / latest-report results

- **pilot verify:** Exit 0. Ready: True; Graph: OK; Adapter: OK (data/local/llm/runs/20260315_171057/adapters).
- **pilot status:** Ready: True, Safe to demo: True, Degraded: False, Adapter: OK, Latest run and Feedback report paths printed.
- **pilot status --json:** Valid JSON with ready, blocking, warnings, degraded, safe_to_demo, config_valid, graph_ok, adapter_ok, adapter_path, latest_run_dir, latest_feedback_report, scope.
- **pilot latest-report:** Exit 0. Wrote data/local/pilot/pilot_readiness_report.md with scope, readiness, evidence, recommendation.

---

## 6. Console launch / pilot view

- Interactive console was not driven end-to-end (no `timeout` on macOS; would require piping input). Verified instead: imports for `run_console`, `render_home`, `render_pilot`, `Screen.PILOT`, and pilot view callable all succeed; no import/runtime crash. Home menu includes option **P** for Pilot; app routes PILOT to `render_pilot`. Console launch and pilot entry are wired; no run-blocking issue found.

---

## 7. Report/doc paths that are real and current

| Path | Exists | Content coherence |
|------|--------|--------------------|
| data/local/release/release_readiness_report.md | Yes | Scope ops, graph/adapter OK, demo readiness, safety boundaries |
| data/local/trials/latest_feedback_report.md | Yes | Trial feedback summary (0 entries in this run); recommendation text |
| data/local/pilot/pilot_readiness_report.md | Yes | Scope, Ready/Safe to demo/Degraded, blocking/warnings, evidence, recommendation |
| data/local/pilot/reliability_issues.json | Yes | Valid JSON; categories must_fix_before_pilot, acceptable_with_warning, post_pilot |
| configs/settings.yaml graph_store_path | Yes | data/local/work_graph.sqlite |
| configs/release_narrow.yaml release_report_dir, trials_output_dir | Yes | data/local/release, data/local/trials |

Scope and readiness in reports match the implemented ops reporting assistant and do not contradict code or command behavior.

---

## 8. Honest narrow-private-pilot readiness verdict

- **Runnable:** Yes. The repo runs through the narrow release + pilot stack in the repo-local venv. Release verify, run, demo and pilot verify, status, latest-report all complete successfully; 34 tests (pilot, release, feedback, trial CLI) pass.
- **Internal founder demo:** Ready. Verify passes; demo runs; report paths exist.
- **One friendly-user run:** Ready. Trial kit, trial tasks, feedback capture, and pilot verify/status are in place; operator can run verify then run/demo then record feedback.
- **Narrow private pilot (2–5 users):** Ready with known limitations. Biggest limitation is **model/UX**: in the run observed, release demo did not pass user/graph context into the prompts, so the model answered generically. That affects perceived usefulness, not command or pipeline failure. Data/setup burden (graph, setup dirs, optional adapter) is documented; path/config stability is sufficient for pilot (paths in configs, report paths wired).

---

## 9. Exact blockers still remaining

- **No run-blocking bugs** found. Release and pilot commands execute; reports generate; console imports and routing work.
- **Product/UX limitation (not a code bug):** Release demo outputs can be generic when the model is not given user/workflow context in the prompt. Improving that is a product/UX task (e.g. inject graph/corpus summary into demo prompts); it does not block running the stack or a narrow pilot.
- **Pilot readiness report:** Was corrected so “Degraded mode: False” is labeled “(adapter available)” instead of “(no adapter; base model only).”

---

## 10. Exact next milestone after this verification pass

- **Next step:** Execute **M21 — Pilot execution and iteration** as in docs/M20_DECISION_OUTPUT.md: run the narrow private pilot with 2–5 users, collect feedback via trial commands and aggregate reports, iterate on reliability and UX from evidence without scope creep. No new architecture or scope expansion; confirm stack runnability and then use it for real pilot sessions.
