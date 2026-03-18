# M23L — Work State Engine + Context-Aware Trigger Policies — Final Output

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/copilot/recommendations.py` | Added `context_snapshot` parameter to `recommend_jobs`; when provided (WorkState or "latest"), enriches each recommendation with `why_now_evidence` and `context_trigger` via trigger evaluation. Added `_enrich_with_context`. |
| `src/workflow_dataset/mission_control/state.py` | Added block 9 **work_context**: latest_snapshot_id, context_recommendations_count, context_blocked_count, newly_recommendable_jobs, reminders_due_count, recent_state_changes, next_recommended_action. Aggregates from context snapshot and drift. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Context]** section: snapshot, context_recommendations, context_blocked, newly_recommendable, recent_state_changes, next. |
| `src/workflow_dataset/cli.py` | `copilot recommend`: added `--context latest`; print `why_now_evidence` when present. Added `copilot explain-recommendation` (--id / --job). Added **context** group: `context refresh`, `context show [--snapshot latest]`, `context compare --latest --previous`. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/context/__init__.py` | Package exports. |
| `src/workflow_dataset/context/config.py` | get_context_root, get_snapshots_dir, get_latest_snapshot_path, get_previous_snapshot_path (data/local/context). |
| `src/workflow_dataset/context/work_state.py` | WorkState dataclass; build_work_state(repo_root) from job_packs_report, intake, dashboard_data, approval_registry, copilot, task_demos; work_state_to_dict, work_state_summary_md. |
| `src/workflow_dataset/context/snapshot.py` | save_snapshot(work_state, repo_root), load_snapshot(snapshot_id, repo_root), list_snapshots(limit). Writes snapshot_<id>.json, latest.json, previous.json (on refresh), work_state_summary.md. |
| `src/workflow_dataset/context/triggers.py` | TriggerResult; evaluate_trigger_for_job(job_id, work_state, repo_root); evaluate_trigger_for_routine(routine_id, work_state, repo_root); evaluate_all_triggers(work_state, repo_root). Trigger types: previous_job_succeeded, approval_present, approval_blocked, simulate_only, reminder_due, intake_available, routine_defined. |
| `src/workflow_dataset/context/drift.py` | ContextDrift; compare_snapshots(older, newer); load_latest_and_previous(repo_root). |
| `src/workflow_dataset/context/recommendation_explain.py` | explain_recommendation(rec_id, repo_root), explain_recommendation_by_job(job_id, repo_root); returns explanation_md and structured fields. |
| `docs/M23L_READ_FIRST.md` | Pre-coding analysis: existing state, local signals, gap, file plan, safety. |
| `docs/M23L_WORK_STATE_OPERATOR.md` | Operator guide: what work-state is, inputs, context-aware recommendations, manual vs automatic, privacy. |
| `docs/M23L_FINAL_OUTPUT.md` | This file. |
| `tests/test_context.py` | Tests: build_work_state, work_state_to_dict/summary_md, save/load/list snapshots, evaluate_trigger for job/routine, recommend_jobs with context, explain_recommendation_by_job, compare_snapshots, load_latest_and_previous, mission_control work_context. |

## 3. Exact CLI usage

```bash
workflow-dataset context refresh [--repo-root PATH]
workflow-dataset context show [--snapshot latest|previous|<id>] [--repo-root PATH]
workflow-dataset context compare [--latest] [--previous] [--repo-root PATH]

workflow-dataset copilot recommend [--limit N] [--context latest] [--repo-root PATH]
workflow-dataset copilot explain-recommendation [--id <rec_id>] [--job <job_pack_id>] [--repo-root PATH]
```

## 4. Sample work-state snapshot

```json
{
  "snapshot_id": "20260315120000",
  "created_at": "2026-03-15T12:00:00.000Z",
  "recent_successful_jobs": [{"job_pack_id": "weekly_status_from_notes", "run_id": "r1", "timestamp": "..."}],
  "trusted_for_real_jobs": [],
  "approval_blocked_jobs": [],
  "simulate_only_jobs": ["weekly_status_from_notes", "replay_cli_demo"],
  "intake_labels": ["notes"],
  "recent_workspaces_count": 0,
  "unreviewed_count": 0,
  "approvals_file_exists": false,
  "reminders_count": 1,
  "routines_count": 1,
  "routine_ids": ["morning_reporting"],
  "task_demos_count": 2,
  "errors": {}
}
```

## 5. Sample trigger evaluation output

TriggerResult (per job):

- `job_or_routine_id`: weekly_status_from_notes  
- `trigger_type`: previous_job_succeeded  
- `triggered`: true  
- `reason`: Job has a recent successful run in specialization memory.  
- `blocker`: null  

Additional triggers: simulate_only (triggered), intake_available (triggered if intake_labels non-empty).

## 6. Sample recommendation explanation

```markdown
# Job: weekly_status_from_notes

## Context triggers
- ✓ previous_job_succeeded: Job has a recent successful run in specialization memory.
- ✓ simulate_only: Job is simulate-only; recommend for simulate mode only.
- ✓ intake_available: Intake sets available (1); job may use them.
```

## 7. Sample context-drift output

```
Context drift (previous → latest)
  Newly recommendable jobs: j3
  Reminders count change: +1
  Unreviewed workspaces change: +2
```

(or "No significant drift detected.")

## 8. Exact tests run

```bash
pytest tests/test_context.py -v
pytest tests/test_copilot.py tests/test_mission_control.py -v
```

- test_context.py: 13 passed (build_work_state, work_state dict/summary, save/load/list snapshot, trigger job/routine, recommend with context, explain_recommendation_by_job, compare_snapshots, load_latest_and_previous, mission_control work_context).
- test_copilot.py + test_mission_control.py: 13 passed.

## 9. What remains manual or simulate-only

- **Context refresh:** Operator runs `context refresh`; no background snapshot daemon.
- **Execution:** Triggers only enrich recommendations; no auto-run from context.
- **Reminders:** List/due only; no automatic execution when due.
- **Simulate-first:** Unchanged; job/routine policy and approval gates unchanged.

## 10. Exact recommended next phase after M23L

- **Optional:** Richer trigger conditions (e.g. “recommend when workspace X is in package_pending”) using dashboard workspace items in work state.
- **Optional:** Stale snapshot warning in mission control when latest snapshot is older than N hours.
- **Optional:** `copilot recommend --context latest` as the default in mission_control next_recommended_action when work_context is present.
- **Continue:** Use context refresh and `copilot recommend --context latest` in daily workflow; keep all execution and refresh explicit and local.
