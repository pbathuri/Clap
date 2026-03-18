# M46A–M46D Long-Run Health + Drift Detection

First-draft long-run health layer for sustained deployment: explicit health model, drift detection across execution/memory/routing/operator burden, alert states, and mission-control visibility. Local-first; no remote telemetry.

## Overview

- **Deployment health snapshot**: Window (daily, weekly, rolling_7, rolling_30), subsystem health signals, drift signals, degradation trends, operator burden / memory / routing / execution indicators, and an overall alert state with evidence-backed explanation.
- **Drift detection**: Eight kinds — execution_loop (failure/awaiting ratio), intervention_rate (pause/takeover), queue_calmness, memory_quality (weak cautions), routing_quality (eval revert/hold), takeover_frequency, triage_recurrence (open issues), value_regression (usefulness/cohort). All read from mission_control state.
- **Alert states**: healthy | watch | degraded | repair-needed | rollback-consider | pause-consider. Each has rationale and evidence_refs; optional contradictory flag when evidence is mixed.
- **Persistence**: Snapshots and drift signals under `data/local/long_run_health`. Mission control builds slice in-memory (no mandatory write).

## CLI

- `workflow-dataset health long-run` — Build and show snapshot; optional `--write` to persist, `--window daily|weekly|rolling_7|rolling_30`, `--json`.
- `workflow-dataset health drift-report` — Drift signals from latest snapshot or fresh run; `--window`, `--limit`, `--json`.
- `workflow-dataset health subsystem --id <id>` — Health for one subsystem (e.g. memory_os, queue, execution_loops, operator_burden, triage); `--json`.
- `workflow-dataset health stability-window` — Current window and snapshot summary; `--window`, `--json`.
- `workflow-dataset health explain --id <id>` — Explain drift signal (drift_xxx) or snapshot alert (health_xxx); `--json`.

## Mission control

- State: `long_run_health_state` from `long_run_health_slice()` — current_alert_state, strongest_drift_signal_id, top_degraded_subsystem_id, operator_burden_trend_summary, next_recommended_maintenance, snapshot_id, drift_signal_count, degraded_subsystem_count.
- Report: `[Long-run health]` section with alert, drift_count, degraded, strongest_drift, top_degraded, next maintenance.

## Subsystem IDs

operator_burden, memory_os, routing, execution_loops, queue, triage.

## Remaining gaps (for later)

- Historical baseline comparison (persisted baseline vs current).
- Deployment-cut / vertical-specific snapshot filtering.
- Tunable thresholds per deployment (currently first-draft constants).
