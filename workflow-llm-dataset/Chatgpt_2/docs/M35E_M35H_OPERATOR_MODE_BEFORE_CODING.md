# M35E–M35H Personal Operator Mode + Governed Delegation — Before Coding

## 1. What delegation / operator-like pieces already exist

| Area | What exists | Limitation for “personal operator mode” |
|------|-------------|----------------------------------------|
| **automations/** | TriggerDefinition, RecurringWorkflowDefinition, evaluate_active_triggers, guardrail profiles, templates. Triggers → workflows; store under `data/local/automations/`. | No first-class “delegated responsibility” or “operator mode profile”; triggers/workflows are not bound to an explicit authority tier or escalation path. |
| **background_run/** | QueuedRecurringJob, pick_eligible_job, run_one_background, evaluate_background_policy (gating). Queue + run under policy/trust. | Queue is job-centric; no “delegated responsibility” entity, no suspend/revoke at responsibility level, no unified operator cycle. |
| **human_policy/** | PolicyEvalResult (may_delegate, simulate_only, blocked), OverrideRecord, action_class policies (execute_simulate, execute_trusted_real, delegate_goal, use_worker_lanes). | Governs actions; no operator-mode profile or “delegated responsibility” with binding to authority/review gates. |
| **lanes/** | LaneScope, LanePermissions, delegated subplans, lane status (open/running/blocked/completed). Worker lanes with project scope. | Bounded delegation for a lane/task; not a recurring “personal operator” responsibility with morning/continuity/sweep semantics. |
| **supervised_loop/** | AgentCycle, QueuedAction, ApprovalQueueItem, ExecutionHandoff, OperatorPolicy. Propose → approve → execute; project/goal-scoped. | Single-cycle, project/goal focused; no persistent “delegated responsibility” or operator mode that spans sessions. |
| **trust/** | TrustCockpit, approval readiness, release gates. Read-only. | Advisory only; no “authority tier” or “contract” model. |
| **job_packs/** | trust_level, check_job_policy. Per-job trust. | No authority tier or trusted routine contract. |
| **mission_control/** | Report expects `automations_state` (active/suppressed/blocked triggers, next_scheduled); `background_runner_state`; `automation_inbox`. | `automations_state` is not currently populated in `state.py` (report uses empty dict). No operator_mode or delegated responsibilities section. |
| **workspace/** | ActiveWorkContext, build_active_work_context. Aggregates project, goal, session. | No operator mode or delegated responsibility visibility. |
| **planner/** | compile goal → Plan, steps, checkpoints. | No operator-mode entry point. |
| **executor/** | Run plan steps, approval checkpoints. | No operator-mode entry point. |
| **portfolio/** | Priority stack, next recommended project. | No delegation binding. |
| **sessions/** | Session board, artifacts. | No operator mode. |

---

## 2. What is missing for a real governed personal operator mode

- **Operator mode profile**  
  Explicit “operator mode” entity: on/off, scope (which projects/packs/routines), reference to authority tier, default review gates. Today there is no single place that says “these responsibilities are under operator mode with this governance.”

- **Delegated responsibility**  
  First-class entity that represents a recurring responsibility (e.g. morning digest, approval sweep, blocked-work follow-up, refresh project state, stage drafts, follow-up queue, resume-work continuity). Each must bind to:
  - project_id / pack_id / routine_id (or global)
  - authority_tier_id (placeholder for Pane 1)
  - review_gates (e.g. before_real, before_send)
  - stop_conditions, escalation_conditions  
  Automations have triggers+workflows but not this governance binding; lanes have scope but not “recurring responsibility” with escalation.

- **Governed operator cycle**  
  A single cycle that: (1) evaluates which delegated responsibilities are eligible, (2) chooses the next governed action (one at a time), (3) queues that action under the correct gate (background / supervised / approval), (4) escalates blocked or uncertain work to human review, (5) can suspend or revoke delegation when boundaries are violated.  
  Today: background picks from a job queue; supervised_loop proposes next action for one cycle. No unified “operator cycle” over multiple delegated responsibilities with suspension/revocation.

- **Authority binding**  
  Reference from delegated responsibility to “authority tier” or “trusted routine contract” (Pane 1). No such model in repo yet; we add a placeholder (e.g. `authority_tier_id: str`) and optional contract_ref.

- **Escalation path**  
  Explicit escalation conditions and a clear “awaiting review” set for operator actions. live_workflow has escalation tiers; automation_inbox has needs_review; we need a single place for “operator escalation” for delegated responsibilities (e.g. blocked, policy_denied, uncertainty).

- **Suspension / revocation state**  
  Ability to mark a delegated responsibility as suspended (temporarily ineligible) or revoked (removed from operator mode until re-delegated). Guardrails suppress triggers; we need explicit suspension/revocation at the responsibility level, with reason and optional expiry.

- **Operator mode summary**  
  One place (CLI + mission control) to see: active delegated responsibilities, suspended/revoked, next governed action, responsibilities awaiting review, top escalation candidate. Today this is spread across automations, background_runner, automation_inbox.

---

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|--------|
| **Create** | `src/workflow_dataset/operator_mode/models.py` | OperatorModeProfile, DelegatedResponsibility, GovernedOperatorFlow (or FlowStep), AuthorityBinding, EscalationPath, SuspensionRevocationState, OperatorModeSummary. |
| **Create** | `src/workflow_dataset/operator_mode/store.py` | Persist profiles and responsibilities (e.g. `data/local/operator_mode/profiles/*.json`, `responsibilities/*.json`); list/get/save; get_active_profile; get/set suspension/revocation state. |
| **Create** | `src/workflow_dataset/operator_mode/responsibilities.py` | Responsibility kinds (recurring_summary, approval_sweep, refresh_state, stage_drafts, follow_up_queue, morning_continuity, resume_continuity); helpers to create/bind to project/pack/routine, authority_tier_id, review_gates, stop_conditions, escalation_conditions. |
| **Create** | `src/workflow_dataset/operator_mode/cycle.py` | Evaluate delegated responsibilities → eligible next actions; pick next governed action; queue under appropriate gate (bridge to background_run / supervised_loop / approval); escalate blocked/uncertain; apply suspension/revocation when boundaries violated; build OperatorModeSummary. |
| **Create** | `src/workflow_dataset/operator_mode/cli.py` | Commands: status, responsibilities, delegate, suspend, resume, revoke, explain. (CLI module; register under main app in cli.py.) |
| **Create** | `src/workflow_dataset/operator_mode/__init__.py` | Public API exports. |
| **Modify** | `src/workflow_dataset/mission_control/state.py` | Add `operator_mode_state`: active_responsibility_ids, suspended_responsibility_ids, revoked_responsibility_ids, next_governed_action (id/label/gate), awaiting_review_responsibility_ids, top_escalation_candidate (id/reason). Source from operator_mode cycle/summary. |
| **Modify** | `src/workflow_dataset/mission_control/report.py` | Add **[Operator mode]** section: active/suspended/revoked counts, next governed action, awaiting review, top escalation. |
| **Modify** | `src/workflow_dataset/cli.py` | Register `operator_mode` group and commands (status, responsibilities, delegate, suspend, explain, etc.). |
| **Data** | `data/local/operator_mode/profiles/*.json`, `responsibilities/*.json` | Sample profile and sample delegated responsibility. Optional `state.json` for active_profile_id and suspension/revocation list. |
| **Create** | `tests/test_operator_mode.py` | Tests: models, store, responsibility creation, eligibility, suspension/revocation, escalation, summary. |
| **Create** | `docs/M35E_M35H_OPERATOR_MODE.md` | Deliverable doc: files, CLI, samples, tests, remaining gaps. |

No new top-level “authority” or “contracts” package in this block; Pane 1 will define those. We only reference `authority_tier_id` (and optional `contract_ref`) as strings on DelegatedResponsibility.

---

## 4. Safety / risk note

- **Do not bypass existing gates.** Operator mode must call existing evaluation: `evaluate_background_policy`, human_policy `evaluate`, approval registry, trust cockpit. The cycle only queues or proposes actions that are already allowed by those layers.
- **No new always-on autonomy.** Actions remain “queued” or “proposed” until the existing approval/execution path is used (background run, agent-loop approve, etc.). No hidden self-directed execution.
- **Suspension/revocation are explicit.** Triggered by operator command or by a clear boundary (e.g. escalation_condition met); state is persisted and visible in CLI/mission control. No silent disable.
- **Escalation is visible.** Blocked or uncertain work is surfaced as “awaiting review” and “top escalation candidate,” not auto-resolved.

---

## 5. What this block will NOT do

- **Implement Pane 1 authority tiers or trusted routine contracts.** Only reference them by id (e.g. `authority_tier_id`, optional `contract_ref`). No schema or store for tiers/contracts.
- **Implement Pane 3 commit/send/apply gates or audit requirements.** Only reference “review gates” by name (e.g. before_real, before_send). No implementation of those gates.
- **Replace or rebuild** background_run, automations, supervised_loop, lanes. We extend and wire only (e.g. operator cycle picks next action and enqueues to background or supervised_loop).
- **Add a real scheduler/cron.** Eligibility is “what would run next” / “next governed action”; actual execution remains via existing background run or agent-loop. No new daemon.
- **Add UI.** CLI and mission control text only.
- **Populate `automations_state` in mission_control.** That can be done in a separate small change; this block focuses on operator_mode_state and operator mode layer.

---

*Do not code until this is complete. Proceed to Phase A (models) after review.*
