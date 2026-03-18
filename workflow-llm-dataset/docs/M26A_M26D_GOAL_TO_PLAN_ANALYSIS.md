# M26A–M26D Goal-to-Plan Compiler — Pre-Coding Analysis

## 1. What planning-related components already exist

| Area | What exists |
|------|-------------|
| **Session** | `Session` (session_id, value_pack_id, active_tasks, active_job_ids, active_routine_ids, active_macro_ids, current_artifacts, notes, state); `SessionBoard` (active_tasks, queued, blocked, ready, completed, artifacts_produced); `build_session_board(session, repo_root)` aggregates from copilot, macros, job_packs, session artifacts. |
| **Copilot plan** | `PlanPreview` (plan_id, job_pack_ids, mode, approvals_required, trusted_actions_involved, expected_outputs, blocked, blocked_reasons, step_previews, created_at); `build_plan_for_job(job_pack_id, mode, params, repo_root)`, `build_plan_for_routine(routine_id, mode, repo_root)` — job/routine-centric, no goal input. |
| **Job packs** | `JobPack` (job_pack_id, title, expected_outputs, trust_level, required_approvals, coordination_graph_ref, …); `list_job_packs`, `get_job_pack`, `preview_job`, `check_job_policy`; job_packs_report (recent_successful, trusted_for_real, approval_blocked, etc.). |
| **Macros** | `Macro`, `MacroStep` (job_pack_id, step_type, trust_requirement, checkpoint_before, expected_outputs); step types: safe_inspect, sandbox_write, trusted_real, blocked, human_checkpoint; `classify_step(job_pack_id, mode, repo_root)`; runner with paused/awaiting_approval runs, get_blocked_steps. |
| **Task demos** | `TaskDefinition` (task_id, steps), `TaskStep` (adapter_id, action_id, params); `list_tasks`, `get_task`; coordination_graph `task_definition_to_graph(task)` → CoordinationGraph (nodes, edges). |
| **Coordination graph** | `CoordinationGraph`, `GraphNode`, `GraphEdge`; `task_definition_to_graph`; advisory only. |
| **Context** | `WorkState` (recent_successful_jobs, trusted_for_real_jobs, routines, task_demos_count, …); `build_work_state(repo_root)`. |
| **Copilot recommendations** | `recommend_jobs(repo_root, limit, context_snapshot)` — returns job recommendations with reason, blocking_issues, mode_allowed. |
| **Trust** | `build_trust_cockpit(repo_root)` — benchmark_trust, approval_readiness, job_macro_trust_state. |
| **CLI** | `copilot plan` (--job / --routine, mode) → PlanPreview for a single job or routine; `planner` group exists for **product evolution** (recommend-next, shortlist, build-brief, build-rfc). No goal-string → plan flow. |
| **Mission control** | `active_session` block (session_id, pack_id, queued_count, blocked_count, ready_count, artifacts_count, recommended_next_session_action). No “current goal” or “latest compiled plan” block. |

## 2. What is missing for a true goal-to-plan compiler

- **Goal request schema** — No first-class “goal” or “operator intent” type; copilot plan is keyed by job/routine id, not by free-form goal text.
- **Goal → plan compilation** — No path from a goal string (e.g. “Prepare weekly stakeholder update”) to an ordered plan that uses session state, pack behavior, jobs, routines, macros, task demos, and coordination graph. Need: goal parsing or matching, selection of relevant jobs/routines/macros/demos, ordering, dependency edges.
- **Explicit work graph / plan schema** — PlanPreview is job-list + blocked; no explicit “plan step” with dependency edges, checkpoints, expected artifact, blocked condition, required approval, provenance (source job/macro/demo/pack).
- **Step classification in a plan** — Macros have step_classifier per step; no unified “plan step” type that carries reasoning_only | local_inspect | sandbox_write | trusted_real_candidate | human_required | blocked.
- **Plan explanation / preview** — No “why this plan”, “what sources influenced it”, “what packs/skills/macros reused”, “where human approval required”, “expected outputs” as a single explanation view.
- **Persistence of “current goal” and “latest plan”** — No stored “active goal” or “latest compiled plan” for preview/explain/graph without re-compiling.
- **CLI** — No `planner compile --goal "..."`, `planner preview --latest`, `planner explain --latest`, `planner graph --latest`.
- **Mission control** — No block for active goal, latest plan summary, blocked plan steps, next checkpoint, expected artifacts.

## 3. Exact file plan

| Phase | Action | Files |
|-------|--------|-------|
| A | Schemas | **Create** `planner/schema.py`: GoalRequest, Plan, PlanStep, DependencyEdge, Checkpoint, ExpectedArtifact, BlockedCondition, RequiredApproval, ProvenanceSource (job_id, macro_id, task_id, pack_id, routine_id). |
| B | Compilation | **Create** `planner/compile.py`: `compile_goal_to_plan(goal, repo_root)` — load session, work_state, recommend_jobs, routines, macros, task_demos, pack behavior summary; match goal to jobs/routines/macros/demos (keyword or tag match first draft); build ordered steps, dependency edges, checkpoints from macro/routine structure; set blocked from policy/cockpit; attach provenance; return Plan. **Create** `planner/sources.py`: helpers to gather session, jobs, routines, macros, demos, pack context for compiler. |
| C | Step classification | **Create** `planner/classify.py`: `classify_plan_step(step, repo_root)` — map to reasoning_only | local_inspect | sandbox_write | trusted_real_candidate | human_required | blocked; use job trust_level, macro step_type, policy. Integrate into Plan compilation so each PlanStep has step_class. |
| D | Explanation / preview | **Create** `planner/explain.py`: `explain_plan(plan)` → text/markdown: why chosen, sources influenced, packs/skills/macros reused, blocked, human approval required, expected outputs. **Create** `planner/preview.py`: `format_plan_preview(plan)`, `format_plan_graph(plan)` for CLI. |
| E | Persistence | **Create** `planner/store.py`: save/load current_goal and latest Plan under `data/local/planner/` (e.g. current_goal.txt, latest_plan.json). |
| E | CLI | **Modify** `cli.py`: add to existing `planner_group`: `planner compile --goal`, `planner preview --latest`, `planner explain --latest`, `planner graph --latest`. |
| E | Mission control | **Modify** `mission_control/state.py`: add block `goal_plan` (active_goal, latest_plan_id, plan_step_count, blocked_step_count, next_checkpoint_index, expected_artifacts). **Modify** `mission_control/report.py`: add [Goal / plan] section. |
| F | Tests + docs | **Create** `tests/test_goal_plan_compiler_m26.py`: goal schema, plan compilation (mock sources), dependency graph, blocked handling, explain output. **Create** `docs/M26A_M26D_GOAL_TO_PLAN.md`: files, CLI, sample goal/plan/explanation/graph, tests, gaps. |

## 4. Safety / risk note

- **No auto-execution** — Compiler only produces a plan; no execution in this block. Execution remains with existing copilot run / macro runner / job execution.
- **Trust boundaries** — Step classification and “human_required” / “blocked” must use existing job_packs policy, macro step_classifier, and trust cockpit; do not relax approval or sandbox rules.
- **Goal matching** — First draft: keyword/tag match of goal text to job titles, routine ids, macro ids, task ids, pack workflow_tags; no LLM or opaque scoring. Reduces risk of suggesting wrong or unsafe steps.
- **Inspectable** — Plan, steps, dependencies, and explanation are all serializable and printable; operators can audit why a plan was chosen and what it would do.

## 5. What this block will NOT do

- **No hidden autonomous execution** — Plans are preview/explain/graph only; execution is out of scope.
- **No opaque reasoning-only prompts** — Explanation is derived from structured data (sources, blocked reasons, approvals); no free-form LLM “reasoning” blob.
- **No replacing job/macro systems** — Compiler consumes jobs, routines, macros, demos as inputs and references them in the plan; it does not replace or duplicate their execution.
- **No semantic goal understanding** — First draft uses keyword/tag matching and session/copilot context; no NLU or embedding-based goal parsing.
- **No plan execution** — No “run this plan” in this block; existing `copilot run` and macro runner remain the execution paths.
