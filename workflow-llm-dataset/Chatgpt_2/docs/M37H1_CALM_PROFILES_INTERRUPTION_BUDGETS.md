# M37H.1 — Calm Queue Profiles + Interruption Budgets (Deliverable)

Extends M37E–M37H signal-quality layer (no rebuild). First-draft support for calm queue profiles, interruption budgets, role/mode-based noise ceilings, and stronger explanations for held back, grouped, and resurfaced items.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/signal_quality/models.py` | Added `CalmQueueProfile`, `InterruptionBudget`, `NoiseCeilingByRoleMode`; added `explanation` field to `SuppressedQueueItem`. |
| `src/workflow_dataset/signal_quality/quieting.py` | When creating `SuppressedQueueItem`, set `explanation` via `explain_held_back(...)` (focus_safe, low_value, rate_cap). |
| `src/workflow_dataset/signal_quality/reports.py` | `build_suppressions_report`: include `explanation` in resurfacing_eligible entries; `build_resurfacing_report`: add `explanation` per candidate via `explain_resurfaced`. |
| `src/workflow_dataset/signal_quality/__init__.py` | Exported `CalmQueueProfile`, `InterruptionBudget`, `NoiseCeilingByRoleMode`. |
| `src/workflow_dataset/cli.py` | Added `queue profile [--mode]` and `queue interruption-budget`. |
| `tests/test_signal_quality.py` | Added tests: calm profile model, get_default_profiles, get_profile_for_role_mode, get_noise_ceiling_for, interruption budget model, get_or_create_budget, build_interruption_budget_report, explain_held_back, explain_resurfaced, suppressed item has explanation. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/signal_quality/explain.py` | `explain_held_back`, `explain_grouped`, `explain_resurfaced` with human-readable templates. |
| `src/workflow_dataset/signal_quality/profiles.py` | `get_default_profiles`, `get_noise_ceilings_by_role_mode`, `get_profile_for_role_mode`, `get_noise_ceiling_for`, `apply_profile_limits`. |
| `src/workflow_dataset/signal_quality/budgets.py` | `get_or_create_budget`, `save_budget`, `consume_one`, `remaining`, `build_interruption_budget_report`; persists under `data/local/signal_quality/interruption_budget.json`. |
| `docs/samples/M37H1_sample_calm_queue_profile.json` | Sample calm queue profile (focus mode). |
| `docs/samples/M37H1_sample_interruption_budget.json` | Sample interruption budget output. |
| `docs/M37H1_CALM_PROFILES_INTERRUPTION_BUDGETS.md` | This deliverable. |

## 3. Sample calm queue profile

See `docs/samples/M37H1_sample_calm_queue_profile.json`. Example (focus mode):

```json
{
  "work_mode": "focused",
  "profile_id": "focus",
  "label": "Focus",
  "max_visible": 10,
  "max_suggestions_per_hour": 4,
  "noise_ceiling": 0.3,
  "interrupt_threshold": 0.3,
  "description": "Minimal interruptions; only high-signal items.",
  "noise_ceiling_for_mode": 0.3,
  "max_visible_for_mode": 10
}
```

CLI: `queue profile` or `queue profile --mode focus` or `queue profile --json`.

## 4. Sample interruption budget output

See `docs/samples/M37H1_sample_interruption_budget.json`. Example:

```json
{
  "budget_id": "per_hour",
  "period_hours": 1.0,
  "max_interruptions": 15,
  "consumed": 7,
  "remaining": 8,
  "window_start_utc": "2025-03-16T14:00:00.000000+00:00",
  "recommendation": "Under budget; interruptions allowed."
}
```

CLI: `queue interruption-budget` or `queue interruption-budget --json`.

## 5. Exact tests run

```bash
cd /Users/prady/Desktop/Clap/workflow-llm-dataset
python -m pytest tests/test_signal_quality.py -v
```

**Result:** 24 passed (including M37H.1: calm profile model, get_default_profiles, get_profile_for_role_mode, get_noise_ceiling_for, interruption budget model, get_or_create_budget, build_interruption_budget_report, explain_held_back, explain_resurfaced, suppressed item has explanation).

## 6. Next recommended step for the pane

- **Wire profile into quieting**: Use `get_profile_for_role_mode(focus.work_mode)` in `apply_queue_quieting` / `apply_assist_quieting` to set `max_visible`, and optionally filter by `noise_ceiling` and `interrupt_threshold` from the profile so queue list/view respect the selected calm profile.
- **Consume budget on show**: When a suggestion or queue item is actually shown to the operator (e.g. in assist now or queue list), call `consume_one(repo_root)` so the interruption budget decreases; when remaining is 0, optionally hold non-urgent items and set explanation to a budget-exhausted template.
- **Config file**: Allow storing custom calm profiles (e.g. `data/local/signal_quality/calm_profiles.yaml`) and optional per-repo override for `max_interruptions` and `period_hours` for the interruption budget.
- **Grouped explanation**: When items are grouped (e.g. by section or mode), attach `explain_grouped(group_reason, item_count)` to the group header in queue view or in reports.
- **Mission control**: Add to the signal_quality block: `active_profile_id`, `interruption_budget_remaining`, and optionally `last_explanation_summary` (e.g. count of items held back with focus_safe vs rate_cap).
