# M28I–M28L Human Policy Engine + Override Board — Pre-Coding Analysis

## 1. What approval/trust/policy-like controls already exist

- **Trust (trust/)**: TrustCockpit aggregates benchmark trust, approval readiness, job/macro trust state, unresolved corrections, release gates. Read-only, advisory; no policy mutation. Safe-to-expand and gate checks inform operator but do not define “what the agent may do.”
- **Approval registry (capability_discovery/approval_registry.py)**: Local `approvals.yaml` — approved_paths, approved_apps, approved_action_scopes. Used by executor/desktop for capability checks. Not scoped by project/pack; no “always manual” or “may batch” rules.
- **Supervised loop OperatorPolicy (supervised_loop/)**: Batch-approve max risk, always_manual_review action types/risk/mode, defer_revisit. Scoped to the **agent-loop queue only** (which actions can be batch-approved). Does not govern routing, planning, delegation, or project/pack-level rules.
- **Runtime mesh policy (runtime_mesh/policy.py)**: Task-class → backend/model recommendation (desktop_copilot, codebase_task, etc.). Not governance; it’s runtime selection.
- **Release lanes (release/review_state.py, lane_views.py)**: Workspace/package lanes (operator, reviewer, stakeholder-prep, approver). Review workflow assignment, not agent autonomy policy.
- **Project/case (project_case/)**: Project, Goal, goal stack, links. No policy fields; no “simulate_only” or “manual_only” per project.
- **Executor/planner**: Checkpoints and job policy (simulate vs real, approval_blocked) come from job_packs and macros; no single operator-defined “this project is simulate-only.”

So: there are **building blocks** (trust, approval registry, queue-level operator policy, project/case identity) but **no unified human policy engine** that defines automatic vs approval-required, project/pack-level differences, overrides for routing/planning/delegation/execution, or a single review/override board.

---

## 2. What is missing for a real human policy engine

- **Multi-scope policy model**: Global, project, pack, task, lane scopes with explicit precedence (e.g. project overrides global, override overrides both).
- **Action-class and approval policies**: Which action classes (e.g. execute_trusted_real, delegate_goal, use_worker_lane) are always manual, may be batched, or allowed automatically under conditions.
- **Delegation and routing policy**: May this goal be delegated; may this project use worker lanes; routing priority overrides.
- **Blocked-action and exception policy**: Explicit blocked action list; exception policy (who can grant exceptions, expiry).
- **Override store**: Temporary overrides (scope + id + rule + expiry) with apply/revoke and audit.
- **Evaluation API**: Single place to ask “is this action always manual,” “may this be batched,” “may this project use lanes,” “must this project stay simulate-only,” “may this pack override defaults.”
- **Override board**: One surface to list active policy effects, show current overrides, apply/revoke overrides, and explain why a route/plan/action was blocked or allowed.
- **Mission control visibility**: Active policy restrictions, current overrides, blocked agent behaviors, high-impact intervention candidates.

---

## 3. Exact file plan

| Area | Action | Path |
|------|--------|------|
| Models | Create | `src/workflow_dataset/human_policy/models.py` — PolicyScope, ActionClassPolicy, ApprovalRequirementPolicy, DelegationPolicy, RoutingPriorityOverride, BlockedActionPolicy, ExceptionPolicy, OperatorPolicy (engine), OverrideRecord |
| Store | Create | `src/workflow_dataset/human_policy/store.py` — default policy JSON, overrides JSON, load/save/list overrides |
| Evaluation | Create | `src/workflow_dataset/human_policy/evaluate.py` — evaluate(action, project_id, pack_id, …) → is_always_manual, may_batch, may_delegate, may_use_lanes, pack_may_override, simulate_only, explanation |
| Board | Create | `src/workflow_dataset/human_policy/board.py` — list_active_effects, list_overrides, apply_override, revoke_override, explain_why_blocked/allowed |
| CLI | Create | `src/workflow_dataset/human_policy/cli.py` — policy show, evaluate, override, revoke, board |
| Package init | Create | `src/workflow_dataset/human_policy/__init__.py` |
| Main CLI | Modify | `src/workflow_dataset/cli.py` — add policy_group (policy show, evaluate, override, revoke, board) |
| Mission control | Modify | `src/workflow_dataset/mission_control/state.py` — add human_policy block (active_restrictions, overrides, blocked_behaviors, intervention_candidates) |
| Mission control report | Modify | `src/workflow_dataset/mission_control/report.py` — add [Human policy] section |
| Tests | Create | `tests/test_human_policy.py` |
| Docs | Create | `docs/M28I_M28L_HUMAN_POLICY_ENGINE.md` |

No changes to trust/*, capability_discovery/*, supervised_loop/* internals; human_policy is additive. supervised_loop can later call human_policy evaluate for “may_batch” if desired.

---

## 4. Safety / risk note

- **Explicit only**: All policy and overrides are stored in local JSON; no hidden defaults that change behavior without operator visibility.
- **No weakening**: Evaluation is additive to existing trust/approval; we do not relax executor or approval-registry checks.
- **Override audit**: Overrides are timestamped and scoped; revoke is explicit. No silent override expiry that changes behavior without board visibility.
- **Local only**: No cloud or remote policy; all control remains operator-owned.

---

## 5. What this block will NOT do

- **No hidden policy**: Every effective rule is inspectable via policy show / board.
- **No replacement of trust/approval**: Trust cockpit and approval registry remain; human_policy layers on top for “may the agent do X” decisions.
- **No cloud governance**: No remote policy fetch or push.
- **No automatic override expiry enforcement in executor**: Override records may have expiry; first draft can show “expired” on board; enforcing “revoke when expired” in executor/planner is optional follow-up.
- **No rebuild of supervised_loop OperatorPolicy**: That stays for queue batch-approval; human_policy can feed into it or remain the broader source for “may batch” at evaluation time.

---

*Document generated before implementation. Implementation follows in Phases A–E.*
