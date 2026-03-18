# M45A–M45D Adaptive Execution — READ FIRST

## 1. What plan/execution/loop-like behavior already exists

- **Planner (M26A–M26D)**: `Plan`, `PlanStep`, `compile_goal_to_plan`; checkpoints, blocked_conditions, dependency edges; **no auto-execution**; preview-only; save/load latest plan. Steps have `step_class` (reasoning_only, local_inspect, sandbox_write, trusted_real_candidate, human_required, blocked), `approval_required`, `checkpoint_before`.
- **Executor (M26E–M26H)**: `ExecutionRun`, `ActionEnvelope`; `run_with_checkpoints(plan_source, plan_ref, mode)` runs steps sequentially; stops at checkpoints (`awaiting_approval`), stops on first blocked; persists run to hub; `BlockedStepRecovery` (retry/skip/substitute/record_correction). No max-step cap or branching.
- **Operator mode (M35E–M35H)**: `DelegatedResponsibility` with `review_gates`, `stop_conditions`, `escalation_conditions`; pause/revoke; `explain_work_impact` (what stops/continues/human takeover). Not wired to a running loop instance.
- **Automations (M34A–M34D)**: `RecurringWorkflowDefinition` with `stop_conditions`, `approval_points`, `execution_mode`; triggers; no in-loop adaptation.
- **Background run (M34E–M34H)**: `pick_eligible_job`, `run_one_background`, simulate_first, gating; single-job runs, no multi-step loop abstraction.
- **Trust**: Contracts with `required_approvals`, `required_review_gates`; tiers with `approval_required`; cockpit for approval readiness.
- **Shadow execution (M45E–M45H)**: `ShadowRun`, expected/observed outcomes, `ConfidenceScore`, `GateType` (e.g. MUST_STOP_LOOP, MUST_HANDOFF_HUMAN). Intervention gates exist but are not yet the driver of a bounded adaptive loop API.
- **Memory intelligence (M44I–M44L)**: `enrich_planning_sources` (prior cases), `build_memory_backed_recommendations`, `retrieve_for_context`. Used for recommendations, not yet for loop generation or step adaptation.
- **Triage loop**: Evidence surfacing, grouping, routing — not an execution loop.

## 2. What is missing for safe adaptive multi-step execution

- **Explicit adaptive execution plan**: A plan that can declare branches, fallback paths, and adaptation triggers (e.g. on outcome or confidence).
- **Bounded execution loop**: A single abstraction (loop instance) with **max_steps**, **required_reviews**, **allowed/forbidden actions**, **stop conditions**, **escalation conditions**, **fallback behavior**, and **human-takeover points**.
- **Loop generation from multiple inputs**: From project goals, trusted routines, operator responsibilities, **memory-backed prior cases**, and runtime/model availability — producing one bounded loop spec.
- **Adaptive step progression**: Next-step advance, **branch if outcome changes**, **stop if confidence drops**, **escalate if blocked**, **switch to fallback** when trust/runtime conditions change.
- **Inspectable loop state**: Active loop id, current step index, current branch, remaining safe steps, next takeover/review point, and clear stop/escalation reason for mission control and CLI.

## 3. Exact file plan

| Area | Action |
|------|--------|
| **Phase A** | `src/workflow_dataset/adaptive_execution/models.py` — AdaptiveExecutionPlan, BoundedExecutionLoop, ExecutionStep, PlanBranch, StepOutcome, AdaptationTrigger, StopCondition, EscalationCondition, HumanTakeoverPoint. |
| **Phase B** | `src/workflow_dataset/adaptive_execution/generator.py` — Generate bounded loop from goal, routine, operator responsibility, memory prior cases, runtime availability; define max_steps, required_reviews, allowed/forbidden, fallback, stop/escalation. |
| **Phase C** | `src/workflow_dataset/adaptive_execution/progression.py` — advance_step, branch_on_outcome, stop_on_condition, escalate, switch_fallback; integrate with executor/trust/shadow where applicable. |
| **Phase C** | `src/workflow_dataset/adaptive_execution/store.py` — save/load active loop state (by loop_id); list active loops. |
| **Phase D** | `src/workflow_dataset/adaptive_execution/mission_control.py` — slice for mission control: active loop, next step, remaining steps, takeover point, branch/fallback. |
| **Phase D** | `src/workflow_dataset/cli.py` — New group `adaptive-execution`: plans, show, explain, step, stop. |
| **Phase D** | `src/workflow_dataset/mission_control/state.py` + `report.py` — Add adaptive_execution_state; report section. |
| **Phase E** | `tests/test_adaptive_execution.py` — Plan creation, bounded loop enforcement, branch/fallback, stop/escalation, no-loop/invalid-loop, blocked-step. |
| **Phase E** | `docs/M45_ADAPTIVE_EXECUTION_DELIVERABLE.md` — Files, CLI, samples, tests, gaps. |

## 4. Safety/risk note

- **Do not** introduce hidden autonomy: every loop has explicit max_steps and required reviews; stop and escalation conditions are first-class and reported.
- **Do not** bypass trust/approval: allowed/forbidden actions and takeover points must align with existing trust contracts and approval registry.
- **Do not** create unbounded recursion: loop advancement is step-by-step; branching chooses from predeclared branches/fallbacks, not arbitrary new plans.
- **Risk**: If generator or progression logic mislabels a step as allowed or misses a takeover point, real actions could run without intended review. Mitigation: use existing executor/checkpoint and trust checks when executing a step; treat adaptive_execution as a **supervisory layer** that produces and advances a bounded plan, while actual execution still goes through `run_with_checkpoints` or equivalent.

## 5. Loop-boundary principles

- **Bounded**: Every loop has a fixed max_steps; after max_steps the loop must stop or escalate.
- **Review points**: Required reviews (e.g. before step indices) are explicit; progression pauses at those points until a decision is recorded.
- **Stop/escalate**: Stop conditions (e.g. confidence_below, blocked_step, manual_stop) and escalation conditions (e.g. blocked, policy_change) are declared and evaluated each step; when triggered, loop state is updated and no further steps run until operator intervenes.
- **Fallback**: A fallback path (e.g. safer plan or “human_only” branch) is declared; switching to fallback is explicit and logged.
- **Inspectable**: Loop id, status, current step, branch, remaining steps, next_review_step, and stop/escalation reason are always available for CLI and mission control.

## 6. What this block will NOT do

- **Will NOT** implement hidden or unbounded autonomous agent loops.
- **Will NOT** replace the executor or planner; it will **use** them (e.g. compile_goal_to_plan, run_with_checkpoints) and add an adaptive loop layer on top.
- **Will NOT** add cloud execution or remote orchestration.
- **Will NOT** weaken approval/checkpoint requirements; it will only declare and respect them.
- **Will NOT** auto-execute steps without going through existing executor/approval gates; step advancement may call executor with the same constraints.

---

Proceeding to implement Phases A–E.
