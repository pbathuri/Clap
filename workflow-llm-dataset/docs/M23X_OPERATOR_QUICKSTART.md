# M23X — First-Run Operator Quickstart + Guided Product Tour

## Purpose

Make the integrated product (M23T + M23U + M23V) understandable to a first real operator by providing:

- **Operator quick reference** — One-page map of dashboard, profile, onboard, jobs, copilot, inbox, trust, runtime, mission-control with key commands.
- **Guided first-run tour** — What the system can do now, what is simulate-only, what approvals matter, recommended first workflow, how to interpret trust/runtime/profile.
- **First-value flow** — Ordered steps: bootstrap profile → check runtime → onboard approvals → show recommended job → show inbox → run one safe simulate-only routine (suggested; no auto-run).
- **Product status card** — Integrated modules available, missing optional pieces, trusted-real vs simulate-only coverage, current recommended next action.

All outputs are **local**, **read-only** (except where operator runs suggested commands), and **no new permissions or auto-run**.

---

## CLI usage

| Command | Description |
|--------|-------------|
| `workflow-dataset quickstart quickref` | Print operator quick reference (optionally `--output FILE`, `--markdown`). |
| `workflow-dataset quickstart tour` | Print guided first-run tour (optionally `--repo-root`, `--output FILE`). |
| `workflow-dataset quickstart first-value` | Print first-value flow steps (optionally `--repo-root`, `--output FILE`). |
| `workflow-dataset quickstart status-card` | Print product status card (optionally `--repo-root`, `--output FILE`). |

---

## Sample quick-reference output (excerpt)

```
Operator quick reference (M23X). All commands under workflow-dataset. Local-only; no auto-run.

  dashboard: Command center: workspaces, packages, cohort, apply-plan, next action.
    · workflow-dataset dashboard
    · dashboard workspace
    · dashboard package
    · dashboard action

  profile: User work profile and bootstrap: field, job family, operator summary.
    · workflow-dataset profile bootstrap
    · profile show
    · profile operator-summary
  ...
  mission-control: Unified dashboard: product, eval, dev, inbox, trust, runtime; recommended next action.
    · workflow-dataset mission-control
    · mission-control --output path
```

---

## Sample first-run tour output (excerpt)

```
=== First-run guided tour (M23X) ===

--- What the system can do now ---
  · Run all adapters in simulate mode (no real writes or app control).
  · Use the operator console (workflow-dataset console) for setup, suggestions, materialize, apply with confirmation.
  ...

--- What is still simulate-only ---
  · Adapters or actions marked simulate-only cannot perform real writes or app control; they only simulate.
  · Jobs and routines can run in --mode simulate without any approval; real mode requires approval registry and trusted actions.
  ...

--- Recommended first workflow ---
  workflow-dataset onboard bootstrap
  ...
--- How to interpret trust ---
  Trust cockpit (workflow-dataset trust cockpit) shows: benchmark trust status, whether the approval registry exists, ...
```

---

## Sample first-value flow output (excerpt)

```
First-value flow (M23X). Run steps in order. Steps marked run_read_only can be executed by the quickstart; others are suggested only.

  Step 1: Bootstrap profile
    Create or refresh user work profile and bootstrap profile.
    Command: workflow-dataset profile bootstrap
    Then: workflow-dataset profile show

  Step 2: Check runtime mesh
    See available backends and recommended model classes.
    Command: workflow-dataset runtime backends
  ...
  Step 6: Run one safe simulate-only routine
    Run a job or routine in simulate mode (no real execution; no approval required).
    Command: workflow-dataset jobs run <job_id> --mode simulate
    Note: Replace <job_id> with a job from 'jobs list' or use the recommended first workflow above.
```

---

## Sample product status card output (excerpt)

```
=== Product status card (M23X) ===

--- Integrated modules available ---
  product_state, desktop_bridge, job_packs, copilot, work_context, runtime_mesh, daily_inbox, trust_cockpit, package_readiness

--- Missing optional pieces ---
  incubator

--- Trusted-real vs simulate-only ---
  Trusted for real: 0. Simulate-only jobs: 0. Real execution requires approval registry.

--- Recommended next action ---
  action: hold
  rationale: No urgent signal; review mission-control state and choose next step.
  ...
(Run workflow-dataset mission-control for full report.)
```

---

## Safety and constraints

- **No hidden permissions** — Quick reference, tour, first-value flow, and status card do not add or assume any approvals.
- **No auto-run of workflows** — First-value flow only suggests commands; the operator runs them explicitly.
- **No rewrite of dashboard or mission-control** — Existing modules are reused; quickstart only aggregates and formats.
- **Local-only** — All data from existing local sources; no cloud, no telemetry.

---

## Tests

Run:

```bash
pytest tests/test_operator_quickstart.py -v
```

Covers: quick reference generation, first-run tour content, first-value flow steps, status card structure and format, no-data/partial-setup behavior.

---

## Next step for the pane

- **Optional:** Add a “Quickstart” or “Tour” entry in the operator console TUI (e.g. menu option that runs the same tour/quickref or opens the first-value flow) so first-run operators can discover it from the console as well as the CLI.
- **Stabilize incubator:** If not already done, guard or stub `workflow_dataset.incubator` so mission-control (and status card) runs without an incubator error when the module is absent.
