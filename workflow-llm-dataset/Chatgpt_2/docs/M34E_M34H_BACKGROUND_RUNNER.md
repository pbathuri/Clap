# M34E–M34H — Bounded Background Runner + Safe Async Execution

First-draft bounded background runner: pick up matched recurring workflows, evaluate policy/trust, run simulate-first, support narrow approved async execution, record state/outputs/failures.

## 1. Files modified

- **`src/workflow_dataset/cli.py`** — Added `background_group` and commands: `queue`, `run`, `status`, `history`, `retry`, `suppress`.
- **`src/workflow_dataset/mission_control/state.py`** — Added `background_runner_state` (active_run_ids, blocked_run_ids, retryable_run_ids, next_automation_id, next_plan_ref, queue_length, recent_outcomes, needs_review_automation_ids).
- **`src/workflow_dataset/mission_control/report.py`** — Added “[Background runner]” section (queue, next, active/blocked/retryable, needs_review, next action).

## 2. Files created

- **`src/workflow_dataset/background_run/models.py`** — BackgroundRun, RunSourceTrigger, QueuedRecurringJob, ExecutionMode, ApprovalState, BackgroundArtifact, FailureRetryState, RunSummary.
- **`src/workflow_dataset/background_run/store.py`** — load/save queue, save/load/list runs, append_history_entry, load_history.
- **`src/workflow_dataset/background_run/gating.py`** — evaluate_background_policy(job, work_state, repo_root) → GatingResult (allowed, simulate_only, approval_required, degraded_fallback, notes).
- **`src/workflow_dataset/background_run/runner.py`** — pick_eligible_job, run_one_background (simulate-first, persist run/artifacts/history), build_run_summary.
- **`src/workflow_dataset/background_run/recovery.py`** — classify_failure, retry_run, defer_run, handoff_to_review, suppress_run.
- **`src/workflow_dataset/background_run/cli.py`** — cmd_queue, cmd_run, cmd_status, cmd_history, cmd_retry, cmd_suppress.
- **`src/workflow_dataset/background_run/__init__.py`** — Public API exports.
- **`docs/M34E_M34H_BACKGROUND_RUNNER_BEFORE_CODING.md`** — Before-coding analysis (what exists, what’s missing, file plan, safety, what we don’t do).
- **`docs/M34E_M34H_BACKGROUND_RUNNER.md`** — This document.
- **`tests/test_background_run.py`** — Tests for models, queue, gating, run roundtrip, recovery, summary.

## 3. Exact CLI usage

Entry point is the main app (e.g. `workflow-dataset` or `python -m workflow_dataset.cli`). All commands live under the **`background`** group:

```bash
# List queued recurring jobs (or add one)
workflow-dataset background queue
workflow-dataset background queue --json
workflow-dataset background queue --add weekly_report --plan-ref weekly_job_id --plan-source job

# Run one background workflow (next eligible, or by automation_id)
workflow-dataset background run
workflow-dataset background run --id weekly_report
workflow-dataset background run --id weekly_report --json

# Status: active, blocked, retryable, next, queue length
workflow-dataset background status
workflow-dataset background status --json

# Recent history
workflow-dataset background history
workflow-dataset background history --limit 20 --json

# Retry a run
workflow-dataset background retry bg_abc123
workflow-dataset background retry bg_abc123 --json

# Suppress a run (do not retry)
workflow-dataset background suppress bg_abc123
workflow-dataset background suppress bg_abc123 --json
```

## 4. Sample queued recurring job

```json
{
  "automation_id": "auto_weekly_report",
  "plan_source": "job",
  "plan_ref": "weekly_report",
  "trigger_type": "schedule",
  "schedule_or_trigger_ref": "0 9 * * 1",
  "allowed_modes": ["simulate"],
  "require_approval_before_real": true,
  "label": "Weekly report job",
  "created_at": "2025-03-16T12:00:00Z",
  "last_queued_at": "2025-03-16T12:00:00Z"
}
```

## 5. Sample background run record

```json
{
  "run_id": "bg_a1b2c3d4e5f6",
  "automation_id": "auto_weekly_report",
  "source_trigger": "recurring_match",
  "plan_source": "job",
  "plan_ref": "weekly_report",
  "execution_mode": "simulate",
  "approval_state": "approved",
  "status": "completed",
  "executor_run_id": "exec_xyz789",
  "timestamp_start": "2025-03-16T12:00:00Z",
  "timestamp_end": "2025-03-16T12:01:00Z",
  "artifacts": [
    {"path": "/data/local/job_packs/out/weekly_report.pdf", "kind": "file", "run_id": "bg_a1b2c3d4e5f6", "step_index": 0}
  ],
  "failure_retry": {
    "failed": false,
    "failure_reason": "",
    "failure_code": "",
    "retry_count": 0,
    "max_retries": 3,
    "defer_until": "",
    "handoff_to_review": false
  },
  "policy_notes": ["allowed_modes does not include real"],
  "outcome_summary": "executed=1 blocked=0"
}
```

## 6. Sample blocked / retry output

**Blocked (policy):**
```json
{
  "error": "Workflow not allowed for background run",
  "notes": ["job in approval_blocked_jobs"],
  "run_id": "",
  "status": "blocked"
}
```

**Retry (after retry_run):**
```json
{
  "run_id": "bg_abc123",
  "status": "queued",
  "retry_count": 1
}
```

**Suppress:**
```json
{
  "run_id": "bg_abc123",
  "status": "suppressed"
}
```

## 7. Sample background summary

From `workflow-dataset background status --json` or mission control `background_runner_state`:

```json
{
  "active_run_ids": [],
  "blocked_run_ids": ["bg_blocked1"],
  "retryable_run_ids": ["bg_failed1"],
  "next_automation_id": "auto_weekly_report",
  "next_plan_ref": "weekly_report",
  "queue_length": 2,
  "recent_outcomes": [
    {
      "run_id": "bg_a1b2c3",
      "automation_id": "auto_weekly_report",
      "plan_ref": "weekly_report",
      "status": "completed",
      "executor_run_id": "exec_xyz",
      "outcome_summary": "executed=1 blocked=0",
      "timestamp": "2025-03-16T12:01:00Z"
    }
  ],
  "needs_review_automation_ids": []
}
```

## 8. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_background_run.py -v
```

**Test names:**

- `test_queued_recurring_job_roundtrip`
- `test_background_run_roundtrip`
- `test_queue_save_load`
- `test_gating_simulate_only_when_real_not_allowed`
- `test_gating_blocked_when_approval_blocked`
- `test_classify_failure`
- `test_retry_run`
- `test_suppress_run`
- `test_build_run_summary`

All 9 tests should pass.

## 9. Exact remaining gaps for later refinement

- **Recurring-workflow contract (Pane 1):** This block consumes a minimal `QueuedRecurringJob` (e.g. from `data/local/background_run/queue.json`). Full trigger/schedule contract (cron expression, reminder integration) is defined elsewhere.
- **Degraded-mode wiring:** Gating does not yet call a “current degraded profile” API; placeholder left in gating for when reliability harness exposes it.
- **Real execution after simulate:** `run_one_background` currently runs only simulate; optional “allow real after simulate” path exists in args but real mode is not yet invoked in the same run (approval and second executor call can be added).
- **Handoff to intervention inbox:** `handoff_to_review` marks the run as `needs_review` and records history; integration with review_studio/inbox to show “automations requiring human review” as first-class items can be added.
- **Cron/scheduler:** No daemon; operator must run `workflow-dataset background run` (e.g. via cron or task scheduler) to process the queue.
- **Run-by-id from queue:** `background run --id <automation_id>` runs that automation if it appears in the queue; dequeue-after-run or per-automation locking is not implemented.
- **Polish:** No UI beyond CLI and mission-control report; no notifications or dashboard tiles.
