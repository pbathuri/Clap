# M24F–M24I — Rollout / Demo / Support Productization Block — Pre-coding analysis

## 1. What rollout / acceptance / deployment surfaces already exist

- **local_deployment** — install_check, first_run (dirs, install-check, onboarding bootstrap, first_run_summary), profile (build_local_deployment_profile, write_deployment_profile).
- **onboarding** — bootstrap_profile, onboarding_flow, get_onboarding_status, product_summary, approval_bootstrap, user_work_profile.
- **operator_quickstart** — quickref, tour, first-value (6 steps), status-card.
- **acceptance** — Scenarios (founder_first_run, analyst_first_run, developer_first_run, document_worker_first_run), journeys (install_readiness … inspect_inbox), runner (run_scenario, classify_outcome), report, storage (save_run, load_latest_run, list_runs). CLI: acceptance list | run --id | report.
- **trust** — build_trust_cockpit (benchmark_trust, approval_readiness, release_gate_status). CLI: trust cockpit | release-gates | readiness-report.
- **package_readiness** — build_readiness_summary (machine_ready, ready_for_first_real_user_install, experimental, not_ready_reasons). CLI: package readiness-report.
- **mission_control** — get_mission_control_state (product, eval, dev, incubator, desktop_bridge, job_packs, copilot, work_context, corrections, runtime_mesh, daily_inbox, trust_cockpit, package_readiness, environment_health, starter_kits, external_capabilities, value_packs, acceptance, **rollout**). format_mission_control_report, recommend_next_action.
- **starter_kits** — BUILTIN_STARTER_KITS, recommend_kit_from_profile, list_kits, get_kit. CLI: kits list | recommend | show | first-run.
- **rollout (M24F already present)** — demos (GuidedDemo, list_demos, get_demo), launcher (launch_golden_journey), tracker (load/save_rollout_state, update_rollout_from_acceptance), support_bundle (build_support_bundle, build_support_bundle_summary_only), issues (format_issues_report). CLI: rollout demos list | launch --id | status | support-bundle | issues report. Mission control: [Rollout] section (rollout_status, demo_readiness, blocked_rollout_items, support_bundle_freshness, next_rollout_action).

---

## 2. What is missing for a coherent first-draft rollout system

- **Unified go/no-go readiness report (Phase E)** — A single operator-facing report that answers: (1) Is this system **demo-ready**? (2) Is this system **first-user-ready**? (3) What **blocks** rollout? (4) What **operator actions** are required? (5) What remains **experimental**? Today package_readiness and trust have their own readiness reports; rollout state and acceptance are separate. No single `workflow-dataset rollout readiness` that aggregates these into one go/no-go view.
- **CLI** — Add `workflow-dataset rollout readiness` [--output FILE].
- **Tests/docs** — Focused tests for readiness report generation and blocked-state handling; doc sample readiness report and remaining gaps.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/rollout/readiness.py` — build_rollout_readiness_report(repo_root): aggregate rollout state, package_readiness, acceptance, trust_cockpit, environment_health → demo_ready, first_user_ready, blocks, operator_actions, experimental; format_rollout_readiness_report() → string. |
| Modify | `src/workflow_dataset/rollout/__init__.py` — Export build_rollout_readiness_report, format_rollout_readiness_report. |
| Modify | `src/workflow_dataset/cli.py` — Add rollout readiness [--output FILE]. |
| Modify | `tests/test_rollout.py` — Add test_readiness_report_generation, test_readiness_report_blocked_state. |
| Modify | `docs/M24F_ROLLOUT_MANAGER.md` — Add sample readiness report, exact CLI, remaining gaps section. |

---

## 4. Safety/risk note

- **Local-only** — Readiness report uses only local state; no cloud or telemetry.
- **Advisory** — Report is go/no-go guidance for the operator; it does not change state or bypass acceptance/trust.
- **No new execution** — Readiness aggregates existing mission_control/rollout/package_readiness/acceptance data; no auto-run of jobs or real mode.

---

## 5. What this block will NOT do

- No cloud customer-success tooling or remote telemetry.
- No rewrite of deployment, onboarding, acceptance, or trust systems.
- No auto-execution of trusted-real actions.
- No polish/optimization pass; first-draft only. Remaining gaps documented for later refinement.
