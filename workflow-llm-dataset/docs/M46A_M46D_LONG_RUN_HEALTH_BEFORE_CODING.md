# M46A–M46D — Long-Run Health Model + Drift Detection: Before Coding

## 1. What health/reliability state already exists

- **reliability/*:** Golden-path runs, `ReliabilityRunResult` (outcome pass/degraded/blocked/fail), recovery playbooks, degraded-mode profiles, fallback matrix. Per-run outcomes; no sustained trend or drift.
- **production_cut/*:** Production cut, vertical lock, surface freeze, production readiness note (blockers, warnings). Snapshot of scope, not time-series health.
- **stability_reviews/*:** Sustained deployment review, `StabilityWindow`, `EvidenceBundle` (health_summary, drift_signals list, repair_history_summary, operator_burden, vertical_value_retention, etc.), continue/narrow/repair/pause/rollback recommendations. **Expects** drift_signals but does not produce them.
- **repair_loops/*:** Bounded repair plans, signal→pattern mapping (`drift` + subsystem → e.g. queue_calmness_retune, memory_curation_refresh). **Expects** drift signal ids (e.g. drift_123); no module currently creates/store those.
- **mission_control/state.py:** Aggregates product_state, evaluation_state, shadow_execution_state, adaptive_execution_state, supervisory_control_state, signal_quality (calmness_score, noise_level), triage, repair_loops_state, stability_reviews, etc. Read-only aggregation; no explicit “deployment health” or “strongest drift” field.
- **signal_quality/*:** Calmness score, noise level, suppressed count, focus protected. Point-in-time queue quality; no trend or drift.
- **triage/*:** UserObservedIssue, IssueCluster, MitigationPlaybook, cohort evidence. Issue state; no explicit “recurrence” or “regression” metric over time.
- **memory_intelligence/*:** Recommendations, retrieval; store has list_recent. No explicit “memory quality” or “retrieval usefulness” trend.
- **adaptive_execution, shadow_execution, supervisory_control:** Loop/takeover state. No aggregated “execution reliability” or “intervention rate” over a window.
- **release/*, deploy_bundle/*, operator_mode/*, background_run/*, benchmark_board/*, learning_lab/*, council/*:** Each has state/reports; none define a unified “subsystem health” or “degradation trend” for long-run use.

## 2. What is missing for long-run drift detection

- **Explicit long-run health model:** No single “deployment health snapshot” that combines subsystem health signals, stability window, and alert state.
- **Structured drift signals:** No first-class `DriftSignal` (id, kind, subsystem, severity, evidence, window). EvidenceBundle.drift_signals are strings; repair_loops expect drift ids but nothing produces/stores them.
- **Degradation trend:** No “trend over window” (e.g. execution success rate declining, calmness declining, intervention rate rising) with explainable evidence.
- **Subsystem health signals:** No unified “subsystem health” view (memory_os, queue, execution_loops, routing, operator_burden, triage, value) with a score or status per subsystem.
- **Alert state classification:** No single place that maps evidence → healthy | watch | degraded | repair-needed | rollback-consider | pause-consider with rationale and evidence refs.
- **Drift detection implementations:** No code that computes drift in: execution loop success/failure, intervention rate, queue calmness/noise regression, memory retrieval usefulness, routing quality, operator takeover frequency, triage issue recurrence, first-value/vertical-value regression.
- **Persistence for health/drift:** No store for health snapshots and drift signals (so stability_reviews and repair_loops can consume them).
- **Mission control slice:** No slice that exposes “current deployment health”, “strongest drift signal”, “top degraded subsystem”, “operator burden trend”, “next recommended maintenance”.

## 3. Exact file plan

| File | Purpose |
|------|--------|
| `src/workflow_dataset/long_run_health/__init__.py` | Package exports. |
| `src/workflow_dataset/long_run_health/models.py` | DeploymentHealthSnapshot, SubsystemHealthSignal, DriftSignal, DegradationTrend, StabilityWindow (reuse or alias), OperatorBurdenIndicator, MemoryQualityIndicator, RoutingQualityIndicator, ExecutionReliabilityIndicator; AlertState enum (healthy, watch, degraded, repair_needed, rollback_consider, pause_consider); AlertStateExplanation. |
| `src/workflow_dataset/long_run_health/drift_detection.py` | Functions to compute drift: execution_loop_drift, intervention_rate_drift, queue_calmness_drift, memory_quality_drift, routing_quality_drift, takeover_frequency_drift, triage_recurrence_drift, value_regression_drift. Each returns a DriftSignal or None; uses mission_control state, reliability store, adaptive/shadow/supervisory, signal_quality, memory_intelligence, triage, etc. (read-only). |
| `src/workflow_dataset/long_run_health/indicators.py` | Build subsystem health indicators from existing state: operator_burden_from_state, memory_quality_from_state, routing_quality_from_state, execution_reliability_from_state (from adaptive/shadow/reliability). |
| `src/workflow_dataset/long_run_health/snapshot.py` | build_deployment_health_snapshot(window_kind, repo_root): assemble indicators, run drift detection, compute overall alert state, return DeploymentHealthSnapshot. |
| `src/workflow_dataset/long_run_health/alert_state.py` | classify_alert_state(snapshot or indicators + drift_signals) → AlertState + AlertStateExplanation (rationale, evidence_refs). |
| `src/workflow_dataset/long_run_health/store.py` | save_snapshot, save_drift_signal, load_snapshot, load_drift_signal, list_snapshots, list_drift_signals; persist under data/local/long_run_health/. |
| `src/workflow_dataset/long_run_health/reports.py` | format_long_run_report(snapshot), format_drift_report(signals), format_subsystem_health(subsystem_id), format_alert_explanation(explanation). |
| `src/workflow_dataset/long_run_health/mission_control.py` | long_run_health_slice(repo_root): current deployment health, strongest_drift_signal_id, top_degraded_subsystem_id, operator_burden_trend_summary, next_recommended_maintenance. |
| `src/workflow_dataset/cli.py` | Add health_group: long-run, drift-report, subsystem --id, stability-window, explain --id. |
| `src/workflow_dataset/mission_control/state.py` | Add long_run_health_state from long_run_health_slice. |
| `src/workflow_dataset/mission_control/report.py` | Add [Long-run health] section when present. |
| `tests/test_long_run_health.py` | Snapshot generation, drift signal creation, alert classification, subsystem view, no-drift/weak/contradictory cases. |
| `docs/M46A_M46D_LONG_RUN_HEALTH_DELIVERABLE.md` | Deliverable: files, CLI, samples, tests, gaps. |

## 4. Safety/risk note

- **Read-only:** Drift detection and snapshot building only read from existing stores and mission_control state. No automatic repair, rollback, or pause. Alert states are advisory; no hidden autonomous escalation.
- **Uncertainty visible:** Alert classification uses confidence (e.g. low/medium/high) and evidence_refs; “contradictory” or “insufficient data” is a valid outcome and is not hidden.
- **Local-first:** All persistence under data/local/long_run_health; no remote telemetry.
- **Risk:** If downstream (e.g. stability_reviews or repair_loops) automatically acts on “degraded” or “repair-needed”, that should remain gated by operator approval; this block does not add such automation.

## 5. Drift-detection principles

- **Evidence-based:** Each drift signal carries subsystem, kind, severity, and concrete evidence (e.g. “calmness 0.3 vs baseline 0.7 over rolling_7”).
- **Windowed:** Drift is evaluated over a stability window (e.g. rolling_7) so short-term noise does not dominate.
- **Explainable:** Operator can see why a signal was raised (evidence_refs, baseline vs current).
- **Subsystem-scoped:** Drift is attributed to a subsystem (queue, memory_os, execution_loops, routing, operator_burden, triage, value) so repair_loops can map to patterns.
- **No overfitting:** Use simple thresholds and baselines (e.g. compare to prior snapshot or fixed baseline); avoid complex ML.

## 6. What this block will NOT do

- Add remote telemetry or cloud monitoring.
- Rebuild reliability, release, or production_cut from scratch.
- Hide uncertainty (e.g. force a single alert state when evidence is contradictory).
- Overfit to one subsystem (all listed drift kinds get a first-draft implementation).
- Automatically trigger repair, rollback, or pause (only surface state and recommendations).
- Replace existing reliability harness or stability_reviews; integrate with them.
