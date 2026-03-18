# M24F — Pre-coding analysis (Guided Rollout Manager + Demo/Support Ops)

## 1. What rollout / deployment / acceptance surfaces already exist

- **local_deployment** — install_check, first_run (ensure dirs, install-check, onboarding bootstrap, first_run_summary), profile (build_local_deployment_profile, write_deployment_profile). Package group: first-run, profile, install-check.
- **onboarding** — bootstrap_profile, onboarding_flow (get_onboarding_status, run_onboarding_flow), product_summary, approval_bootstrap, user_work_profile.
- **operator_quickstart** — quickref, tour, first-value (6 steps: bootstrap, runtime, onboard, job list, inbox, run one simulate), status-card.
- **acceptance** — Scenarios (founder_first_run, analyst_first_run, developer_first_run, document_worker_first_run), journeys (install_readiness … inspect_inbox), runner (run_scenario, classify_outcome), report, storage (save_run, load_latest_run, list_runs). CLI: acceptance list | run --id | report.
- **trust** — build_trust_cockpit (benchmark_trust, approval_readiness, release_gate_status). trust cockpit | release-gates | readiness-report.
- **package_readiness** — build_readiness_summary (machine_ready, ready_for_first_real_user_install).
- **mission_control** — get_mission_control_state (product, eval, dev, incubator, desktop_bridge, job_packs, copilot, work_context, corrections, runtime_mesh, daily_inbox, trust_cockpit, package_readiness, macros, environment_health, starter_kits, external_capabilities, value_packs, acceptance), format_mission_control_report, recommend_next_action.
- **starter_kits** — BUILTIN_STARTER_KITS (founder_ops_starter, analyst_starter, developer_starter, document_worker_starter), recommend_kit_from_profile, list_kits, get_kit. kits list | recommend | show | first-run.

No dedicated **rollout** surface: no guided demo definitions, no golden-journey launcher, no rollout-stage tracker, no support-bundle or issue-report generator, and no mission_control section for rollout status/demo readiness/blocked items/bundle freshness.

---

## 2. What is missing for real demo and first-user support

- **Guided demo flows** — Reusable demo definitions (e.g. founder_demo, analyst_demo) with: required pack (starter_kit_id), required capabilities, recommended sample assets, expected outputs, trust/readiness notes, ordered demo steps. Acceptance scenarios are validation-oriented; demos are operator-facing “run this to show the product.”
- **Golden journey launcher** — Single entry that runs the same journey as acceptance (install → bootstrap → onboard → select pack → run first simulate → inspect trust → inspect inbox → next step) in a **launch** flow (e.g. run acceptance run + print next step, or run first_run + quickstart first-value). Today operator must run acceptance and quickstart separately.
- **Rollout tracker** — Persisted state: target user/scenario, current rollout stage, passed readiness checks, blocked items, support notes, next required action, latest acceptance result. Stored under data/local/rollout/ so operator and support bundle can read it.
- **Support bundle / issue bundle** — Single command that collects: environment health, runtime mesh summary, starter kit (value pack) state, latest acceptance result, trust state, paths to last reports/manifests, and an issue-summary template. Output to a directory or tarball for local handoff.
- **CLI** — rollout demos list, rollout launch --id founder_demo, rollout status, rollout support-bundle, rollout issues report. No such group today.
- **Mission control hooks** — Additive section: rollout_status (current stage, target scenario), demo_readiness (ready/blocked), blocked_rollout_items, support_bundle_freshness (last generated path/time), next recommended operator action for rollout.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/rollout/__init__.py` — Public API. |
| Create | `src/workflow_dataset/rollout/demos.py` — Demo definition schema and built-in demos (founder_demo, analyst_demo, developer_demo, document_worker_demo): demo_id, name, required_pack (starter_kit_id), required_capabilities, recommended_sample_assets, expected_outputs, trust_readiness_notes, demo_steps. list_demos(), get_demo(). |
| Create | `src/workflow_dataset/rollout/launcher.py` — launch_golden_journey(demo_id or scenario_id, repo_root): run acceptance run for matching scenario, then return/print next step (quickstart first-value style). No execution of real actions. |
| Create | `src/workflow_dataset/rollout/tracker.py` — Rollout state: target_scenario_id, current_stage, passed_checks, blocked_items, support_notes, next_required_action, latest_acceptance_result (ref or summary). load_rollout_state(), save_rollout_state(), update_rollout_from_acceptance(). Persist under data/local/rollout/rollout_state.json. |
| Create | `src/workflow_dataset/rollout/support_bundle.py` — build_support_bundle(repo_root, output_dir): gather environment_health, runtime_mesh summary, starter_kits state, latest acceptance result, trust state, copy/write paths to last reports (deployment report, acceptance report, mission_control output), issue_summary template; write to output_dir. Return summary dict. |
| Create | `src/workflow_dataset/rollout/issues.py` — format_issues_report(bundle_summary or state): template for issue description (environment, runtime, pack state, acceptance outcome, trust, steps to reproduce). |
| Modify | `src/workflow_dataset/cli.py` — Add rollout_group: rollout demos list, rollout launch --id &lt;demo_id&gt;, rollout status, rollout support-bundle [--output DIR], rollout issues report [--output FILE]. |
| Modify | `src/workflow_dataset/mission_control/state.py` — Add try/except block: rollout (rollout_status, demo_readiness, blocked_rollout_items, support_bundle_freshness, next_rollout_action). |
| Modify | `src/workflow_dataset/mission_control/report.py` — Add [Rollout] section from state. |
| Create | `tests/test_rollout.py` — Demo definitions, launcher (no execution), tracker load/save/update, support bundle creation, issues report format, mission_control rollout block. |
| Create | `docs/M24F_ROLLOUT_MANAGER.md` — Usage, sample demo, rollout status, support bundle summary, issue report, safety, next step. |

---

## 4. Safety/risk note

- **Local-only** — All rollout state and support bundles under data/local/rollout/ and operator-specified output dirs. No cloud, no telemetry.
- **No auto-run of trusted-real** — Launcher and demos do not execute real mode; they run acceptance (report mode) and/or suggest commands. Support bundle only gathers existing reports and state.
- **No bypass** — Acceptance and trust gates unchanged; rollout tracker reflects acceptance result, it does not override it.
- **Inspectable** — Rollout state and support bundle contents are files the operator can review and share under their control.

---

## 5. What this phase will NOT do

- **No cloud admin or remote telemetry** — Rollout and support bundle stay local and operator-controlled.
- **No broad customer-success platform** — Only local operator rollout discipline and first-user support artifacts.
- **No rewrite of acceptance/local_deployment** — Reuse acceptance, local_deployment, quickstart, starter_kits, trust, package_readiness; add rollout layer and mission_control hooks only.
- **No auto-execution of real actions** — Launch runs acceptance in report mode and suggests next steps; it does not run jobs/macros in real mode.
