# M46A–M46D — Long-Run Health Model + Drift Detection: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `health_group` (health long-run, drift-report, subsystem, stability-window, explain). |
| `src/workflow_dataset/mission_control/state.py` | Added `long_run_health_state` from `long_run_health_slice` and `local_sources["long_run_health"]`. |
| `src/workflow_dataset/mission_control/report.py` | Added `[Long-run health]` section: alert, drift_count, degraded, strongest_drift, top_degraded, next maintenance. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M46A_M46D_LONG_RUN_HEALTH_BEFORE_CODING.md` | Before-coding: existing health state, gaps, file plan, safety, principles, what we will not do. |
| `src/workflow_dataset/long_run_health/__init__.py` | Package exports. |
| `src/workflow_dataset/long_run_health/models.py` | DeploymentHealthSnapshot, SubsystemHealthSignal, DriftSignal, DegradationTrend, StabilityWindow, OperatorBurdenIndicator, MemoryQualityIndicator, RoutingQualityIndicator, ExecutionReliabilityIndicator, AlertState, AlertStateExplanation. |
| `src/workflow_dataset/long_run_health/indicators.py` | operator_burden_from_state, memory_quality_from_state, routing_quality_from_state, execution_reliability_from_state, build_subsystem_health_signals (from mission_control state). |
| `src/workflow_dataset/long_run_health/drift_detection.py` | execution_loop_drift, intervention_rate_drift, queue_calmness_drift, memory_quality_drift, routing_quality_drift, takeover_frequency_drift, triage_recurrence_drift, value_regression_drift; collect_drift_signals. |
| `src/workflow_dataset/long_run_health/alert_state.py` | classify_alert_state(snapshot or drift_signals + subsystem_signals) → AlertState + AlertStateExplanation. |
| `src/workflow_dataset/long_run_health/snapshot.py` | build_deployment_health_snapshot(window_kind, repo_root, vertical_id). |
| `src/workflow_dataset/long_run_health/store.py` | save_snapshot, load_snapshot, list_snapshots, save_drift_signal, load_drift_signal, list_drift_signals, get_health_dir (data/local/long_run_health). |
| `src/workflow_dataset/long_run_health/reports.py` | format_long_run_report, format_drift_report, format_subsystem_health, format_alert_explanation. |
| `src/workflow_dataset/long_run_health/mission_control.py` | long_run_health_slice: current_alert_state, strongest_drift_signal_id, top_degraded_subsystem_id, operator_burden_trend_summary, next_recommended_maintenance. |
| `tests/test_long_run_health.py` | Snapshot generation, alert state (healthy/degraded/repair-needed), subsystem/drift/alert format, store save/load, operator_burden, queue_calmness_drift, triage_recurrence_drift, mission_control_slice, build_deployment_health_snapshot integration. |
| `docs/M46A_M46D_LONG_RUN_HEALTH_DELIVERABLE.md` | This file. |

## 3. Exact CLI usage

```bash
# Long-run health snapshot (optional --write to persist)
workflow-dataset health long-run [--repo PATH] [--window daily|weekly|rolling_7|rolling_30] [--write] [--json]

# Drift report (from fresh snapshot)
workflow-dataset health drift-report [--repo PATH] [--window rolling_7] [--limit N] [--json]

# Subsystem health by id
workflow-dataset health subsystem --id memory_os [--repo PATH] [--window rolling_7] [--json]

# Stability window summary
workflow-dataset health stability-window [--repo PATH] [--window rolling_7] [--json]

# Explain drift or snapshot alert
workflow-dataset health explain --id drift_xxx [--repo PATH] [--json]
workflow-dataset health explain --id health_xxx [--repo PATH] [--json]
```

## 4. Sample long-run health snapshot (JSON shape)

```json
{
  "snapshot_id": "health_abc123",
  "window": {"kind": "rolling_7", "start_iso": "", "end_iso": "", "label": "Last 7 days (rolling)"},
  "subsystem_signals": [
    {"subsystem_id": "operator_burden", "label": "Operator burden", "status": "ok", "score": 0.9, "summary": "awaiting_takeover=0 taken_over=0 paused=0 triage_open=0", "evidence_refs": ["adaptive_execution_state", "supervisory_control_state", "triage"]},
    {"subsystem_id": "memory_os", "label": "Memory / retrieval", "status": "ok", "score": 0.7, "summary": "recommendations=0 weak_cautions=0", "evidence_refs": ["memory_intelligence"]},
    {"subsystem_id": "queue", "label": "Queue / signal quality", "status": "ok", "score": 0.8, "summary": "calmness=0.8 noise=0.2", "evidence_refs": ["signal_quality"]}
  ],
  "drift_signals": [],
  "degradation_trends": [],
  "operator_burden": {"review_count": 0, "takeover_count": 0, "triage_open_count": 0, "summary": "awaiting_takeover=0 ...", "trend": "stable"},
  "memory_quality": {"recommendation_count": 0, "weak_caution_count": 0, "usefulness_summary": "recommendations=0 weak_cautions=0", "score": 0.5},
  "routing_quality": {"summary": "eval_recommendation=unknown", "score": 0.6, "fallback_used": false},
  "execution_reliability": {"loops_completed": 0, "loops_failed_or_stopped": 0, "shadow_forced_takeover_count": 0, "summary": "running=0 ...", "score": 0.5},
  "alert_state": "healthy",
  "alert_explanation": {"state": "healthy", "rationale": "No drift signals; subsystems ok. Sustained deployment healthy.", "evidence_refs": [], "confidence": "medium", "contradictory": false},
  "generated_at_iso": "2026-03-17T12:00:00Z",
  "vertical_id": "default"
}
```

## 5. Sample drift report (text)

```
[Drift report] count=2
  drift_xyz  kind=queue_calmness  subsystem=queue  severity=medium
    Queue calmness low: 0.35 (noise=0.6)
    baseline=0.7 current=0.35 window=rolling_7
  drift_abc  kind=triage_recurrence  subsystem=triage  severity=low
    Triage open issues: 4
    baseline=0.0 current=4.0 window=rolling_7
```

## 6. Sample degraded-state explanation

```
[Alert state] degraded  confidence=medium
  rationale: Some drift or degraded subsystem; monitor and consider repair.
  evidence_refs: queue, memory_os
```

## 7. Exact tests run

```bash
pytest tests/test_long_run_health.py -v --tb=short
```

- **Unit/fast (13):** test_snapshot_generation, test_alert_state_healthy, test_alert_state_degraded, test_alert_state_repair_needed, test_subsystem_health_format, test_drift_report_format, test_alert_explanation_format, test_store_snapshot_and_load, test_store_drift_signal, test_operator_burden_from_state, test_queue_calmness_drift_fires, test_queue_calmness_drift_no_fire, test_triage_recurrence_drift_fires.
- **Integration (2, slower, use real repo root):** test_mission_control_slice, test_build_deployment_health_snapshot_integration.

To run only the fast set:

```bash
pytest tests/test_long_run_health.py -v -k "not test_mission_control_slice and not test_build_deployment_health_snapshot_integration"
```

**Result:** 13 passed (2 deselected when excluding integration).

## 8. Remaining gaps for later refinement

- **Baselines over time:** Drift currently uses fixed baselines (e.g. calmness 0.7) or single-point state; no persisted history of metrics to compute real trend (e.g. 7-day ago vs today).
- **Stability_reviews / repair_loops wiring:** EvidenceBundle.drift_signals and repair_loops propose --from drift_xxx expect persisted drift ids; this block creates drift signals in-memory during snapshot build. Persisting drift signals when snapshot is saved (and optionally when any drift fires) would allow stability_reviews and repair-loops propose to use them by id.
- **Subsystem coverage:** Only a subset of subsystems (operator_burden, memory_os, routing, execution_loops, queue, triage) have indicators; release, deploy_bundle, benchmark_board, learning_lab could be added as optional signals.
- **Thresholds:** All drift thresholds (e.g. calmness < 0.5, triage open >= 3) are hardcoded; a small config or profile would allow per-vertical tuning.
- **Contradictory evidence:** classify_alert_state does not set contradictory=True; if evidence points both ways, a later pass could detect and set it.
- **Mission control report:** The report section is additive; no link from “next_recommended_maintenance” to a specific CLI command (e.g. “run: workflow-dataset health drift-report”).
- **Integration test runtime:** The two tests that call long_run_health_slice and build_deployment_health_snapshot with repo_root=None can be slow (full mission_control state load); consider marking them as slow or running in a separate CI job.
