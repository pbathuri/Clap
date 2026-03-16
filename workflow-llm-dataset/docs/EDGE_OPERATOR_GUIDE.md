# Edge Readiness — Operator Guide

How to run edge commands, read reports, and interpret outcomes. All outputs are local (e.g. `data/local/edge/`). No cloud; no hardware device design.

## Quick start

1. **Check your tier:** `workflow-dataset edge profile --tier local_standard`
2. **See workflow support:** `workflow-dataset edge matrix --tier local_standard`
3. **Run a smoke check (readiness only):** `workflow-dataset edge smoke-check --tier local_standard --no-demo`

Sample profiles per tier: [docs/edge/sample_profiles](edge/sample_profiles).

---

## Commands and examples

### Profile

Print runtime, paths, and workflow availability for a tier.

```bash
workflow-dataset edge profile --tier local_standard
workflow-dataset edge profile --tier constrained_edge
```

**What you see:** Tier name, description, LLM requirement, repo root, Python version, supported workflows list, and per-workflow status (supported / degraded / unavailable) with short reason.

---

### Matrix

Generate the workflow support matrix (required/optional deps, workflow status, degraded section).

```bash
# All tiers
workflow-dataset edge matrix --output data/local/edge/all_tiers.md

# One tier (markdown or JSON)
workflow-dataset edge matrix --tier local_standard --output data/local/edge/local_standard_matrix.md
workflow-dataset edge matrix --tier constrained_edge --format json --output data/local/edge/constrained_matrix.json
```

**What you get:** A report with required local dependencies, optional dependencies, a workflow table (workflow | status | reason | missing | fallback), and for degraded tiers a **Degraded workflows** section explaining why each is partial, what is missing, and what fallback is available.

---

### Compare

Compare two tiers (workflow status diff, degraded workflows, path/dependency differences).

```bash
workflow-dataset edge compare --tier local_standard --tier-b constrained_edge
workflow-dataset edge compare --tier local_standard --tier-b constrained_edge --output data/local/edge/compare.md
```

**What you get:** LLM requirement diff, workflow status changes (e.g. supported → degraded), which workflows are degraded in each tier with reason/fallback, and path differences (paths only in first tier, only in second).

---

### Package report

Generate packaging/readiness metadata for a tier (for handoff to deployment or appliance testing).

```bash
workflow-dataset edge package-report --tier local_standard
workflow-dataset edge package-report --tier constrained_edge --format json --output data/local/edge/pkg_constrained.json
```

**What you get:** Required/optional runtime components, supported/degraded/unavailable workflows, local path assumptions (with exists/missing), config assumptions, missing dependency summary, and notes for packaging.

---

### Smoke check

Run readiness checks and optionally workflow demo runs. Use `--no-demo` for readiness-only (fast).

```bash
# Readiness only
workflow-dataset edge smoke-check --tier local_standard --no-demo

# Readiness + workflow demos (weekly_status, status_action_bundle by default)
workflow-dataset edge smoke-check --tier local_standard
workflow-dataset edge smoke-check --tier local_standard --workflow weekly_status --output data/local/edge/smoke.md
```

**What you get:** Console summary (Overall: PASS/FAIL, passed/failed/skipped counts, per-workflow status) and a report file with readiness summary, workflows tested table (workflow | status | message | degraded reason | missing reason), and summary counts.

---

### Degraded report

Explain why workflows are only partially supported, what is missing, and what fallback is available.

```bash
workflow-dataset edge degraded-report --tier constrained_edge
workflow-dataset edge degraded-report --output data/local/edge/degraded.md
```

**What you get:** Per tier (or all tiers with degraded workflows), for each degraded workflow: **Why partial**, **Missing**, **Fallback**.

---

### Readiness and missing-deps

Full readiness report (summary, runtime, sandbox paths, checks, workflows):

```bash
workflow-dataset edge readiness --output data/local/edge/readiness.md
workflow-dataset edge report
```

Missing dependency report (required vs optional failures):

```bash
workflow-dataset edge missing-deps --output data/local/edge/missing.md
```

---

### Continuous readiness checks and drift (M23B-F5)

Detect when the local environment drifts away from a previously healthy readiness state. All behavior is operator-started; no daemon or cloud.

**Record a snapshot (run checks and save to history):**

```bash
workflow-dataset edge check-now
workflow-dataset edge check-now --repo-root /path/to/repo
```

Snapshots are stored under `data/local/edge/history/` (`readiness_<timestamp>.json` and `latest.json`). After running, the CLI suggests running `drift-report` to compare.

**Compare current state to last snapshot (drift report):**

```bash
workflow-dataset edge drift-report
workflow-dataset edge drift-report --output data/local/edge/readiness_drift_report.md
```

The report shows: **Outcome** (current vs previous ready), **What got worse** (checks that passed before and now fail), **What improved**, **Still failing (unchanged)**, and **Next command** (e.g. run `missing-deps` or `check-now`).

**Optional: schedule marker (no daemon):**

To run checks periodically, use cron (or similar) to invoke `check-now`. To record your intended interval and instructions locally:

```bash
workflow-dataset edge schedule-checks --interval-hours 24
```

This writes `data/local/edge/schedule.json` with the interval and a note to run `workflow-dataset edge check-now` from cron. No background process is started; you control when checks run.

---

## How to read degraded-mode output

- **Degraded** means the workflow can run in a reduced way (e.g. baseline only, no adapter/retrieval). It is not “broken”; it is partial.
- In **matrix** and **degraded-report** you get:
  - **Why partial:** Short reason (e.g. “LLM optional; with LLM runs baseline only”).
  - **Missing:** What is not available (e.g. Adapter, Retrieval, Full sandbox).
  - **Fallback:** What you can do (e.g. “Provide LLM config for baseline runs; or use minimal_eval for eval-only”).
- **Smoke check:** If a workflow is skipped with “LLM required but config missing”, add an LLM config (e.g. `configs/llm_training_full.yaml`) or use a tier where LLM is optional and interpret results as baseline-only.

---

## How to interpret missing dependencies

- **Required (must fix):** Checks that must pass for the product to be considered “ready” (e.g. Python version, config exists, core sandbox paths). Fix these first.
- **Optional (feature disabled when missing):** When a check fails but is optional, that feature is disabled (e.g. LLM config, extra paths). The product can still run in a reduced mode.
- **Missing dependency report** lists failed checks under “Required (must fix)” and “Optional (feature disabled when missing)”. Use it together with **readiness** to see the full check list and which failed.

---

## Where outputs go

By default, reports are written under **`data/local/edge/`** (created if missing), for example:

- `edge_readiness_report.md`
- `missing_dependency_report.md`
- `supported_workflow_matrix.md`
- `all_tiers_workflow_matrix.md` or `<tier>_workflow_matrix.md`
- `tier_compare.md`
- `degraded_workflows_report.md` or `<tier>_degraded_report.md`
- `edge_package_report.md` or `edge_package_report_<tier>.md`
- `smoke_check_report.md`
- `readiness_drift_report.md` (from `edge drift-report`)
- `schedule.json` (from `edge schedule-checks`; marker only, no daemon)
- `history/readiness_<timestamp>.json`, `history/latest.json` (from `edge check-now`)

Use `--output` or `-o` to write to a different path. All outputs stay local and inspectable.
