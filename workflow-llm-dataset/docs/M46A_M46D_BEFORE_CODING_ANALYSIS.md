# M46A–M46D Before-Coding Analysis — Long-Run Health + Drift Detection

## 1. What health/reliability state already exists

- **reliability/** (M30E–M30H): Golden-path runs, `ReliabilityRunResult` (pass/degraded/blocked/fail), recovery playbooks, degraded mode profiles, fallback matrix. Point-in-time harness runs, not sustained drift.
- **deploy_bundle/health.py**: Deployment health summary (validation, upgrade/rollback readiness, recovery posture, blocked risks). Bundle-level, not long-run trend.
- **triage/health.py**: Cohort health summary (open issues, severity, recommended mitigation/downgrade). Support/triage view.
- **state_durability/**: Startup health, maintenance profiles, compaction. Durability/maintenance, not execution/memory/routing drift.
- **long_run_health/** (M46A–M46D, **already present**):
  - **Models**: `DeploymentHealthSnapshot`, `SubsystemHealthSignal`, `DriftSignal`, `DegradationTrend`, `StabilityWindow`, `OperatorBurdenIndicator`, `MemoryQualityIndicator`, `RoutingQualityIndicator`, `ExecutionReliabilityIndicator`, `AlertState` (healthy, watch, degraded, repair-needed, rollback-consider, pause-consider), `AlertStateExplanation`.
  - **Drift detection**: `execution_loop_drift`, `intervention_rate_drift`, `queue_calmness_drift`, `memory_quality_drift`, `routing_quality_drift`, `takeover_frequency_drift`, `triage_recurrence_drift`, `value_regression_drift`; `collect_drift_signals`. All read from mission_control state.
  - **Indicators**: `operator_burden_from_state`, `memory_quality_from_state`, `routing_quality_from_state`, `execution_reliability_from_state`, `build_subsystem_health_signals`.
  - **Alert classification**: `classify_alert_state` with evidence-backed rationale.
  - **Snapshot**: `build_deployment_health_snapshot(window_kind, repo_root, vertical_id)`.
  - **Store**: `save_snapshot`, `load_snapshot`, `list_snapshots`, `save_drift_signal`, `load_drift_signal`, `list_drift_signals`, `get_health_dir`.
  - **Reports**: `format_long_run_report`, `format_drift_report`, `format_subsystem_health`, `format_alert_explanation`.
  - **Mission control**: `long_run_health_slice` (current_alert_state, strongest_drift_signal_id, top_degraded_subsystem_id, operator_burden_trend_summary, next_recommended_maintenance).
- **CLI**: `workflow-dataset health long-run`, `health drift-report`, `health subsystem --id <id>`, `health stability-window`, `health explain --id <drift_xxx|health_xxx>`.
- **mission_control/state.py**: Includes `long_run_health_state` from `long_run_health_slice`.
- **mission_control/report.py**: Formats `[Long-run health]` with alert, drift_count, degraded, strongest_drift, top_degraded, next maintenance.

## 2. What is missing for long-run drift detection

- **Historical baseline**: Drift uses current mission_control state only; no persisted baseline (e.g. “7 days ago”) to compare against. Thresholds are hardcoded (e.g. fail_ratio &gt; 0.3, calmness &lt; 0.5). Acceptable for first-draft.
- **Stability window dates**: `StabilityWindow` has `start_iso`/`end_iso` but they are not set from actual time range when building snapshot; only `kind` and `label` are used.
- **Contradictory evidence**: `AlertStateExplanation.contradictory` exists but is never set `True`; no path when evidence is mixed (e.g. some subsystems ok, others high-severity drift).
- **Deployment-cut / vertical-specific view**: Snapshot has `vertical_id` but no filtering of state by vertical or deployment cut; single global snapshot.
- **Explicit “no drift” / “weak signal” tests**: Tests exist for healthy and for drift firing; explicit no-drift empty state and weak-signal (watch-only) edge cases could be clearer.
- **Doc**: No single doc that describes the long-run health layer, CLI, and mission-control integration for operators.

## 3. Exact file plan

- **No new packages.** Extend existing `long_run_health` and tests/docs only.
- **tests/test_long_run_health.py**: Add `test_no_drift_empty_state` (minimal state, zero drift, healthy), `test_weak_signal_watch_only` (warnings only, no drift → watch), `test_alert_state_contradictory` (optional: set contradictory when both healthy subsystems and high drift exist).
- **long_run_health/alert_state.py**: Optionally set `contradictory=True` in explanation when e.g. some subsystems are ok but there is at least one high-severity drift (first-draft heuristic).
- **long_run_health/snapshot.py**: Optionally set `window.start_iso` / `window.end_iso` from current time and window kind (e.g. rolling_7 → now minus 7 days to now).
- **docs/M46A_M46D_LONG_RUN_HEALTH.md**: New doc — overview, drift kinds, alert states, CLI usage, mission control slice, sample outputs, remaining gaps.
- **docs/M46A_M46D_DELIVERABLE.md**: Final deliverable (files modified/created, CLI, sample snapshot, sample drift report, sample degraded explanation, tests run, remaining gaps).

## 4. Safety/risk note

- **Local-first preserved**: All data from mission_control state and local stores; no remote telemetry. Snapshots and drift signals persisted under `data/local/long_run_health`.
- **No weakening of trust**: Alert states are advisory (repair-needed, rollback-consider, pause-consider); no automatic rollback or pause. Operator retains control.
- **Uncertainty visible**: Rationale and evidence_refs on every alert explanation; confidence (low/medium/high) and contradictory flag surface ambiguity.
- **Risk**: Thresholds (e.g. fail_ratio 0.3, calmness 0.5) are first-draft; may need tuning per deployment. Document as such.

## 5. Drift-detection principles

- **Evidence-tied**: Every drift signal and alert state has evidence_refs (e.g. adaptive_execution_state, signal_quality). No hidden scoring.
- **Read-only aggregation**: Drift and indicators derive from existing mission_control state and stores; no new write paths for production data.
- **Explainable**: Each alert state has a rationale and optional contradictory flag; operators can run `health explain --id <id>`.
- **Subsystem-scoped**: Drift is per kind (execution_loop, queue_calmness, memory_quality, etc.) and subsystem_id; supports subsystem health view.
- **Window-aware**: Signals carry window_kind (daily, weekly, rolling_7, rolling_30); snapshot built for a single window.
- **No overfit to one subsystem**: Eight drift kinds across execution, intervention, queue, memory, routing, takeover, triage, value.

## 6. What this block will NOT do

- **No remote telemetry or cloud monitoring.** All data local.
- **No automatic rollback, pause, or repair.** Only recommend (next_recommended_maintenance).
- **No replacement of reliability harness, deploy_bundle health, or triage health.** Long-run health is an additional layer that aggregates and trends.
- **No historical time-series storage** (e.g. daily metrics DB). Only snapshots and drift signal files; no baseline comparison across time yet.
- **No deployment-cut or multi-vertical filtering** in this first draft; single global snapshot per repo.
