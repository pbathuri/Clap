# M46A–M46D Deliverable — Long-Run Health + Drift Detection

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/long_run_health/alert_state.py` | Set `contradictory=True` when mixed evidence (high/medium drift and ≥2 subsystems ok). |
| `src/workflow_dataset/long_run_health/snapshot.py` | `_make_window()` now sets `start_iso` and `end_iso` from current time and window kind (daily, weekly, rolling_7, rolling_30). |
| `tests/test_long_run_health.py` | Added `test_no_drift_empty_state`, `test_weak_signal_watch_only`, `test_alert_state_contradictory`. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M46A_M46D_BEFORE_CODING_ANALYSIS.md` | Before-coding: existing health state, gaps, file plan, safety, drift principles, what this block does not do. |
| `docs/M46A_M46D_LONG_RUN_HEALTH.md` | Operator-facing overview: CLI, mission control, subsystem IDs, remaining gaps. |
| `docs/M46A_M46D_DELIVERABLE.md` | This deliverable. |

*Note:* The long-run health layer (models, drift_detection, indicators, snapshot, store, reports, mission_control, CLI, mission_control state/report integration) already existed in the repo; this deliverable adds contradictory handling, stability-window dates, tests, and docs.

## 3. Exact CLI usage

```bash
workflow-dataset health long-run [--repo PATH] [--window daily|weekly|rolling_7|rolling_30] [--write] [--json]
workflow-dataset health drift-report [--repo PATH] [--window rolling_7] [--limit 30] [--json]
workflow-dataset health subsystem --id <memory_os|queue|execution_loops|operator_burden|triage|routing> [--repo PATH] [--window rolling_7] [--json]
workflow-dataset health stability-window [--repo PATH] [--window rolling_7] [--json]
workflow-dataset health explain --id <drift_xxx|health_xxx> [--repo PATH] [--json]
```

## 4. Sample long-run health snapshot

```json
{
  "snapshot_id": "health_abc123",
  "window": {
    "kind": "rolling_7",
    "start_iso": "2026-03-10T12:00:00Z",
    "end_iso": "2026-03-17T12:00:00Z",
    "label": "Last 7 days (rolling)"
  },
  "subsystem_signals": [
    {"subsystem_id": "operator_burden", "label": "Operator burden", "status": "ok", "score": 0.9, "summary": "awaiting_takeover=0 taken_over=0 paused=0 triage_open=0", "evidence_refs": ["adaptive_execution_state", "supervisory_control_state", "triage"]},
    {"subsystem_id": "memory_os", "label": "Memory / retrieval", "status": "ok", "score": 0.7, "summary": "recommendations=2 weak_cautions=0", "evidence_refs": ["memory_intelligence"]},
    {"subsystem_id": "execution_loops", "label": "Execution reliability", "status": "ok", "score": 0.85, "summary": "running=2 awaiting_takeover=0 forced_takeover=0", "evidence_refs": ["adaptive_execution_state", "shadow_execution_state"]}
  ],
  "drift_signals": [],
  "alert_state": "healthy",
  "alert_explanation": {
    "state": "healthy",
    "rationale": "No drift signals; subsystems ok. Sustained deployment healthy.",
    "evidence_refs": [],
    "confidence": "medium",
    "contradictory": false
  },
  "generated_at_iso": "2026-03-17T12:00:00Z",
  "vertical_id": "default"
}
```

## 5. Sample drift report

```
[Drift report] count=2
  drift_xyz1  kind=queue_calmness  subsystem_id=queue  severity=medium
    Queue calmness low: 0.38 (noise=0.6)
    baseline=0.7 current=0.38 window=rolling_7
  drift_xyz2  kind=triage_recurrence  subsystem_id=triage  severity=low
    Triage open issues: 5
    baseline=0.0 current=5.0 window=rolling_7
```

## 6. Sample degraded-state explanation

```
[Alert state] degraded  confidence=medium
  rationale: Some drift or degraded subsystem; monitor and consider repair.
  evidence_refs: queue, drift_xyz1
```

With contradictory evidence:

```
[Alert state] repair-needed  confidence=medium
  rationale: Drift or degraded subsystems indicate repair recommended before continuing.
  evidence_refs: routing, drift_abc
  (contradictory evidence)
```

## 7. Exact tests run

```bash
pytest tests/test_long_run_health.py -v
```

- **Existing (15):** test_snapshot_generation, test_alert_state_healthy, test_alert_state_degraded, test_alert_state_repair_needed, test_subsystem_health_format, test_drift_report_format, test_alert_explanation_format, test_store_snapshot_and_load, test_store_drift_signal, test_operator_burden_from_state, test_queue_calmness_drift_fires, test_queue_calmness_drift_no_fire, test_triage_recurrence_drift_fires, test_mission_control_slice, test_build_deployment_health_snapshot_integration.
- **Added (3):** test_no_drift_empty_state, test_weak_signal_watch_only, test_alert_state_contradictory.

**Total: 18 tests.** (Integration tests that call `get_mission_control_state` may be slow; unit tests run in &lt;1s.)

## 8. Exact remaining gaps for later refinement

- **Historical baseline:** Compare current state to a persisted baseline (e.g. 7 days ago) instead of fixed thresholds.
- **Stability window semantics:** Use start_iso/end_iso to filter or weight evidence (e.g. only consider events in window); currently window is descriptive only.
- **Deployment-cut / vertical filtering:** Build snapshot per vertical or deployment cut; today single global snapshot per repo.
- **Threshold tuning:** Document and optionally make configurable the drift thresholds (e.g. fail_ratio 0.3, calmness 0.5, open_issue_count 3).
- **No-drift vs weak-signal clarity:** Explicit “no drift” vs “drift below threshold” in report text when useful.
