# M27E–M27H Supervised Agent Loop

First-draft human-in-the-loop agent: select project/goal → compile/refresh plan → propose next actions → **approval queue** → execute only approved → update cycle → repeat.

## CLI usage

```bash
# Status: current cycle, queue counts, last handoff, next proposed
workflow-dataset agent-loop status

# Propose next actions and add to queue (optionally for a project slug)
workflow-dataset agent-loop next
workflow-dataset agent-loop next --project founder_case_alpha

# Show pending approval queue (why / risk / mode)
workflow-dataset agent-loop queue

# Approve and run (or approve only with --no-execute)
workflow-dataset agent-loop approve --id q_xxx
workflow-dataset agent-loop approve --id q_xxx --no-execute

# Reject or defer
workflow-dataset agent-loop reject --id q_xxx
workflow-dataset agent-loop defer --id q_xxx

# Cycle report (latest)
workflow-dataset agent-loop cycle-report
workflow-dataset agent-loop cycle-report --latest
```

All commands accept `--repo-root <path>` to override repo root.

## Sample queued action

A proposed action in the queue looks like:

- **queue_id**: `q_abc123...`
- **label**: `Run job: weekly_status_from_notes`
- **action_type**: `executor_run` | `planner_compile` | `executor_resume`
- **plan_ref**: routine_id or job_pack_id
- **plan_source**: `routine` | `job`
- **mode**: `simulate` | `real`
- **why**: e.g. `Next step from plan: job weekly_status_from_notes (goal: Ship weekly report)`
- **risk_level**: `low` | `medium` | `high`
- **trust_mode**: `simulate` | `trusted_real_candidate`

## Sample approval queue output

```
Approval queue (pending)
  q_abc123  Run job: weekly_status_from_notes
    type=executor_run  plan_ref=weekly_status_from_notes  mode=simulate
    why: Next step from plan: job weekly_status_from_notes  risk=medium
    approve: workflow-dataset agent-loop approve --id q_abc123
```

## Sample cycle report

```
=== Cycle report ===
cycle_id: cy_xyz
project: founder_case_alpha
goal: Ship weekly stakeholder update
status: awaiting_approval
blocked: —
pending: 1  approved: 2  rejected: 0  deferred: 0
last_handoff: completed  last_run_id: run_abc
next_proposed: Run job: weekly_status_from_notes (id: q_abc123)
```

## Sample approved execution handoff output

After `agent-loop approve --id q_xxx` (with execution):

```
Approved q_xxx
  handoff_id: h_yyy  status: completed  run_id: run_zzz
  outcome: executed=1 blocked=0 Paused at checkpoint before step 1. Resume: workflow-dataset executor resume --run run_zzz
```

If the run pauses at a checkpoint, `last_run_id` and cycle status are updated; next `agent-loop next` can propose "Resume executor run run_zzz".

## Mission control

`workflow-dataset mission-control` includes a **[Supervised agent loop]** section:

- cycle_id, project_slug, status
- blocked_reason (if any)
- queue: pending / approved / rejected / deferred counts
- last_handoff_status, last_run_id
- next_proposed_action_label and hint: `agent-loop approve --id <id>`

State key: `supervised_loop`. Source path: `data/local/supervised_loop`.

## Persistence

- **Cycle**: `data/local/supervised_loop/current_cycle.json`
- **Queue**: `data/local/supervised_loop/approval_queue.json`
- **Queue history**: `data/local/supervised_loop/queue_history.json`
- **Handoffs**: `data/local/supervised_loop/handoffs.json`

## Tests run

```bash
pytest tests/test_supervised_loop.py -v --tb=short
```

Covers: cycle roundtrip, save/load cycle, next-action proposal (no plan), enqueue/list_pending, approve/reject/defer, approve nonexistent, build_cycle_summary, handoff planner_compile, cycle summary after handoff, BlockedCycleReason.

## Remaining gaps (for later refinement)

1. **Project/case contract**: Loop uses planner current_goal + optional project_slug; no deep integration with project_case (e.g. goal stack) yet.
2. **Skills/packs in “why”**: Next-action proposal does not yet cite accepted skills or value packs in the reason text.
3. **Trust in risk_level**: risk_level is set generically (e.g. medium for executor_run); could be driven by trust cockpit / job policy.
4. **Executor run --from-planner**: Executor still takes plan_ref (routine_id | job_id). Loop derives these from plan steps; a direct “run from planner” path in the executor is optional future work.
5. **Session/outcome updates**: After handoff we update cycle and last_run_id; we do not yet write session outcomes or update session recommended_next_actions.
6. **No retry/backoff**: Single execution attempt; no automatic retry or richer recovery.
7. **One cycle per repo**: Current design is one active cycle (current_cycle.json); multi-project would need cycle-per-project or scope in queue.
