# C3 — Cohort-aware dashboard + alert strip

Cohort summary and lightweight alert strip for the Local Reporting Command Center. Read-oriented and operator-friendly.

---

## 1. Files modified

| Path | Change |
|------|--------|
| `src/workflow_dataset/release/dashboard_data.py` | Added `cohort_summary` (active_cohort_name, sessions_count, avg_usefulness, recent_recommendation). Added `alerts` (review_pending, review_pending_count, package_ready, staged_apply_plan_available, benchmark_regression_detected). Benchmark regression from `eval.board.compare_latest_vs_best` when available. |
| `src/workflow_dataset/ui/dashboard_view.py` | Added `_render_alert_strip()` (one line: Review pending, Package ready, Staged apply-plan preview, Benchmark regression). Added `_render_cohort_summary()` (panel: Active cohort, Sessions, Avg usefulness, Recent recommendation). Dashboard content now shows alert strip and cohort summary first, then Readiness, Workspaces, etc. |
| `tests/test_review_queue.py` | `test_dashboard_data_structure` extended for cohort_summary and alerts keys. Added `test_dashboard_cohort_summary_and_alerts`. |
| **New** `docs/C3_COHORT_ALERT_STRIP.md` | This delivery memo. |

---

## 2. Exact dashboard usage

Unchanged; cohort summary and alert strip are part of the existing dashboard:

```bash
workflow-dataset dashboard
workflow-dataset dashboard --workflow weekly_status
workflow-dataset console
# D → view dashboard (alert strip + cohort summary at top)
```

---

## 3. Sample cohort-aware dashboard output

```
Alerts: Review pending: 3  |  Package ready  |  Staged apply-plan preview

╭──────────────────────── Cohort summary ─────────────────────────────────╮
│   Active cohort: broader_ops_q1                                         │
│   Sessions: 13                                                           │
│   Avg usefulness: 3.92                                                   │
│   Recent recommendation: expand_adjacent                                 │
╰──────────────────────────────────────────────────────────────────────────╯

——— Readiness ———
╭──────────────────────────────── 1. Readiness ────────────────────────────────╮
...
```

With no alerts:

```
Alerts: none

╭──────────────────────── Cohort summary ─────────────────────────────────╮
│   Active cohort: —                                                      │
│   Sessions: 0                                                            │
│   Avg usefulness: —                                                      │
│   Recent recommendation: —                                              │
╰──────────────────────────────────────────────────────────────────────────╯
```

With benchmark regression detected:

```
Alerts: Review pending: 2  |  Benchmark regression
```

---

## 4. Alert strip semantics

| Alert | When shown |
|-------|------------|
| **Review pending** | One or more workspaces have artifacts not yet reviewed (unreviewed_count > 0). Shows count. |
| **Package ready** | At least one recent workspace has status package_ready (package already built). |
| **Staged apply-plan preview** | Staging board has a last apply-plan preview path (file exists). |
| **Benchmark regression** | Eval board `compare_latest_vs_best(root=data/local/eval)` returns a non-empty `regressions` list. Optional; no eval data → not shown. |

---

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python -m pytest tests/test_review_queue.py -v --tb=short -k "dashboard"
```

Includes: `test_dashboard_data_structure` (cohort_summary, alerts), `test_dashboard_cohort_summary_and_alerts`.
