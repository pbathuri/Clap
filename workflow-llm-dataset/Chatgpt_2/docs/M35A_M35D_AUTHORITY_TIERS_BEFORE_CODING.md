# M35A–M35D — Authority Tiers + Trusted Routine Contracts: Before Coding

## 1. What trust / policy / approval concepts already exist

- **Trust (trust/*)**  
  - **TrustCockpit**: read-only aggregation of benchmark_trust, approval_readiness (registry_exists, approved_paths_count, approved_action_scopes_count), job_macro_trust_state (simulate_only_count, trusted_for_real_count, approval_blocked_count), release_gate_status, safe_to_expand.  
  - **ApprovalReadiness**, **JobMacroTrustState**: no explicit “authority tier” or “contract”; jobs/routines are either simulate_only, trusted_for_real, or approval_blocked from job_packs/specialization.

- **Approvals (capability_discovery)**  
  - **ApprovalRegistry**: approved_paths, approved_apps, approved_action_scopes (adapter_id, action_id, executable). Load/save from YAML. Used to decide if a job is “trusted for real.” No tiers or routine-level contracts.

- **Human policy (human_policy/*)**  
  - **Scopes**: global, project, pack, task, lane. **ActionClassPolicy** per action_class (require_approval, allow_batch, allow_auto). **BlockedActionPolicy** (scope + blocked_action_classes). **PolicyEvalResult**: is_always_manual, simulate_only, blocked, explanation.  
  - **evaluate(action_class, project_id, pack_id)** returns policy result. No notion of “authority tier” or “trusted routine contract.”

- **Automations (automations/*)**  
  - **TriggerDefinition**: required_policy_trust = simulate | approval_required | trusted. **RecurringWorkflowDefinition**: execution_mode, approval_points, review_destination. **GuardrailProfile**: suppression_rules, require_approval_for_real, max_recurring_per_day.  
  - Trigger/workflow-level policy hints; no explicit contract model (permitted/excluded actions, required review gates, allowed targets, stop conditions, audit).

- **Macros / executor**  
  - Step types: safe_inspect, sandbox_write, trusted_real, blocked, human_checkpoint. **ActionEnvelope**: mode, approvals_required, checkpoint_required. Planner step_class: reasoning_only, local_inspect, sandbox_write, trusted_real_candidate, human_required, blocked.  
  - Classification is per-step/job; no tier that bundles “what this routine is allowed to do” or “where human approval is always required.”

- **Background runner**  
  - Gating uses human_policy and work_state (approval_blocked_jobs, simulate_only_jobs). No authority tier or contract lookup.

**Summary:** Trust is observational (cockpit); policy is scope + action-class; approvals are path/scope registry; automations have guardrails and workflow-level execution_mode. There is **no** explicit authority tier (observe_only → commit_candidate), no trusted-routine **contract** (permitted/excluded actions, review gates, targets, stop conditions, audit), and no single place that defines “what each routine is allowed to do” and “where human approval is always required” in a contract-driven way.

---

## 2. What is missing for a real authority-tier and trusted-routine contract system

- **Authority tiers**  
  - Named tiers (e.g. observe_only, suggest_only, draft_only, sandbox_write, queued_execute, bounded_trusted_real, commit_or_send_candidate) with: allowed_action_classes, forbidden_action_classes, approval_requirements, reversibility_expectations, audit_requirements, valid_scopes.  
  - So that “current posture” can be stated as a tier and checked against actions.

- **Trusted routine contract**  
  - Explicit contract per routine/workflow: scope, permitted_actions, excluded_actions, required_approvals, required_review_gates, allowed_targets/resources, stop_conditions, audit_requirements, fallback_behavior.  
  - Stored and loadable; validatable; referenceable by automation/background/executor.

- **Scope + inheritance**  
  - global < project < pack < workflow < recurring_routine (and worker_lane if needed). Precedence and conflict rules (e.g. “more specific overrides less”; “forbidden always wins”) defined and inspectable.

- **Validation and explain**  
  - Validate a contract (consistent, within tier limits, no conflicting rules). Explain why a routine is allowed or blocked (which contract/tier/scope applied).

- **Mission control visibility**  
  - Active authority tier posture, trusted routines in effect, routines blocked by contract, highest-authority active scope, next recommended trust review.

---

## 3. Exact file plan

| Area | Action | Path |
|------|--------|------|
| **Authority tiers** | Create | `src/workflow_dataset/trust/tiers.py` — AuthorityTier enum/model, allowed/forbidden action classes, approval/audit/reversibility, valid scopes; BUILTIN_TIERS list; get_tier(tier_id). |
| **Contracts** | Create | `src/workflow_dataset/trust/contracts.py` — TrustedRoutineContract model (scope, permitted/excluded actions, required approvals, review gates, allowed targets, stop conditions, audit, fallback); store load/save/list; validate_contract(contract). |
| **Scope** | Create | `src/workflow_dataset/trust/scope.py` — SCOPE_ORDER, precedence, merge_contracts(context) or effective_contract(routine_id, context); conflict rules. |
| **Explain** | Create | `src/workflow_dataset/trust/explain_contract.py` — explain_why_allowed(routine_id, action_class, context), explain_why_blocked(routine_id, action_class, context); use tiers + contracts + scope. |
| **CLI** | Modify | `src/workflow_dataset/cli.py` — trust_group: add commands tiers, contracts list, contracts show --id, contracts validate --id, explain --routine. |
| **Mission control** | Modify | `src/workflow_dataset/mission_control/state.py` — add authority_contracts_state (active_tier, trusted_routines_in_effect, routines_blocked_by_contract, highest_authority_scope, next_trust_review). |
| **Mission control** | Modify | `src/workflow_dataset/mission_control/report.py` — add [Authority / Trust contracts] section. |
| **Package** | Modify | `src/workflow_dataset/trust/__init__.py` — export tiers, contracts, scope, explain. |
| **Tests** | Create | `tests/test_trust_authority_contracts.py` — tier definitions, contract validation, scope precedence, explain allowed/blocked. |
| **Docs** | Create | `docs/M35A_M35D_AUTHORITY_TIERS_AND_CONTRACTS.md` — design, samples, CLI, tests, gaps. |

---

## 4. Safety / risk note

- **Do:** Define tiers and contracts explicitly; forbid by default; make approval requirements and audit requirements part of the contract; make precedence and “why blocked” explainable. No silent escalation.  
- **Do not:** Allow a contract to broaden allowed actions without being validated and visible; allow “trusted_real” without an explicit approval or tier that requires approval.  
- **Risk:** Misconfiguration could mark a routine as higher-trust than intended; mitigation: default to lower tiers, require explicit contract for bounded_trusted_real/commit_candidate, and validation that forbidden and required_approvals are consistent.

---

## 5. What this block will NOT do

- Replace or rewrite existing trust cockpit, approval registry, human_policy, or executor/macros step classification; it adds a **contract layer** that those can consult.  
- Implement cloud IAM or enterprise SSO; remains local-first and file-based.  
- Auto-execute at higher authority; “governed operator mode” is prepared for (contracts + tiers) but not implemented here.  
- Add new approval UI; only models, validation, explain, and mission-control visibility.
