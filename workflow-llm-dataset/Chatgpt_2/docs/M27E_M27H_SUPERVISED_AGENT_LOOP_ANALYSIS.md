# M27E–M27H Supervised Agent Loop — Pre-Coding Analysis

## 1. What loop-like behavior already exists

- **Planner**: `compile_goal_to_plan` produces a `Plan` with ordered steps, checkpoints, blocked conditions; `save_current_goal` / `load_current_goal`, `save_latest_plan` / `load_latest_plan` persist goal and plan. No automatic “next step” selection or re-compile trigger.
- **Executor**: `run_with_checkpoints` runs a plan (routine/job) step-by-step; pauses at checkpoints with `status=awaiting_approval`; `resume_run` / `resume_from_blocked` continue after operator decision. Single run-centric; no notion of “project” or “cycle” or “next recommended action” across runs.
- **Mission control**: Aggregates state (goal_plan, executor, teaching_skills, trust_cockpit, etc.) and `recommend_next_action` suggests a single next action string (e.g. “executor resume” or “planner compile”). No approval queue; no persistent “cycle” or “proposed actions.”
- **Session**: `Session` holds active_tasks, active_job_ids, active_routine_ids, recommended_next_actions; session storage and current-session pointer exist. No link from session to a “current agent cycle” or approval queue.
- **Outcomes**: Session outcomes, patterns, signals, bridge to corrections/pack refinement. Not wired into a loop.
- **Trust / capability**: Trust cockpit (benchmark, approval readiness, release gates), approval registry (paths, apps, action scopes). Used by executor/job policy; no explicit “risk/trust” on a proposed action in a queue.
- **Existing `agent_loop`**: Assistive Q&A (query → context → response, session_store, explain/next_step engines). Not the plan–approve–execute cycle; distinct concern.

So: **there is no existing “supervised agent loop”** that (1) selects project/goal, (2) compiles/refreshes plan, (3) proposes next actions, (4) waits in an explicit approval queue, (5) executes only approved actions, (6) updates project/session/outcome, (7) repeats. There are building blocks (planner, executor, session, mission_control, trust) but no orchestration layer that ties them into one visible human-in-the-loop cycle.

---

## 2. What is missing for a true supervised agent cycle

- **Explicit cycle model**: A “cycle” or “agent cycle” that has identity, status (e.g. proposing | awaiting_approval | executing | completed | blocked), and link to project/goal/session.
- **Next-action proposal**: Logic that, given current goal, latest plan, session, skills, packs, trust, produces a small set of **proposed next actions** (e.g. “Execute step 0: job X”, “Compile plan for goal G”, “Resume run R”) with why/risk/mode, not just a single free-text recommendation.
- **Approval queue**: Persisted queue of proposed actions with ids; each item has proposal reason, risk/trust/mode; operator can **approve / reject / defer**; history of decisions.
- **Execution handoff**: When an item is approved, hand the action to the executor (or planner) in a defined way; record result back into the loop (cycle state, session, outcomes as appropriate); advance cycle and produce next proposed action or blocked reason.
- **Visibility**: Mission control (and CLI) must show current cycle, queued approvals, approved/rejected/deferred items, latest execution result, and next proposed action.
- **Project/case contract**: Consume “active project” from existing surface (planner current_goal, optional session_id / project slug). No new global “project” schema; use planner store + session as source of truth.

---

## 3. Exact file plan

| Area | Action | Path |
|------|--------|------|
| Models | Create | `src/workflow_dataset/supervised_loop/models.py` — AgentCycle, QueuedAction, ApprovalQueueItem, ExecutionHandoff, LoopStatus, CycleSummary, BlockedCycleReason |
| Store | Create | `src/workflow_dataset/supervised_loop/store.py` — persist/load cycle, queue, queue history (data/local/supervised_loop/) |
| Next action | Create | `src/workflow_dataset/supervised_loop/next_action.py` — propose next actions from goal, session, plan, skills, packs, trust |
| Queue | Create | `src/workflow_dataset/supervised_loop/queue.py` — enqueue proposal, list pending, approve/reject/defer, persist history |
| Handoff | Create | `src/workflow_dataset/supervised_loop/handoff.py` — on approve: build executor/planner call, run, record result, update cycle |
| CLI | Create | `src/workflow_dataset/supervised_loop/cli.py` — status, next, queue, approve, reject, defer, cycle-report (invoked from main cli) |
| Mission control | Modify | `src/workflow_dataset/mission_control/state.py` — add block `supervised_loop` (current_cycle, queued_count, latest_result, next_proposed) |
| Mission control report | Modify | `src/workflow_dataset/mission_control/report.py` — add [Supervised agent loop] section |
| Package init | Create | `src/workflow_dataset/supervised_loop/__init__.py` |
| Tests | Create | `tests/test_supervised_loop.py` — next-action proposal, queue approve/reject/defer, handoff, blocked, cycle summary |
| Docs | Create | `docs/M27E_M27H_SUPERVISED_AGENT_LOOP.md` — usage, samples, gaps |

No changes to planner/*, executor/*, teaching/* internals; only additive calls and one new package.

---

## 4. Safety / risk note

- **No hidden autonomy**: Execution happens only after explicit approve. No background execution or bypass of approval.
- **Trust/approval respected**: Proposed actions carry risk/trust/mode; handoff uses existing executor (checkpoints, approval registry, job policy). We do not add new execution paths that skip trust.
- **Visibility**: Cycle state and queue are persisted and shown in CLI and mission control; operator can always see what is proposed and what was approved/rejected/deferred.
- **Bounded scope**: First draft focuses on “one project/goal, one cycle, one queue”; no multi-tenant or cross-project automation.

---

## 5. What this block will NOT do

- **No hidden autonomous execution**: No agent that runs without operator approval.
- **No bypass of checkpoints**: Executor’s existing checkpoint and resume behavior is unchanged.
- **No rebuild of planner/executor/teaching**: Only consumption and wiring.
- **No replacement of existing agent_loop**: The assistive Q&A agent_loop remains; supervised loop is a separate package and CLI group (`agent-loop`).
- **No polish/optimization**: First draft; no UI polish, no retry/backoff, no rich conflict resolution.
- **No “run from planner” in executor**: Executor continues to take plan_ref (routine_id | job_id). The supervised loop will propose actions like “run job X” or “run routine Y” (derived from plan steps) and call existing executor run; optional “executor run --from-planner” can be added later elsewhere.

---

*Document generated before implementation. Implementation follows in Phases A–F.*
