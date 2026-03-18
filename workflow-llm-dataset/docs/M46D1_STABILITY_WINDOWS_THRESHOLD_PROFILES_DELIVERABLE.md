# M46D.1 — Stability Windows + Drift Threshold Profiles (Deliverable)

First-draft support for stability windows (daily, weekly, rolling_7, rolling_30, rolling long-run), drift threshold profiles (conservative, balanced, production-strict), and clearer operator-facing explanations (short_summary) for why a system is healthy, under watch, degraded, or repair-needed. Extends M46A–M46D; no rebuild.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/long_run_health/models.py` | Added `short_summary` to `AlertStateExplanation`. |
| `src/workflow_dataset/long_run_health/alert_state.py` | Set `short_summary` on every explanation (one-line "why" per state). |
| `src/workflow_dataset/long_run_health/drift_detection.py` | All drift detectors and `collect_drift_signals` accept optional `threshold_profile`; use profile thresholds (execution_loop_fail_ratio_max, queue_calmness_min, etc.) when provided. |
| `src/workflow_dataset/long_run_health/snapshot.py` | Use `build_window(kind)` from stability_windows; `build_deployment_health_snapshot(..., threshold_profile_id="balanced")` and pass profile into `collect_drift_signals`. |
| `src/workflow_dataset/long_run_health/store.py` | Load/save `short_summary` on `AlertStateExplanation`. |
| `src/workflow_dataset/long_run_health/reports.py` | `format_alert_explanation` prints `why: <short_summary>` when present. |
| `src/workflow_dataset/long_run_health/__init__.py` | Exported `list_stability_windows`, `get_stability_window`, `build_window`, `list_threshold_profiles`, `get_threshold_profile`, `DriftThresholdProfile`, `PROFILE_*`. |
| `src/workflow_dataset/cli.py` | `health long-run` / `drift-report` / `subsystem` / `stability-window`: added `--threshold-profile`. `health stability-window`: added `--list` to list windows. New command `health threshold-profiles`. `health explain`: import `build_deployment_health_snapshot`; show short summary in alert explanation. |
| `tests/test_long_run_health.py` | Added tests: `test_list_stability_windows`, `test_build_window_rolling_long_run`, `test_list_threshold_profiles`, `test_conservative_profile_fires_drift_earlier`, `test_alert_explanation_has_short_summary`. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/long_run_health/stability_windows.py` | Registry of stability windows (daily, weekly, rolling_7, rolling_30, rolling_long_run); `list_stability_windows()`, `get_stability_window(kind)`, `build_window(kind)` → `StabilityWindow` with start_iso/end_iso. |
| `src/workflow_dataset/long_run_health/threshold_profiles.py` | Drift threshold profiles: conservative, balanced, production_strict; `list_threshold_profiles()`, `get_threshold_profile(profile_id)`. |
| `docs/M46D1_STABILITY_WINDOWS_THRESHOLD_PROFILES_DELIVERABLE.md` | This deliverable. |

---

## 3. Sample stability-window output

**CLI:** `workflow-dataset health stability-window --list`

```
[bold]Stability windows[/bold]
  daily: Today  (1 days)
    Single-day view; most recent 24 hours.
  weekly: This week  (7 days)
    Last 7 days; week view.
  rolling_7: Last 7 days (rolling)  (7 days)
    Rolling 7-day window for short-run stability.
  rolling_30: Last 30 days (rolling)  (30 days)
    Rolling 30-day window.
  rolling_long_run: Long-run (rolling 30 days)  (30 days)
    Rolling 30-day window for sustained deployment health.
```

**CLI:** `workflow-dataset health stability-window --window rolling_long_run --json`

```json
{
  "window": {
    "kind": "rolling_long_run",
    "start_iso": "2026-02-15T12:00:00Z",
    "end_iso": "2026-03-17T12:00:00Z",
    "label": "Long-run (rolling 30 days)"
  },
  "alert_state": "healthy",
  "snapshot_id": "health_..."
}
```

---

## 4. Sample drift-threshold profile

**CLI:** `workflow-dataset health threshold-profiles`

```
[bold]Drift threshold profiles[/bold]
  conservative: Conservative
    Tighter thresholds; drift signals fire earlier. Use for new or high-stakes deployments.
    execution_loop_fail_ratio_max=0.2  queue_calmness_min=0.6  triage_open_issues_min=2
  balanced: Balanced
    Default thresholds; balanced sensitivity for most deployments.
    execution_loop_fail_ratio_max=0.3  queue_calmness_min=0.5  triage_open_issues_min=3
  production_strict: Production-strict
    Looser thresholds; fewer drift signals. Use when production stability is paramount.
    execution_loop_fail_ratio_max=0.4  queue_calmness_min=0.4  triage_open_issues_min=5
```

**JSON (balanced):**

```json
{
  "profile_id": "balanced",
  "label": "Balanced",
  "description": "Default thresholds; balanced sensitivity for most deployments.",
  "execution_loop_fail_ratio_max": 0.3,
  "intervention_rate_max": 0.5,
  "queue_calmness_min": 0.5,
  "memory_weak_cautions_max": 2,
  "triage_open_issues_min": 3,
  "takeover_count_min": 2,
  "value_usefulness_min": 0.4
}
```

---

## 5. Exact tests run

```bash
pytest tests/test_long_run_health.py -v -k "not test_mission_control_slice and not test_build_deployment_health_snapshot_integration"
```

**21 passed** (2 deselected: slow integration tests). New M46D.1 tests: `test_list_stability_windows`, `test_build_window_rolling_long_run`, `test_list_threshold_profiles`, `test_conservative_profile_fires_drift_earlier`, `test_alert_explanation_has_short_summary`.

Full suite (including integration): `pytest tests/test_long_run_health.py -v` (23 tests; mission_control and full snapshot tests may be slow).

---

## 6. Next recommended step for the pane

- **Persist threshold profile choice:** Allow storing the active threshold profile (e.g. in `data/local/long_run_health/current_profile.json` or mission_control state) so `health long-run` and mission_control slice use it by default without passing `--threshold-profile` every time.
- **Stability window in mission control:** Include the current stability window kind and label in the long_run_health mission_control slice so operators see which window the current alert is based on.
- **Explain with profile:** In `health explain --id health_xxx`, show which threshold profile was used for that snapshot (e.g. add `threshold_profile_id` to the snapshot model and persist it when saving).
