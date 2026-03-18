# M33E–M33H — Supervised Real-Time Workflow Runner: Before-Coding Analysis

## 1. What real-time assist and workflow surfaces already exist

- **planner/**  
  - **Plan**, **PlanStep**, **Checkpoint**, **ExpectedArtifact**, **BlockedCondition**, **ProvenanceSource**; **compile_goal_to_plan(goal, repo_root, mode)**; **gather_planning_sources** (session, jobs, routines, macros, task demos, packs).  
  - Step classes: reasoning_only, local_inspect, sandbox_write, trusted_real_candidate, human_required, blocked.

- **executor/**  
  - **ActionEnvelope**, **ExecutionRun**, **CheckpointDecision**, **BlockedStepRecovery**; run state (running, paused, awaiting_approval, blocked, completed, cancelled).  
  - No direct “live” API; execution is plan-driven.

- **assist_engine/**  
  - **AssistSuggestion**, **SuggestionType** (next_step, draft_summary, blocked_review, resume_routine, open_artifact, use_preference, remind), **TriggeringContext**, **SuggestionReason**; **generate_assist_suggestions**; queue with **apply_policy**, **list_suggestions**, snooze/dismiss/accept.  
  - Suggestion-only; no step sequence or escalation tiers.

- **action_cards/**  
  - **ActionCard**, **HandoffTarget** (open_view, prefill_command, queue_simulated, approval_studio, create_draft, compile_plan, executor_run), **CardState**, **TrustRequirement**; **execute_handoff(card_id)** → planner compile, queue_simulated, prefill, etc.  
  - Cards are created from suggestions or other sources; handoff is explicit and supervised.

- **supervised_loop/** (agent-loop)  
  - Propose next → approval queue → approve/reject/defer → execute only approved; **QueuedAction**, **enqueue_proposal**, cycle report.  
  - Not wired to “live” step-by-step during an episode.

- **live_context/** (M32)  
  - **ActiveWorkContext** (inferred_project, activity_mode, focus_state, work_mode); **fuse_active_context_from_sources**; state persisted.  
  - No mapping to a workflow plan or step sequence.

- **session/**  
  - **Session** (active_tasks, active_job_ids, active_routine_ids, active_macro_ids); get_current_session, board.  
  - Used by planner sources; not a “live workflow run” state.

- **mission_control/**  
  - State and report include product, evaluation, development, observation, live_context, job_packs, copilot, etc.  
  - No “active live workflow” or “current step / escalation” slice.

- **trust / approvals / policy**  
  - Trust modes, approval registry, policy presets; used by executor and action cards.  
  - No change required; we consume them.

**Workflow-episode tracker (Pane 1):** Not present in repo; assumed future. We will consume “active workflow” via: live context + optional goal/routine_id/job_id and derive a supervised path from planner when possible.

---

## 2. What is missing for a true supervised real-time workflow runner

- **Explicit “supervised live workflow” model**: No single object that represents an active real-time workflow run (goal/routine ref, plan ref, current step index, escalation level, blocked step, run state).  
- **Step sequence for live use**: No “current step + next step + alternate path + escalation path” generated from plan + context for real-time display.  
- **Escalation tiers**: No bounded ladder (hint → action-card → draft → planner prefill → simulated handoff → review routing); assist_engine and action_cards exist but are not organized as tiers.  
- **Mapping episode → plan**: No component that takes “active context + goal or routine” and produces a supervised workflow path (steps, escalation path, blocked handling).  
- **Blocked/stalled handoff**: No explicit “blocked real-time step” with handoff to planner/executor/review (BlockedStepRecovery exists in executor but not wired to a live workflow UX).  
- **CLI and mission control**: No `live-workflow now`, `steps --latest`, `escalate --latest`, `preview-next`, or mission-control visibility for active live workflow and escalation.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| **Create** | `src/workflow_dataset/live_workflow/__init__.py` — exports. |
| **Create** | `src/workflow_dataset/live_workflow/models.py` — SupervisedLiveWorkflow, LiveStepSuggestion, EscalationTier, WorkflowRunState, BlockedRealTimeStep, expected artifact/handoff, checkpoint requirement. |
| **Create** | `src/workflow_dataset/live_workflow/step_generator.py` — Build step sequence from live context + goal/routine + planner output; current step, next step, alternate path, escalation path. |
| **Create** | `src/workflow_dataset/live_workflow/escalation.py` — Escalation tiers (hint → action-card → draft → planner prefill → simulated handoff → review); next tier for current step; handoff builders. |
| **Create** | `src/workflow_dataset/live_workflow/state.py` — Persist/load current live workflow run (data/local/live_workflow). |
| **Modify** | `src/workflow_dataset/cli.py` — Add **live_workflow_group** with: now, steps --latest, escalate --latest, preview-next --latest. |
| **Modify** | `src/workflow_dataset/mission_control/state.py` — Add **live_workflow_state** (active run, current step, escalation level, blocked step, next recommended assist). |
| **Modify** | `src/workflow_dataset/mission_control/report.py` — Add [Live workflow] section. |
| **Create** | `docs/M33_LIVE_WORKFLOW.md` — Model, step gen, escalation, CLI, samples, gaps. |
| **Create** | `tests/test_live_workflow.py` — Plan generation from context, escalation tier behavior, blocked handoff, empty workflow, safe handoff to planner/executor. |

---

## 4. Safety/risk note

- **Risk**: Real-time guidance could be perceived as autopilot or could push users into unsafe actions.  
- **Mitigation**: (1) All actions remain previewable and hand off to existing planner/executor/approval flows; no hidden execution. (2) Escalation is explicit and tiered; no auto-execute from this layer. (3) Blocked steps route to existing BlockedStepRecovery and approval surfaces. (4) We do not bypass trust/approval/policy; we only suggest and hand off.  
- **Residual**: Step and escalation logic are heuristics; always present “why” and allow dismiss/snooze.

---

## 5. Escalation principles

- **Lowest friction first**: Prefer hint → then action-card suggestion → then draft/handoff prep → then planner goal prefill → then simulated run handoff → then review/approval routing.  
- **Explicit and supervised**: Every tier is visible; user chooses to act.  
- **Blocked/stalled**: When step is blocked or no progress, offer next tier (e.g. “Create action card” or “Open planner with goal”) and record blocked step for handoff.  
- **No auto-escalation without user signal**: Escalation tier is suggested; user or policy can request “escalate” (e.g. CLI `live-workflow escalate --latest`).

---

## 6. What this block will NOT do

- Will **not** run workflows autonomously or hide execution.  
- Will **not** bypass trust, approval, or policy gates.  
- Will **not** implement the workflow-episode tracker (Pane 1); we consume live context + optional goal/routine.  
- Will **not** replace planner, executor, or action_cards; we map into them and hand off.  
- Will **not** add new approval or trust primitives; we use existing ones.
