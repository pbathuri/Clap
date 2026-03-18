# M46L.1 — Review Cadences + Long-Run Rollback Policies: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/stability_reviews/models.py` | Added `ReviewCadenceKind`, `ReviewCadence`, `RollbackPolicy`, `StabilityThresholds` with `to_dict()`. |
| `src/workflow_dataset/stability_reviews/pack_builder.py` | Load thresholds and rollback policy; apply `apply_thresholds()` for band (continue_as_is / continue_with_watch / narrow / pause); resolve `prior_stable_ref` via `resolve_prior_stable_ref()`; evaluate rollback policy for `should_rollback_by_policy`; `_decide()` now takes `threshold_band`, `prior_stable_ref`, `should_rollback_by_policy`, `rollback_reason`, `rollback_policy` and uses band for continue vs watch vs narrow, and sets `prior_stable_ref` on rollback rec. |
| `src/workflow_dataset/stability_reviews/__init__.py` | Exported `ReviewCadence`, `ReviewCadenceKind`, `RollbackPolicy`, `StabilityThresholds`. |
| `src/workflow_dataset/cli.py` | `stability-reviews generate` uses `load_active_cadence()` and `next_review_due_iso()` for `next_scheduled_review_iso`. Added commands: `stability-reviews cadence show \| set`, `stability-reviews rollback-policy show \| set`, `stability-reviews thresholds show \| set`. |
| `tests/test_stability_reviews.py` | Added tests for cadences (default, next_due, load/save active), rollback policy (evaluate, resolve_prior_stable_ref, load/save), thresholds (apply continue/watch/narrow/pause, load/save). |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/stability_reviews/cadences.py` | Default cadences (daily, weekly, rolling_stability); `get_cadence_for()`, `next_review_due_iso()`, `load_active_cadence()`, `save_active_cadence()`; persistence in `data/local/stability_reviews/cadence.json`. |
| `src/workflow_dataset/stability_reviews/rollback_policy.py` | Default `RollbackPolicy`; `load_rollback_policy()`, `save_rollback_policy()`, `evaluate_rollback_policy()`, `resolve_prior_stable_ref()`; persistence in `data/local/stability_reviews/rollback_policy.json`. |
| `src/workflow_dataset/stability_reviews/thresholds.py` | Default `StabilityThresholds`; `load_thresholds()`, `save_thresholds()`, `apply_thresholds()`; persistence in `data/local/stability_reviews/thresholds.json`. |
| `docs/M46L1_REVIEW_CADENCES_ROLLBACK_POLICIES_DELIVERABLE.md` | This file. |

## 3. Sample review cadence

**Daily:**
```json
{
  "cadence_id": "daily",
  "kind": "daily",
  "window_kind": "daily",
  "label": "Daily stability review",
  "description": "Review every 24h; window = last 24h.",
  "default_days_until_next": 1
}
```

**Weekly:**
```json
{
  "cadence_id": "weekly",
  "kind": "weekly",
  "window_kind": "weekly",
  "label": "Weekly stability review",
  "description": "Review every 7 days; window = last 7 days.",
  "default_days_until_next": 7
}
```

**Rolling stability (default):**
```json
{
  "cadence_id": "rolling_stability",
  "kind": "rolling_stability",
  "window_kind": "rolling_7",
  "label": "Rolling stability review (7d)",
  "description": "Rolling 7-day window; review on a weekly cadence.",
  "default_days_until_next": 7
}
```

Active cadence is stored in `data/local/stability_reviews/cadence.json`:
```json
{
  "cadence_id": "weekly",
  "updated_at_iso": "2026-03-17T12:00:00Z"
}
```

## 4. Sample rollback policy

**Default long-run rollback policy:**
```json
{
  "policy_id": "default",
  "label": "Default long-run rollback policy",
  "recommend_rollback_on_guidance": true,
  "recommend_rollback_on_cohort_downgrade": true,
  "max_blockers_before_rollback_considered": 0,
  "max_consecutive_pause_before_rollback_considered": 3,
  "prior_stable_ref_rule": "latest_continue_review",
  "description": "Recommend rollback when guidance=rollback or cohort downgrade; prior stable = latest review with decision=continue."
}
```

- **prior_stable_ref_rule**: `latest_continue_review` (use most recent review with decision continue/continue_with_watch), `latest_checkpoint`, or `manual` (operator sets ref).

## 5. Operator-facing thresholds (sample)

**Default thresholds:**
```json
{
  "thresholds_id": "default",
  "label": "Default operator thresholds",
  "max_warnings_continue_as_is": 0,
  "max_triage_issues_continue_as_is": 0,
  "require_checkpoint_criteria_for_continue": false,
  "min_triage_issues_narrow": 1,
  "min_warnings_narrow": 3,
  "min_blockers_pause": 1,
  "min_failed_gates_pause": 1,
  "use_watch_when_weak_evidence": true,
  "use_watch_when_warnings_in_band": true,
  "description": "Continue as-is only with no warnings/triage issues; watch when weak or in band; narrow at 1+ triage or 3+ warnings; pause at 1+ blocker or failed gate."
}
```

- **Continue as-is**: only when warnings ≤ max_warnings_continue_as_is, triage_issues ≤ max_triage_issues_continue_as_is, and (if required) checkpoint criteria met.
- **Continue with watch**: weak evidence, or warnings in band, or above continue-as-is limits but below narrow/pause.
- **Narrow**: triage_issues ≥ min_triage_issues_narrow or warning_count ≥ min_warnings_narrow.
- **Pause**: blocker_count ≥ min_blockers_pause or failed_gates_count ≥ min_failed_gates_pause.

## 6. Exact tests run

```bash
python3 -m pytest tests/test_stability_reviews.py -v
```

**29 tests** (18 existing + 11 M46L.1):  
- test_stability_window_to_dict … test_contradictory_evidence_handling  
- test_default_cadences, test_next_review_due_iso, test_load_save_active_cadence  
- test_rollback_policy_evaluate, test_resolve_prior_stable_ref, test_load_save_rollback_policy  
- test_apply_thresholds_continue_as_is, test_apply_thresholds_watch, test_apply_thresholds_narrow, test_apply_thresholds_pause, test_load_save_thresholds  

## 7. Next recommended step for the pane

- **Integrate cadence with ops_jobs/calendar**: Schedule “next stability review” as an ops job or calendar reminder using `next_review_due_iso(active_cadence, last_review_at)` so operators get a concrete due date.
- **Expose thresholds in mission control**: Add a `stability_reviews.thresholds_band` (or similar) to the mission-control slice so the UI can show “current band: continue_with_watch” and link to `workflow-dataset stability-reviews thresholds show`.
- **Optional: custom threshold/cadence presets**: Allow named presets (e.g. “strict”, “relaxed”) for thresholds and cadence and persist under the same `stability_reviews` dir for operator choice.
