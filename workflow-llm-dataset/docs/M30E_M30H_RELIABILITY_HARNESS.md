# M30E–M30H Reliability Harness + Golden Path Recovery

## Overview

Local-first reliability layer that:

1. Defines **golden-path user journeys** (clean install → onboard → workspace; project → plan → approve → simulate; pack install → behavior → workspace query; recovery from blocked upgrade; review inbox → approve → progress).
2. **Validates** those journeys locally via a harness (report-only; no job execution).
3. **Classifies** outcomes: pass / degraded / blocked / fail, with failure step and subsystem.
4. **Supports guided recovery** for common failures (broken pack, failed upgrade, missing runtime, blocked approval, stuck project/agent, invalid workspace).
5. Exposes **CLI** and **mission control** visibility for release confidence.

## Golden paths (built-in)

| path_id | Description |
|--------|-------------|
| `golden_first_run` | Clean install → onboard → first workspace open (acceptance first-value steps). |
| `project_plan_approve_simulate` | Project open → plan compile → approval → simulated execution. |
| `pack_install_behavior_query` | Pack install → behavior resolution → workspace command query. |
| `recovery_blocked_upgrade` | Recovery from blocked upgrade or broken pack state (readiness checks). |
| `review_inbox_approve_progress` | Review inbox → approve/defer → progress update. |

## CLI

- **List golden paths:** `workflow-dataset reliability list`
- **Run a path:** `workflow-dataset reliability run --id golden_first_run` (optional: `--repo-root`, `--no-save`, `--output <file>`)
- **Report (latest):** `workflow-dataset reliability report --latest` (optional: `--output`; use `--all` for list of runs)
- **Suggest recovery:** `workflow-dataset recovery suggest --case broken_pack_state` or `--subsystem packs`
- **Full recovery guide:** `workflow-dataset recovery guide --case failed_upgrade`

## Recovery cases

| case_id | When to use |
|--------|-------------|
| `broken_pack_state` | Pack fails to load, behavior resolution errors, incompatible pack. |
| `failed_upgrade` | Install check fails after upgrade or migration reports errors. |
| `missing_runtime_capability` | Behavior resolution or workspace command query fails (missing runtime). |
| `blocked_approval_policy` | Approval registry missing or policy blocks execution. |
| `stuck_project_session_agent` | Project stalled, replan needed, agent loop not advancing. |
| `invalid_workspace_state` | Workspace context fails to build or active work context invalid. |

## Mission control

The mission control state includes a **reliability** block:

- `golden_path_health`: outcome of latest run (pass / degraded / blocked / fail)
- `recent_regressions`: list of path:subsystem for recent blocked/fail runs
- `top_recovery_case`: suggested recovery case id when latest run is blocked/fail
- `release_confidence_summary`: pass | degraded | blocked_or_fail | no_runs

The mission control report prints a **[Reliability]** line and suggests `reliability list | run | report` and `recovery guide --case <case>`.

## Storage

- Runs: `data/local/reliability/runs/<run_id>.json`
- No remote monitoring or telemetry.

## Constraints

- No cloud monitoring; no automatic remediation (recovery is operator guidance only).
- Harness reuses acceptance journey steps and existing gather APIs; does not replace acceptance or rollout.
- Degraded states are not hidden; release confidence reflects actual outcomes.
