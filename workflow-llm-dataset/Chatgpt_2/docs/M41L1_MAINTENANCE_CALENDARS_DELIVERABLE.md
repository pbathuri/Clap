# M41L.1 — Maintenance Calendars + Production Rhythm Packs: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/ops_jobs/models.py` | Added `MaintenanceCalendarEntry`, `ProductionRhythmPack` dataclasses with `to_dict()`. |
| `src/workflow_dataset/ops_jobs/__init__.py` | Exported calendar, rhythm_packs, operator_summary symbols. |
| `src/workflow_dataset/cli.py` | Added `ops-jobs calendar`, `ops-jobs rhythm-packs list`, `ops-jobs rhythm-packs show --id`, `ops-jobs operator-summary`. |
| `tests/test_ops_jobs.py` | Added `test_maintenance_calendar`, `test_rhythm_packs`, `test_operator_maintenance_summary`. |

---

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/ops_jobs/calendar.py` | `get_maintenance_calendar()` — groups BUILTIN_OPS_JOBS by rhythm (twice_daily, daily, weekly, monthly). |
| `src/workflow_dataset/ops_jobs/rhythm_packs.py` | `BUILTIN_RHYTHM_PACKS`, `get_rhythm_pack()`, `list_rhythm_pack_ids()` — weekly_production, monthly_production with job_ids and review_checklist. |
| `src/workflow_dataset/ops_jobs/operator_summary.py` | `build_operator_maintenance_summary(repo_root)` — weekly/monthly blocks, summary_text, recommended_action. |
| `docs/samples/M41L1_maintenance_calendar_sample.json` | Sample maintenance calendar (list of rhythm entries). |
| `docs/samples/M41L1_production_rhythm_pack_sample.json` | Sample production rhythm pack (weekly_production). |
| `docs/M41L1_MAINTENANCE_CALENDARS_DELIVERABLE.md` | This file. |

---

## 3. Sample maintenance calendar

See `docs/samples/M41L1_maintenance_calendar_sample.json`. Structure: list of entries, each with `rhythm`, `job_ids`, `label`, `description`. Rhythms: `twice_daily`, `daily`, `weekly`, (optional) `monthly`.

CLI: `workflow-dataset ops-jobs calendar` or `workflow-dataset ops-jobs calendar --json`.

---

## 4. Sample production rhythm pack

See `docs/samples/M41L1_production_rhythm_pack_sample.json`. One pack: `weekly_production` with `pack_id`, `name`, `description`, `rhythm`, `job_ids`, `review_checklist`.

CLI: `workflow-dataset ops-jobs rhythm-packs list`, `workflow-dataset ops-jobs rhythm-packs show --id weekly_production` (or `--json`).

---

## 5. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_ops_jobs.py -v
```

**Scope:** All 10 tests, including M41L.1:
- `test_maintenance_calendar`: calendar has daily/weekly, twice_daily contains queue_calmness_review, weekly contains supportability_refresh or adaptation_audit.
- `test_rhythm_packs`: list includes weekly_production and monthly_production; weekly_production has rhythm weekly, job_ids, review_checklist; get_rhythm_pack("nonexistent") is None.
- `test_operator_maintenance_summary`: summary has summary_text, weekly/monthly with job_ids and review_checklist, calendar_rhythms, recommended_action.

---

## 6. Next recommended step for the pane

- **Wire operator summary into mission control:** Add an optional **[Operator summary]** line or block to `mission_control/report.py` (e.g. one-line `summary_text` or “next weekly/monthly due”) so operators see “what to run and review” from the main dashboard without running `ops-jobs operator-summary` separately.
- **Optional:** Allow override of maintenance calendar or rhythm packs from `data/local/ops_jobs/` (e.g. `calendar.json`, `rhythm_packs.json`) so deployments can customize weekly/monthly packs without code changes.
- **Optional:** Add a “next weekly pack due” / “next monthly pack due” to ops_jobs_state in mission_control state (e.g. next_due_weekly_pack_id, next_due_monthly_pack_id) for at-a-glance visibility.
