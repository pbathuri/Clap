# M48I–M48L Governed Operator Mode + Delegation Safety — Before Coding

## 1. What operator/delegation safety already exists

- **Operator mode (M35E–M35H)**  
  - `DelegatedResponsibility`: project/pack/routine, authority_tier_id, review_gates, stop/escalation conditions.  
  - `OperatorModeProfile`: on/off, scope (project/pack ids), default_review_gates.  
  - `SuspensionRevocationState`: suspended_ids, revoked_ids with reasons.  
  - `PauseState`: NONE | EMERGENCY | SAFE; safe_continue_responsibility_ids for SAFE.  
  - `RevocationRecord`, `WorkImpactExplanation`, `PauseRevocationReport`.  
  - Store: profiles, responsibilities, bundles, state.json, pause_state.json, revocation_history.json.  
  - Flows: set_emergency_pause, set_safe_pause, clear_pause, revoke_responsibility, revoke_bundle, explain_work_impact, build_pause_revocation_report.  
  - CLI: operator-mode status, bundles, pause, revoke, explain-impact, pause-revocation-report.

- **Trust layer**  
  - `AuthorityTier`: allowed/forbidden action classes, approval_required, reversibility, audit, valid_scopes.  
  - `TrustedRoutineContract`: scope, authority_tier_id, routine_id, permitted/excluded actions, required_approvals, required_review_gates, stop_conditions, audit, fallback.  
  - effective_contract(routine_id, context), merge_contract_with_tier.  
  - Trust presets and eligibility matrix (routine_type → max tier by preset).

- **Review domains (Pane 2)**  
  - `ReviewDomain`, `ApprovalDomain`, `ReviewParticipantRole`, `EscalationRoute`, `MultiReviewRequirement`, `SensitiveActionDomain`, `BlockedCrossDomainAction`.  
  - Domains: operator_routine, sensitive_gate, production_repair, trusted_routine_audit, adaptation_promotion.  
  - boundaries: allowed_reviewers_for_domain, allowed_approvers_for_domain, role_safe_approval_chain, self_approve_blocked.

- **Supervisory control**  
  - `SupervisedLoopView`, `OperatorIntervention`, `PauseState`, `RedirectState`, `TakeoverState`, `HandbackState`, `OperatorRationale`, `LoopControlAuditNote`.  
  - Presets and takeover playbooks.

- **Adaptive execution**  
  - Plans, steps, outcomes, adaptation triggers, stop conditions, escalation/takeover.

- **Sensitive gates**  
  - Commit/send/apply gates, sign-off, audit ledger, blocked reasons.

- **Audits**  
  - Agent action audit log (stub), authority-tier audit summary, domain audit trace.

---

## 2. What is missing for governed operator mode

- **Explicit binding of operator mode to role and review domain**  
  - Responsibilities have authority_tier_id but no review_domain_id or role_id; no formal “this delegation is under domain X and role Y”.

- **Delegated scope and action boundary**  
  - No first-class “governed scope” (scope_id, domain_id, role_id, routine_ids, allowed_actions) or “delegated action boundary” (what may vs may not be done in this scope).

- **Delegation-safe loop**  
  - No single model that ties a loop (or responsibility) to: governed scope, domain, role, trust posture, and “continuation allowed only if …”.

- **Suspension/revocation triggers**  
  - Pause/revoke are manual; no explicit “suspension trigger” or “revocation trigger” (e.g. policy breach, confidence boundary, domain conflict).

- **Governed continuation approval**  
  - No explicit “continuation approval” that is domain/role-aware and required before resuming a suspended delegated loop.

- **Operator-mode domain conflict**  
  - No explicit model for “this operator action conflicts with domain X” or “cross-domain delegation not allowed”.

- **Single place to check “can this role run this routine in this scope?”**  
  - Eligibility is trust-preset vs routine-type; no unified “governed operator check” that combines role, domain, scope, and routine.

- **CLI and reports**  
  - No governed-operator status/scopes/check/suspend/revoke or “why delegation allowed/paused/revoked” explanation.

- **Mission control**  
  - No visibility for “active governed delegations”, “suspended delegations”, “highest-risk scope”, “reauthorization-needed”, “next governance action”.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| **Create** | `src/workflow_dataset/governed_operator/models.py` — GovernedOperatorMode, DelegatedScope, DelegatedActionBoundary, DelegationSafeLoop, SuspensionTrigger, RevocationTrigger, GovernedContinuationApproval, OperatorModeDomainConflict. |
| **Create** | `src/workflow_dataset/governed_operator/controls.py` — role_safe_delegation, domain_bound_delegation, action_restrictions_by_role_scope, supervised_continuation_allowed, suspend_on_policy_or_confidence, revoke_on_unsafe_or_conflict. |
| **Create** | `src/workflow_dataset/governed_operator/flows.py` — suspend_delegated_loop, revoke_delegated_scope, require_reauthorization, narrow_operator_scope, explain_delegation (why allowed/paused/revoked). |
| **Create** | `src/workflow_dataset/governed_operator/store.py` — persist governed scopes and delegation state (e.g. data/local/governed_operator). |
| **Create** | `src/workflow_dataset/governed_operator/mission_control.py` — slice: active_governed_delegations, suspended_delegations, highest_risk_scope, reauthorization_needed_scope_ids, next_governance_action. |
| **Create** | `src/workflow_dataset/governed_operator/__init__.py` — exports. |
| **Modify** | `src/workflow_dataset/cli.py` — add governed-operator Typer and commands: status, scopes, check, suspend, revoke, explain. |
| **Modify** | `src/workflow_dataset/mission_control/state.py` — add governed_operator_state from slice. |
| **Modify** | `src/workflow_dataset/mission_control/report.py` — add [Governed operator] section. |
| **Create** | `tests/test_governed_operator.py` — model creation, allow/block delegation, suspend/revoke flows, reauthorization, cross-domain block, explanation. |
| **Create** | `docs/samples/M48_governed_scope.json`, `M48_delegation_explanation.json`. |

---

## 4. Safety/risk note

- Governed operator layer **does not replace** trust, review, or audit; it **sits on top** and makes delegation explicit and domain/role-bound.  
- Risk: if callers bypass the check (e.g. run a routine without calling governed-operator check), automation could still run outside governed scope; mitigation: document that sensitive operator-mode entry points **should** call the governed-operator layer and that audits remain the backstop.  
- Revocation/suspension are local state; no cryptographic or multi-device consensus.  
- “Highest-risk” scope is heuristic (e.g. scope with commit_or_send or production_repair); not a formal risk score.

---

## 5. Delegation-safety principles

1. **Explicit scope** — Every delegated loop is tied to a governed scope (scope_id, domain_id, role_id, routine_ids).  
2. **Domain-bound** — Delegation is valid only within allowed review domains and approval boundaries.  
3. **Role-safe** — Actions under operator mode are restricted by role and scope (using existing role/domain boundaries).  
4. **No silent escalation** — Narrowing scope or revoking scope is explicit; no automatic expansion of delegated scope.  
5. **Continuation only where allowed** — Supervised continuation requires governed continuation approval when policy or confidence boundary is crossed.  
6. **Suspend on boundary crossing** — Policy or confidence boundary crossing can trigger suspension (not automatic escalation).  
7. **Revoke on unsafe/conflict** — Unsafe authority state or domain conflict triggers revocation path.  
8. **Explain** — Operator-facing explanation for why delegation is allowed, paused, or revoked.

---

## 6. What this block will NOT do

- **Not** a multi-user collaboration platform (no multi-tenant auth, no shared real-time state).  
- **Not** hidden escalation (all scope changes and revocations are explicit and visible).  
- **Not** bypassing trust/review/audit (governed layer uses existing tiers, contracts, domains).  
- **Not** replacing operator mode (wraps and constrains it; operator_mode store unchanged).  
- **Not** implementing cryptographic or distributed revocation.  
- **Not** enforcing execution at runtime (enforcement points remain at trust/sensitive_gates/supervisory; this layer provides models, checks, and CLI/reports).
