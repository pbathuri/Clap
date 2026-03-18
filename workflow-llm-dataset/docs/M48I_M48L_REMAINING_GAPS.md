# M48I–M48L Governed Operator Mode — Remaining Gaps for Later Refinement

## Implemented in this block

- **Phase A**: Models for governed operator mode, delegated scope, action boundary, delegation-safe loop, suspension/revocation triggers, governed continuation approval, domain conflict, delegation explanation.
- **Phase B**: role_safe_delegation, domain_bound_delegation, action_restrictions_by_role_scope, supervised_continuation_allowed, suspend_on_policy_or_confidence, revoke_on_unsafe_or_conflict, check_delegation.
- **Phase C**: suspend_delegated_loop, revoke_delegated_scope, require_reauthorization, narrow_operator_scope, explain_delegation, clear_suspension.
- **Phase D**: CLI (status, scopes, check, suspend, revoke, explain), mission control slice and report.
- **Phase E**: Tests and sample JSON (governed scope, delegation explanation).

---

## Exact remaining gaps (for later)

1. **DelegatedActionBoundary persistence**  
   Model exists; no store/API yet to attach boundaries to scopes or enforce permitted/excluded targets at check time.

2. **DelegationSafeLoop persistence and use**  
   Store has list_loop_ids, get_loop, save_loop but no CLI or default data; supervised_continuation_allowed could resolve loop by scope and use loop.supervised_continuation_allowed.

3. **SuspensionTrigger / RevocationTrigger persistence**  
   Models only; no registry or evaluation (e.g. “on policy_breach suspend scope X”). Triggers are not evaluated automatically; suspend/revoke are still manual or via controls.suspend_on_policy_or_confidence / revoke_on_unsafe_or_conflict.

4. **GovernedContinuationApproval persistence**  
   Model only; no store or flow to record an approval and clear reauthorization_needed or suspended state.

5. **OperatorModeDomainConflict recording**  
   Model only; no store to append conflicts or to block actions that would create a conflict (recording would sit at call sites that perform the check).

6. **Clearing revocation**  
   Revoked scope ids are stored but there is no “clear revocation” flow; to reuse a scope after revoke you must re-create it or add an explicit clear_revocation API.

7. **Runtime enforcement**  
   Trust/sensitive_gates/supervisory call sites do not yet call check_delegation or action_restrictions_by_role_scope; enforcement is advisory via CLI and mission control.

8. **Link to operator_mode responsibilities**  
   DelegatedScope.responsibility_ids and DelegationSafeLoop.responsibility_id are not synced with operator_mode store; no automatic “create governed scope from responsibility” or “suspend responsibility when scope suspended.”

9. **Highest-risk heuristic**  
   Slice uses authority_tier_id (e.g. commit_or_send_candidate) as a simple risk signal; no formal risk score or configurable weights.

10. **Review domain custom packs**  
    get_domain uses built-in registry; if custom domains are loaded from data/local/review_domains, that path should be confirmed and used in role_safe_delegation/check_delegation.
