# M24F–M24I — Guided Rollout Manager + Demo/Support Ops

Local operator layer for guided demos, golden journey launch, pilot rollout tracking, support/issue bundles, go/no-go readiness, and first-draft operator support. No cloud; no telemetry; evidence-driven.

## CLI usage

```bash
# List guided demos
workflow-dataset rollout demos list

# Launch golden journey for a demo (runs acceptance, updates rollout state, prints next step)
workflow-dataset rollout launch --id founder_demo
workflow-dataset rollout launch --id analyst_demo --repo-root /path/to/repo

# Rollout status
workflow-dataset rollout status
workflow-dataset rollout status --repo-root /path/to/repo

# Build support bundle (writes to data/local/rollout/support_bundle_<timestamp> or --output)
workflow-dataset rollout support-bundle
workflow-dataset rollout support-bundle --output /tmp/bundle

# Go/no-go readiness report (demo-ready, first-user-ready, blocks, operator actions, experimental)
workflow-dataset rollout readiness
workflow-dataset rollout readiness --output /tmp/readiness.txt

# Issue report (from current state; no bundle dir created)
workflow-dataset rollout issues report
workflow-dataset rollout issues report --output /tmp/issue.txt

# Operator runbooks (how to run demos, recover, interpret bundles, go/no-go, escalate)
workflow-dataset rollout runbooks list
workflow-dataset rollout runbooks show operator_runbooks
workflow-dataset rollout runbooks show recovery_escalation
```

## Sample demo definition

```python
# founder_demo (from rollout.demos)
demo_id: founder_demo
name: Founder / operator demo
required_pack: founder_ops_starter
required_capabilities: ["config_exists", "edge_checks", "approval_registry_optional"]
demo_steps: ["install_readiness", "bootstrap_profile", "onboard_approvals", "select_pack", "run_first_simulate", "inspect_trust", "inspect_inbox", "next_step"]
```

## Sample golden journey output

After `workflow-dataset rollout launch --id founder_demo` (success path):

```
Outcome: pass
Next step: Product ready for trial. Run 'workflow-dataset inbox' for daily digest; consider 'workflow-dataset kits first-run --id founder_ops_starter' for first-value flow.
```

When partial or blocked, next_step will point to fixing issues and re-running acceptance.

## Sample rollout status output

```
Target scenario: founder_first_run
Current stage: ready_for_trial
Passed checks: ['acceptance_pass']
Blocked: []
Next action: Proceed to first real user / pilot; run inbox and first-value flow as needed.
Latest acceptance: pass ready_for_trial= True
```

## Sample readiness report

After `workflow-dataset rollout readiness` (or with pass state):

```
=== Rollout readiness (go/no-go) ===

[Demo-ready] YES
  Rollout stage ready_for_trial and latest acceptance pass.

[First-user-ready] NO
  Not ready: Release readiness report missing (run: workflow-dataset release report).
  Acceptance not ready for trial; re-run acceptance for target scenario.

[Blocks]
  - Release readiness report missing (run: workflow-dataset release report).

[Operator actions]
  - Proceed to first real user / pilot; run inbox and first-value flow as needed.
  - Run 'workflow-dataset package readiness-report' and fix missing prerequisites.

[Experimental / advisory]
  - Macros/routines: run in simulate first; real mode requires approvals.
  - Corrections and propose-updates: operator review required before apply.

(Local-only. No automatic changes.)
```

When blocked (e.g. rollout stage blocked, acceptance fail):

```
[Demo-ready] NO
  Latest acceptance outcome: blocked (need pass).
  Rollout stage: blocked (need ready_for_trial). Run 'workflow-dataset rollout launch --id founder_demo'.

[Blocks]
  - Rollout: Install check did not pass.
  - Rollout: Missing: config file
```

## Sample support bundle summary

After `workflow-dataset rollout support-bundle`:

- **output_dir**: `data/local/rollout/support_bundle_2025-03-16T12-00-00`
- **Files**: `environment_health.json`, `runtime_mesh.json`, `starter_kits.json`, `latest_acceptance.json`, `trust_cockpit.json`, `rollout_state.json`, `issue_summary.txt`, optional copies of latest acceptance runs.

## Sample issue report

```
--- Support / issue summary (local operator bundle) ---

Environment:
  required_ok: True
  optional_ok: True
  python_version: 3.11

Latest acceptance:
  scenario_id: founder_first_run
  outcome: pass
  ready_for_trial: True

Rollout state:
  target_scenario_id: founder_first_run
  current_stage: ready_for_trial
  next_required_action: Proceed to first real user / pilot...

Steps to reproduce / operator actions:
  1. workflow-dataset rollout status
  2. workflow-dataset acceptance report
  3. workflow-dataset trust cockpit
  4. workflow-dataset mission-control

--- End of issue summary ---
```

## Mission control

`workflow-dataset mission-control` includes a **[Rollout]** section:

- status, target scenario, demo_readiness
- blocked rollout items
- support_bundle freshness (latest support_bundle_* dir)
- next recommended operator action

## Safety

- All state and bundles under `data/local/rollout/` or operator-specified paths.
- Launcher runs acceptance in report mode only; no job/macro execution.
- No remote telemetry or cloud dependency.

## Tests run

```bash
pytest tests/test_rollout.py -v
```

Covers: demo definitions, tracker load/save/update_from_acceptance, support bundle creation and summary-only, issues report format, launcher (unknown demo + founder_demo), mission_control rollout block, **readiness report generation**, **readiness report blocked-state handling**.

## Operator runbooks (M24I.1)

First-draft runbooks live in **docs/rollout/**:

- **OPERATOR_RUNBOOKS.md** — How to run demos, recover from blocked rollout, interpret support bundles, decide go/no-go, escalate/defer; includes sample recovery path and escalation decision tree.
- **RECOVERY_ESCALATION.md** — Quick reference: recovery steps and escalation decision tree.

View from CLI: `workflow-dataset rollout runbooks list` and `workflow-dataset rollout runbooks show operator_runbooks` (or `recovery_escalation`).

## Remaining gaps for later refinement

- **Multi-scenario rollout**: Track multiple target scenarios or pilot users in one state; today single target_scenario_id.
- **Support bundle tarball**: Option to produce a single .tar.gz for handoff instead of only a directory.
- **Readiness history**: Record readiness snapshots over time (e.g. data/local/rollout/readiness_history/) for drift.
- **Demo step-by-step runner**: Interactive or scripted step-by-step execution of demo_steps (e.g. run install_readiness, then bootstrap, then …) with pause/resume; today launch runs full acceptance in one go.
- **Starter-kit vs value_pack**: Rollout demos use starter_kit_id; if value_packs package is present, optionally show value_pack readiness in readiness report and support bundle.
- **Polish**: Richer formatting (e.g. Rich tables for readiness), optional JSON output for rollout readiness, and tighter integration of trust release gates into first_user_ready criteria.

## Next step for the pane

- Run `workflow-dataset rollout demos list` and `workflow-dataset rollout launch --id founder_demo` from repo root.
- Run `workflow-dataset rollout status` and `workflow-dataset mission-control` to confirm Rollout section.
- Run `workflow-dataset rollout support-bundle` and inspect `data/local/rollout/support_bundle_*`.
- Run `workflow-dataset rollout issues report --output /tmp/issue.txt` and open the file.
- Run `workflow-dataset rollout readiness` and optionally `workflow-dataset rollout readiness --output data/local/rollout/readiness_report.txt`.
