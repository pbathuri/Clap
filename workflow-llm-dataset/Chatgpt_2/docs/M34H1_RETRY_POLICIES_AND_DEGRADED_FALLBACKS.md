# M34H.1 — Retry Policies + Async Degraded Fallbacks

First-draft support for retry policies, backoff/suppression strategies, async degraded fallback profiles, and operator-facing failure/fallback explanations.

## 1. Files modified

- **`src/workflow_dataset/background_run/models.py`** — Added `BackoffStrategy` enum, `RetryPolicy` dataclass (max_retries, backoff_strategy, backoff_base_seconds, suppress_after_failures, handoff_after_failures), `AsyncDegradedFallbackProfile` dataclass.
- **`src/workflow_dataset/background_run/store.py`** — Added `RETRY_POLICIES_FILE`, `load_retry_policies()`, `save_retry_policies()`; store imports `RetryPolicy`.
- **`src/workflow_dataset/background_run/recovery.py`** — `retry_run()` now uses `get_policy_for_automation()` and `compute_defer_until()`; optional `with_backoff` parameter; sets `defer_until` from policy backoff.
- **`src/workflow_dataset/background_run/cli.py`** — `cmd_retry()` accepts `no_backoff`; added `cmd_retry_policy`, `cmd_retry_policy_set`, `cmd_fallback_report`, `cmd_explain`.
- **`src/workflow_dataset/cli.py`** — Added `background_group` and commands: `queue`, `run`, `status`, `history`, `retry` (with `--no-backoff`), `suppress`, `retry-policy`, `retry-policy-set`, `fallback-report`, `explain`.
- **`src/workflow_dataset/background_run/__init__.py`** — Exported `BackoffStrategy`, `RetryPolicy`, `AsyncDegradedFallbackProfile`, `load_retry_policies`, `save_retry_policies`, `get_policy_for_automation`, `compute_defer_until`, `build_degraded_fallback_report`, `get_fallback_for_failure`, `build_failure_explanation`, `build_fallback_explanation`, and related constants.
- **`tests/test_background_run.py`** — Added tests for retry policy, compute_defer_until, get_policy_for_automation, retry with backoff, degraded fallback report, get_fallback_for_failure, build_failure_explanation, build_fallback_explanation.

## 2. Files created

- **`src/workflow_dataset/background_run/retry_policies.py`** — `DEFAULT_RETRY_POLICY`, `get_policy_for_automation()`, `compute_defer_until()` (fixed/linear/exponential backoff), `should_suppress_after_failure()`, `should_handoff_after_failure()`.
- **`src/workflow_dataset/background_run/degraded_fallback.py`** — `ASYNC_DEGRADED_FALLBACK_PROFILES` (transient_failure, blocked_approval, policy_suppressed, degraded_simulate), `get_fallback_for_failure()`, `build_degraded_fallback_report()`.
- **`src/workflow_dataset/background_run/explain.py`** — `build_failure_explanation()`, `build_fallback_explanation()` (operator-facing text and recommended_action).
- **`docs/M34H1_RETRY_POLICIES_AND_DEGRADED_FALLBACKS.md`** — This document.

## 3. Sample retry policy

**Default (in code):**
```json
{
  "policy_id": "default",
  "max_retries": 3,
  "backoff_strategy": "exponential",
  "backoff_base_seconds": 60,
  "suppress_after_failures": 0,
  "handoff_after_failures": 0,
  "label": "Default retry with exponential backoff"
}
```

**Custom (saved to `data/local/background_run/retry_policies.json`):**
```json
{
  "default": {
    "policy_id": "default",
    "max_retries": 5,
    "backoff_strategy": "exponential",
    "backoff_base_seconds": 120,
    "suppress_after_failures": 3,
    "handoff_after_failures": 2,
    "label": "max_retries=5 backoff=exponential"
  },
  "by_automation": {
    "auto_weekly_report": {
      "policy_id": "auto_weekly_report",
      "max_retries": 2,
      "backoff_strategy": "linear",
      "backoff_base_seconds": 300,
      "suppress_after_failures": 0,
      "handoff_after_failures": 1,
      "label": "max_retries=2 backoff=linear"
    }
  }
}
```

**CLI:**  
`workflow-dataset background retry-policy`  
`workflow-dataset background retry-policy --automation-id auto_weekly`  
`workflow-dataset background retry-policy-set --max-retries 5 --backoff exponential --base-seconds 120 --suppress-after 3`

## 4. Sample degraded fallback report

From `workflow-dataset background fallback-report --json`:

```json
{
  "report_type": "degraded_fallback",
  "entries": [
    {
      "run_id": "bg_abc123",
      "automation_id": "auto_weekly_report",
      "plan_ref": "weekly_report",
      "status": "failed",
      "failure_code": "transient",
      "outcome_summary": "job not found",
      "timestamp_end": "2025-03-16T12:01:00Z",
      "fallback_profile_id": "transient_failure",
      "fallback_profile_name": "Transient failure",
      "fallback_mode": "retry_with_backoff",
      "operator_explanation": "Run failed with a transient error (e.g. network or temporary resource). Retry with backoff is recommended. Check defer_until and run 'background retry <run_id>' if needed.",
      "still_works": ["retry", "background status", "background history"],
      "disabled_flows": [],
      "defer_until": "2025-03-16T12:02:00Z",
      "retry_count": 1,
      "max_retries": 3
    }
  ],
  "profiles_available": ["transient_failure", "blocked_approval", "policy_suppressed", "degraded_simulate"]
}
```

## 5. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_background_run.py -v
```

**New M34H.1-related test names:**

- `test_retry_policy_roundtrip`
- `test_compute_defer_until`
- `test_get_policy_for_automation_default`
- `test_retry_run_with_backoff`
- `test_build_degraded_fallback_report`
- `test_get_fallback_for_failure`
- `test_build_failure_explanation`
- `test_build_fallback_explanation`

**Full suite:** 17 tests (9 existing + 8 above).

## 6. Next recommended step for the pane

- **Surface in mission control / UI:** Include a short “Retry / fallback” section in the mission-control report (or background runner pane): show default retry policy, link to `fallback-report`, and for each failed/blocked run a one-line operator explanation and “Explain” link (e.g. `workflow-dataset background explain <run_id>`).
- **Auto-apply policy thresholds:** When a run fails, optionally auto-suppress or auto-handoff using `suppress_after_failures` and `handoff_after_failures` from the effective retry policy (e.g. in runner after `run_one_background` sees status failed).
- **Wire degraded detection:** When reliability harness exposes “current degraded profile,” use it in gating and in `get_fallback_for_failure("degraded")` so the fallback report reflects actual degraded state.
- **Per-automation policy in queue:** Let `QueuedRecurringJob` optionally reference a `policy_id` so new runs for that automation pick the right retry policy without requiring `retry-policy-set --automation-id` beforehand.
