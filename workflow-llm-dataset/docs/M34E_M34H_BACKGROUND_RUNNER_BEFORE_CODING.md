# M34E–M34H — Bounded Background Runner: Before Coding

## 1. What execution / queue / async-like behavior already exists

- **Executor (M26E–M26H)**  
  - `ExecutionRun`, `ActionEnvelope`, checkpoint decisions, blocked/recovery.  
  - `run_with_checkpoints(plan_source, plan_ref, mode, …)` — synchronous run; can pause at checkpoints with `awaiting_approval`; persists to `data/local/executor/runs/<run_id>/`.  
  - `resume_run(run_id, decision)`, `resume_from_blocked(run_id, recovery)`.  
  - Hub: `save_run`, `load_run`, `list_runs`, `record_checkpoint_decision`, `get_recovery_options`, `record_recovery_decision`.

- **Supervised loop (M27E–M27H)**  
  - Approval queue: `ApprovalQueueItem`, `QueuedAction`; enqueue → approve/reject/defer; `execute_approved(queue_id)` calls `run_with_checkpoints` and records `ExecutionHandoff`.  
  - No recurring schedule; approval is one-shot then execute.

- **Context / triggers (M23L)**  
  - `WorkState` from local sources; `evaluate_trigger_for_job`, `evaluate_trigger_for_routine` — explicit trigger results (approval_blocked, simulate_only, reminder_due, etc.).  
  - No auto-run; used by copilot recommendations.

- **Assist engine**  
  - Policy (quiet hours, focus-safe, interruptibility); queue of suggestions (snooze/dismiss/accept).  
  - No execution; suggestion-only.

- **Human policy (M28I–M28L)**  
  - `evaluate_policy` → `PolicyEvalResult` (is_always_manual, may_batch, may_delegate, simulate_only, blocked).  
  - Overrides by project/pack; used to gate actions.

- **Reliability (M30)**  
  - Degraded profiles (install_blocked, approval_blocked, etc.); fallback matrix (subsystem → disable_flows, fallback_capability).  
  - No runner; advisory for “what still works”.

- **Edge**  
  - `schedule-checks`: writes `data/local/edge/schedule.json` with interval; “use cron to run workflow-dataset edge check-now”.  
  - No daemon; no recurring workflow execution.

- **Devlab**  
  - Experiment queue (queued/running/done); `run-next` runs one experiment.  
  - Not workflow/planner/executor; separate experiment pipeline.

**Summary:** Synchronous executor + approval queue + triggers + policy + degraded fallbacks exist. There is **no** recurring-workflow queue, no “background run” record, no policy-gated “run between sessions” loop, and no simulate-first then optional approved execution in one contract.

---

## 2. What is missing for a safe bounded background runner

- **Recurring-workflow / trigger contract (consumption)**  
  - Explicit “queued recurring job” model: automation_id, plan_source, plan_ref, trigger_type, schedule_or_trigger_ref, allowed_modes, require_approval_before_real.  
  - Assumed provided by Pane 1; this block consumes it (e.g. from `data/local/background/queue.json` or equivalent).

- **Background run model**  
  - A “background run” record: run_id, source_trigger, automation_id, plan_ref, execution_mode, approval_state, status, timestamps, artifacts, failure/retry state.  
  - Distinct from `ExecutionRun` (which is plan execution state); background run wraps intent + policy + outcome.

- **Policy / trust gating before run**  
  - Before starting a run: workflow allowed in background? simulate-only required? operator approval required first?  
  - Use human_policy, assist_engine policy, context triggers, and reliability state to decide: go / simulate_only / blocked / degraded.

- **Simulate-first then optional approved execution**  
  - Run in simulate mode first; record result; if policy allows and (if required) approval present, optionally run real in same or next invocation.  
  - Bounded: only workflows explicitly marked for background + passing policy.

- **Queue processing loop (bounded)**  
  - Pick next eligible queued recurring job; gate by policy; run simulate (and optionally approved real); persist run record and outputs; skip/pause blocked; retry/defer on failure.  
  - One-shot or small batch per CLI invocation (no hidden daemon).

- **Failure / retry / recovery**  
  - Blocked runs (policy, approval, capability); retryable failures (transient error, defer); suppressed (policy); degraded (fallback mode); handoff to human (e.g. add to intervention inbox).

- **Visibility**  
  - CLI: queue, run, status, history, retry, suppress.  
  - Mission control: active background runs, blocked/retryable, next recurring, recent outcomes, automations needing review.

---

## 3. Exact file plan

| Area | Action | Path |
|------|--------|------|
| **Models** | Create | `src/workflow_dataset/background_run/models.py` — BackgroundRun, RunSourceTrigger, QueuedRecurringJob, ExecutionMode, ApprovalState, BackgroundArtifact, FailureRetryState, RunSummary |
| **Store** | Create | `src/workflow_dataset/background_run/store.py` — queue load/save, run save/load/list, history append |
| **Gating** | Create | `src/workflow_dataset/background_run/gating.py` — evaluate_background_policy(workflow, work_state, policy, degraded) → allowed, simulate_only, approval_required, degraded_fallback |
| **Runner** | Create | `src/workflow_dataset/background_run/runner.py` — pick_eligible_job, run_one_background(simulate_first, then optional approved real), persist run/artifacts, set blocked/retry/suppress |
| **Recovery** | Create | `src/workflow_dataset/background_run/recovery.py` — classify failure (blocked / retryable / suppress / degraded), retry_run, defer_run, handoff_to_review |
| **CLI** | Create | `src/workflow_dataset/background_run/cli.py` — queue, run, status, history, retry, suppress; register under `background_group` |
| **CLI** | Modify | `src/workflow_dataset/cli.py` — add `background_group`, mount background_run CLI |
| **Mission control** | Modify | `src/workflow_dataset/mission_control/state.py` — add `background_runner_state` (active runs, blocked, next recurring, recent outcomes, needs_review) |
| **Mission control** | Modify | `src/workflow_dataset/mission_control/report.py` — add Background section (active, blocked, next, outcomes, needs review) |
| **Package** | Create | `src/workflow_dataset/background_run/__init__.py` — export public API |
| **Tests** | Create | `tests/test_background_run.py` — run creation, queue processing, simulate-first, blocked/retry, policy gating, degraded |
| **Docs** | Create | `docs/M34E_M34H_BACKGROUND_RUNNER.md` — design, samples, CLI, tests, gaps |

---

## 4. Safety / risk note

- **Do:** Gate every run with policy and trust (human_policy, simulate_only, approval_required). Simulate-first by default. Only run real when explicitly allowed and (if required) approved. Persist all runs and outcomes; no hidden execution.  
- **Do not:** Bypass approval, run real without policy allow, or start a persistent daemon that runs without operator invocation (e.g. cron or explicit `workflow-dataset background run`).  
- **Risk:** If “recurring workflow” definitions or policy are misconfigured, background could run more than intended; mitigation: default to simulate_only and require explicit allow + approval for real; all runs visible in status/history.

---

## 5. What this block will NOT do

- Define the **recurring-workflow / trigger contract** (Pane 1); we consume a minimal contract (e.g. QueuedRecurringJob with plan_source, plan_ref, trigger_type, allowed_modes).  
- Replace or rewrite planner/executor/action cards/policy/trust; we call existing executor and policy APIs.  
- Add cloud job workers or distributed queues.  
- Implement a long-lived daemon; execution is bounded per CLI invocation (or explicit cron running the CLI).  
- Auto-approve real execution; approval remains explicit (or from pre-approved list per automation_id, if policy allows).  
- Polish UI/UX; first-draft visibility via CLI and mission-control report only.
