# M28E–M28H — Bounded Worker Lanes + Delegated Subplans — Pre-coding analysis

## 1. What task/plan decomposition already exists

- **planner/schema.py** — Plan (steps, edges, checkpoints, expected_artifacts, blocked_conditions), PlanStep with step_class, provenance. Single plan per goal; no subplan or lane.
- **planner/compile.py** — compile_goal_to_plan(goal) produces a Plan from jobs, routines, macros, session. No decomposition into delegated subplans.
- **planner/store.py** — save/load current_goal, save/load latest_plan (one plan).
- **executor/** — ExecutionRun, ActionEnvelope, save_run, load_run, list_runs. Runs are plan-based; no lane or delegated-subplan concept.
- **project_case/** — Project, Goal, Subgoal (hierarchy); LinkedPlan, LinkedRun, LinkedArtifact. No worker lane or delegated subplan.
- **supervised_loop/** — AgentCycle, QueuedAction, ApprovalQueueItem, ExecutionHandoff. Handoff is executor result; no lane handoff.
- **teaching/** — Skills (accepted/draft); no assignment to lanes.
- **outcomes/** — SessionOutcome, task outcomes; no lane results.

## 2. What is missing for safe delegated worker lanes

- **Worker lane model** — Explicit record: lane_id, project_id, goal_id, scope, permissions, status, created/updated, parent_plan_ref. No lane entity today.
- **Delegated subplan** — Bounded subplan with explicit scope, expected_outputs, trust/approval mode, stop_conditions. Not derived from Plan or goals today.
- **Lane scope / permissions** — Narrow scope (e.g. extract_only, summarize_only); permissions (simulate_only, trusted_real_if_approved). Not modeled.
- **Lane artifact/result and handoff** — Return artifacts and a lane summary to the parent project/loop; handoff record. Executor has artifacts per run but no lane handoff.
- **Lane failure/blocked** — Reason and step for lane-level blocked/failed. Plan has blocked_conditions; no lane-level blocked.
- **Subplan generation** — Create delegated subplans from active goals, planner output, accepted skills, pack defaults, context. Not implemented.
- **Lane execution** — Simulate subplan, optionally hand steps to executor, collect results, return summary. Not implemented.
- **CLI and mission control** — lanes list, create, status, results, close; visibility for active/blocked lanes, results awaiting review, parent→lane mapping.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `lanes/__init__.py` |
| Create | `lanes/models.py` — WorkerLane, DelegatedSubplan, LaneScope, LanePermissions, LaneStatus, LaneArtifact, LaneHandoff, LaneFailure/blocked. |
| Create | `lanes/store.py` — get_lanes_dir, save_lane, load_lane, list_lanes (by project/status). data/local/lanes/. |
| Create | `lanes/subplan.py` — create_delegated_subplan(project_id, goal_id, scope, ...) from planner/context/skills; explicit scope, expected_outputs, trust_mode, stop_conditions. |
| Create | `lanes/execution.py` — run_lane_simulate(lane_id), collect_lane_results(lane_id), build_lane_summary(lane_id); optional handoff to executor. |
| Modify | `cli.py` — lanes_group: list, create, status, results, close. |
| Modify | `mission_control/state.py` — lanes section: active_lanes, blocked_lanes, results_awaiting_review, parent_project_to_lanes, next_handoff_needed. |
| Modify | `mission_control/report.py` — [Worker lanes] section. |
| Create | `tests/test_lanes.py` |
| Create | `docs/M28E_M28H_WORKER_LANES.md` |

## 4. Safety/risk note

- Lanes are bounded and explicit: scope and permissions are stored; no open-ended autonomy.
- Lane execution respects approval/capability: simulate-only or trusted_real only when allowed; no bypass of trust/approval.
- Results and handoffs are inspectable; state under data/local/lanes.
- No hidden background swarms; operator can list and close lanes.

## 5. What this block will NOT do

- No open-ended multi-agent chaos; no independent agents with no operator visibility.
- No bypass of policy/trust/approval rules.
- No rebuild of planner/executor/supervised_loop; additive only.
- No automatic creation of lanes without explicit create command or documented flow.
