# M30E–M30H Reliability Harness + Golden Path Recovery — Pre-Coding Analysis

## 1. What reliability / acceptance / recovery-like behavior already exists

- **Acceptance (acceptance/)**: Scenarios (founder_first_run, analyst_first_run, etc.) with first_value_steps (install_readiness, bootstrap_profile, onboard_approvals, select_pack, run_first_simulate, inspect_trust, inspect_inbox). Runner: `run_scenario`, `classify_outcome` → pass | partial | blocked | fail. Journeys: `run_journey_steps`, gather_* (read-only state). Storage: save_run, load_latest_run, list_runs. Report: format_acceptance_report. **Does not** cover project→plan→approval→simulate, pack install→behavior→query, or recovery from upgrade/pack/workspace.
- **Rollout (rollout/)**: Readiness report (demo_ready, first_user_ready, blocks, operator_actions). Launcher: `launch_golden_journey(demo_id)` runs acceptance for demo’s scenario, updates rollout state. Tracker: update_rollout_from_acceptance. **Does not** run multiple golden paths or attribute failures to subsystems.
- **Progress recovery (progress/)**: Intervention playbooks (stalled_founder_ops, blocked_analyst_case, etc.) with trigger_pattern, operator_intervention, agent_next_step. `match_playbook`, `build_stalled_recovery` for stalled projects. **Does not** cover broken pack, failed upgrade, missing runtime, invalid workspace.
- **Local deployment**: `run_install_check`, first_run flow. **Does not** drive full golden paths or recovery guides.
- **Distribution readiness**: Aggregates install_check, package_readiness, rollout readiness. **Does not** run journeys or suggest recovery.
- **Desktop bench / eval**: Harnesses for benchmarks and eval suites. **Separate** from product golden-path validation.

So: **existing** = acceptance scenarios + runner + classify, rollout readiness + launcher, progress playbooks for stalled projects, install_check. **Missing** = unified golden-path set beyond first-run acceptance, continuous validation of multiple journeys, failure attribution to subsystems, recovery playbooks for broken_pack / failed_upgrade / missing_runtime / blocked_approval / stuck_agent / invalid_workspace, single reliability CLI and report, mission-control visibility for golden-path health and top recovery action.

---

## 2. What is missing for a true release-grade reliability layer

- **Golden-path set**: Clean install→onboard→workspace open; project open→plan compile→approval→simulated execution; pack install→behavior resolution→workspace query; recovery from blocked upgrade or broken pack; review inbox→approve/defer→progress update. Each path with steps and optional subsystem tags.
- **Reliability harness**: Run one or more golden paths, classify result (pass / degraded / blocked / fail), record where failure occurred and which subsystem, persist runs for regression view.
- **Recovery playbooks**: First-draft cases: broken_pack_state, failed_upgrade, missing_runtime_capability, blocked_approval_policy, stuck_project_session_agent, invalid_workspace_state. For each: suggest (when to use) and guide (step-by-step operator actions).
- **CLI**: reliability list, reliability run --id <path_id>, reliability report --latest; recovery suggest --case <case>, recovery guide --case <case>.
- **Mission control**: Golden-path health summary, recent regressions, degraded-but-usable states, top recommended recovery action, release confidence summary.
- **No remote deps**: All local; no cloud monitoring or telemetry.

---

## 3. Exact file plan

| Area | Action | Path |
|------|--------|------|
| Models | Create | `src/workflow_dataset/reliability/models.py` — GoldenPathScenario (path_id, name, steps, subsystem_tags), ReliabilityRunResult (run_id, path_id, outcome, failure_step_index, subsystem, reasons, timestamp), RecoveryCase (case_id, name, when_to_use, steps_guide) |
| Golden paths | Create | `src/workflow_dataset/reliability/golden_paths.py` — define built-in paths (golden_first_run, project_plan_approve_simulate, pack_install_behavior_query, recovery_blocked_upgrade, review_inbox_approve_progress), get_path(path_id), list_path_ids() |
| Harness | Create | `src/workflow_dataset/reliability/harness.py` — run_golden_path(path_id, repo_root), classify_run_result(steps_results) → outcome + failure_step + subsystem, record run |
| Recovery | Create | `src/workflow_dataset/reliability/recovery_playbooks.py` — RECOVERY_CASES (broken_pack_state, failed_upgrade, missing_runtime, blocked_approval_policy, stuck_project_agent, invalid_workspace_state), suggest_recovery(case_id or auto-detect), get_recovery_guide(case_id) |
| Store | Create | `src/workflow_dataset/reliability/store.py` — save_run, load_latest_run, list_runs, get_reliability_dir |
| Report | Create | `src/workflow_dataset/reliability/report.py` — format_reliability_report(run_result or latest) |
| CLI | Create | `src/workflow_dataset/reliability/cli.py` — cmd_list, cmd_run, cmd_report, cmd_recovery_suggest, cmd_recovery_guide |
| Main CLI | Modify | `src/workflow_dataset/cli.py` — add reliability_group (list, run, report), recovery_group (suggest, guide) or recovery under reliability |
| Mission control | Modify | `src/workflow_dataset/mission_control/state.py` — add reliability block (golden_path_health, recent_regressions, top_recovery_case, release_confidence_summary) |
| Mission control report | Modify | `src/workflow_dataset/mission_control/report.py` — add [Reliability] section |
| Tests | Create | `tests/test_reliability.py` |
| Docs | Create | `docs/M30E_M30H_RELIABILITY_HARNESS.md` |

---

## 4. Safety/risk note

- **Read-only where possible**: Golden-path steps should gather state or call existing acceptance/journey/install_check APIs; avoid executing real jobs/macros in harness unless explicitly “simulate” and gated.
- **No hidden autonomy**: Recovery guides are operator instructions only; no auto-fix without operator running commands.
- **No weakening**: Do not relax approval or trust boundaries; recovery for “blocked approval” means guidance to review policy/approvals, not bypass.
- **Local only**: No telemetry or cloud; all runs and reports local.

---

## 5. What this block will NOT do

- **No cloud monitoring** or remote reliability service.
- **No automatic remediation**: Recovery playbooks output guidance; operator runs commands.
- **No replacement** of acceptance or rollout: reliability layer uses/calls them and adds paths + recovery.
- **No full upgrade/migration implementation**: “Failed upgrade” recovery is guidance only; actual upgrade logic stays in Pane 1 / distribution.
- **No synthetic-only tests**: Golden paths will use real product flows (acceptance journeys, workspace, inbox) where applicable.
