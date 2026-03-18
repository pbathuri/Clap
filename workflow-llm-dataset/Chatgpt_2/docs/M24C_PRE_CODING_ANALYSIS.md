# M24C — Pre-coding analysis (First Real-User Acceptance Harness)

## 1. What install-to-first-value surfaces already exist

- **local_deployment** — `install_check` (run_install_check, format_install_check_report): edge checks + package_readiness; pass/fail, missing_prereqs. `first_run`: ensure dirs, run install-check, run onboarding bootstrap, build first_run_summary. `profile`: build_local_deployment_profile (edge, readiness, trust_summary, product_surfaces), write_deployment_profile, format_deployment_report.
- **onboarding** — bootstrap_profile (machine, adapters, approvals, trusted subset, recommended job packs), onboarding_flow (get_onboarding_status, run_onboarding_flow), product_summary (build_first_run_summary, format_first_run_summary), approval_bootstrap, user_work_profile.
- **operator_quickstart** — quick_reference, first_run_tour (what system can do, simulate-only, approvals, first workflow, how to read trust/runtime/profile), first_value_flow (6 steps: bootstrap, runtime, onboard, job list, inbox, run one simulate), status_card (integrated modules, missing optional, trusted vs simulate, next action).
- **starter_kits** — StarterKit (kit_id, target_field/job_family, domain_pack_id, recommended_job_ids, recommended_routine_ids, first_simulate_only_workflow, first_value_flow, approvals_likely_needed). Built-in: founder_ops_starter, analyst_starter, developer_starter, document_worker_starter. recommend_kit_from_profile, _missing_prerequisites. kits list | recommend | show | first-run.
- **trust** — build_trust_cockpit (benchmark_trust, approval_readiness, job_macro_trust_state, release_gate_status). trust cockpit | release-gates | readiness-report.
- **desktop_bench** — board_report (latest_run_id, trust_status, simulate_only_coverage, trusted_real_coverage), list_runs, get_run, compare_runs. Trusted actions via desktop_bench.trusted_actions.
- **mission_control** — get_mission_control_state (product, eval, dev, incubator, desktop_bridge, job_packs, copilot, work_context, corrections, runtime_mesh, daily_inbox, trust_cockpit, package_readiness, macros), format_mission_control_report, recommend_next_action.
- **package_readiness** — build_readiness_summary (current_machine_readiness, ready_for_first_real_user_install, not_ready_reasons).

No single “acceptance scenario” or “golden journey” runner exists that (1) defines scenarios with expected outcomes, (2) runs a scenario in report-only mode, (3) compares actual state to expected, (4) classifies pass/partial/blocked/fail, (5) produces a readiness-for-real-user report.

---

## 2. What is missing for a real acceptance harness

- **Acceptance scenario schema** — Explicit scenario definitions (e.g. founder_first_run, analyst_first_run, developer_first_run, document_worker_first_run) with: profile assumptions, machine/runtime assumptions, approvals needed, starter kit used, first-value steps, expected outputs, expected blocked behaviors, trust/readiness expectations. Today starter_kits and first_value_flow are separate; no single “scenario” object that ties them and adds expectations.
- **Golden journeys** — Reusable acceptance journeys as ordered steps: install/readiness → bootstrap profile → onboard approvals → select pack → run first simulate → inspect trust → inspect inbox → optionally run one trusted-real if approved. These should be runnable in **report mode** (read-only: gather actual state, no execution of jobs/macros beyond what the harness explicitly runs in a safe way).
- **Acceptance runner** — A harness that: runs a scenario (by id), gathers actual state from existing modules (install_check, onboarding status, trust cockpit, job_packs_report, inbox, mission_control), compares to scenario expectations, classifies outcome (pass / partial / blocked / fail), produces human-readable reasons.
- **Acceptance reports** — Summary report: scenario outcome, where the system succeeded, where it blocked correctly, where it failed unexpectedly, and a single “ready for real-user trial” (yes/no with evidence).
- **CLI** — acceptance list, acceptance run --id <scenario_id>, acceptance report --latest. No auto-run of unsafe real actions; runner may run read-only checks and simulate-only steps if we define that explicitly.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/acceptance/__init__.py` — Public API. |
| Create | `src/workflow_dataset/acceptance/scenarios.py` — Acceptance scenario schema (dataclass or dict): scenario_id, name, profile_assumptions, machine_assumptions, approvals_needed, starter_kit_id, first_value_steps (ordered), expected_outputs, expected_blocked, trust_readiness_expectations. Built-in scenarios: founder_first_run, analyst_first_run, developer_first_run, document_worker_first_run. list_scenarios(), get_scenario(). |
| Create | `src/workflow_dataset/acceptance/journeys.py` — Golden journey definitions: install_readiness, bootstrap_profile, onboard_approvals, select_pack, run_first_simulate, inspect_trust, inspect_inbox, optionally_trusted_real. Each step: step_id, description, gather_actual (function or ref), expected_state (optional). |
| Create | `src/workflow_dataset/acceptance/runner.py` — run_scenario(scenario_id, repo_root, report_only=True): load scenario, run journey steps in report mode (gather actual state from existing APIs, no job/macro execution unless we add an explicit “run simulate” step that invokes jobs run --mode simulate for the kit’s first_simulate_only_workflow). Compare actual vs expected. classify_outcome(actual, expected) -> pass | partial | blocked | fail with reasons. Return run result (scenario_id, outcome, steps_results, reasons, ready_for_trial). |
| Create | `src/workflow_dataset/acceptance/report.py` — format_acceptance_report(run_result): scenario outcome, where succeeded, where blocked correctly, where failed unexpectedly, ready for real-user trial (yes/no + evidence). Write report to file or return string. |
| Create | `src/workflow_dataset/acceptance/storage.py` — Save latest run to data/local/acceptance/runs/ (run_id, scenario_id, outcome, timestamp, steps_results, reasons). load_latest_run(), list_runs(). |
| Modify | `src/workflow_dataset/cli.py` — Add acceptance_group: acceptance list, acceptance run --id <id>, acceptance report [--latest]. |
| Create | `tests/test_acceptance.py` — Scenario definitions, runner outcome classification, expected-vs-actual, blocked behavior handling, report generation, no-data behavior. |
| Create | `docs/M24C_ACCEPTANCE_HARNESS.md` — Usage, sample scenario, sample run output, sample report, safety, what we do not do. |

---

## 4. Safety/risk note

- **Report mode by default** — Acceptance run gathers state via existing read-only APIs (install_check, onboarding status, trust cockpit, job_packs_report, inbox, mission_control). No execution of real actions; optional “run first simulate” step can be implemented by calling existing jobs run --mode simulate or macro run --mode simulate in a subprocess or via existing Python API, with explicit consent (e.g. --include-simulate-run flag). Default: report-only, no job/macro execution.
- **No bypass of trust/approval** — Runner does not create or modify approval registry; does not run real mode. If we add a “run first simulate” step, it runs only simulate mode.
- **Local-only** — All state and reports under data/local/acceptance/. No cloud, no telemetry.
- **Explicit scenarios** — Scenarios and expectations are defined in code/config; no silent inference of “expected” state.

---

## 5. What this phase will NOT do

- **No auto-run of unsafe real actions** — Real mode jobs/macros are not executed by the harness.
- **No bypass of trust/approval policy** — Existing check_job_policy and approval registry remain the gate.
- **No uncontrolled trials** — Acceptance validates readiness for a controlled small rollout; it does not launch or manage trials.
- **No rewrite of deployment/onboarding/trust** — Reuse local_deployment, onboarding, operator_quickstart, starter_kits, trust, package_readiness, mission_control as-is; add only the acceptance scenario schema, runner, and report layer.
