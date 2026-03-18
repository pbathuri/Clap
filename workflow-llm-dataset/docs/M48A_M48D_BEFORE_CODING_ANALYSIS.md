# M48A–M48D Before-Coding Analysis — Role Model + Scope-Bound Authority Controls

## 1. What current trust/role/authority concepts already exist

- **trust/tiers.py:** AuthorityTier (allowed/forbidden action classes, approval_required, audit_required, valid_scopes: global, project, pack, workflow, recurring_routine, worker_lane). BUILTIN_TIERS from observe_only through commit_or_send_candidate. tier_allows_action(tier, action_class).
- **trust/scope.py:** SCOPE_ORDER (global → project → pack → workflow → recurring_routine → worker_lane). effective_contract(routine_id, context) returns highest-precedence TrustedRoutineContract. merge_contract_with_tier(contract, tier).
- **trust/presets.py:** TrustPreset (max_authority_tier_id, require_approval_for_real, allow_commit_send, allow_bounded_trusted_real, valid_scope_hint). Built-in: cautious, supervised_operator, bounded_trusted_routine, release_safe.
- **trust/contracts.py:** TrustedRoutineContract (scope, scope_id, authority_tier_id, routine_id, permitted/excluded action classes, required_approvals, required_review_gates, allowed/excluded targets, audit_required).
- **production_cut/models.py:** ChosenPrimaryVertical, RequiredTrustPosture (trust_preset_id, review_gates_default, audit_posture), DefaultOperatingProfile (operator_mode_usage, role_operating_hint). Surfaces: included, excluded, quarantined.
- **governed_operator/models.py:** GovernedOperatorMode (role_id, review_domain_id, authority_tier_id, allowed_scope_ids). DelegatedScope (role_id, routine_ids, allowed/forbidden action classes, authority_tier_id, trust_preset_id). DelegatedActionBoundary (permitted/excluded action classes, require_approval_before). GovernedOperatorStatus.
- **review_domains/models.py:** ReviewParticipantRole (role_id, capabilities: observe, review, approve, reject, escalate). EscalationRoute, MultiReviewRequirement. ReviewDomainPolicy (separation_of_duties, initiator_cannot_approve). EscalationPack.
- **review_domains/policies.py:** Domain policies (sensitive_gate, production_repair, trusted_routine_audit, adaptation_promotion) with separation of duties and initiator_cannot_approve.

**Gaps:** Roles are referenced (role_id, role_operating_hint) but there is no single **human role** registry with explicit allowed/forbidden surfaces and action classes per role. Scope binding exists at contract/tier level but not a unified **authority scope** model (product / vertical / project / workflow / review_domain / operator_routine) with precedence. **Review requirement** and **override requirement** and **escalation path** appear in review_domains but are not wired to a governance **check** or **explain**. No **governance** CLI or mission_control slice that answers “can role X do action Y?” or “why is this blocked?”.

## 2. What is missing for a real role-governance layer

- **Explicit human role definitions:** operator, reviewer, approver, maintainer, observer, support_reviewer with stable semantics and allowed/forbidden surface sets and action classes.
- **Authority scope levels:** product_wide, vertical, project, workflow_routine, review_domain, operator_mode_routine with clear precedence and conflict resolution.
- **Role–scope bindings:** Which surfaces and action classes each role gets at each scope level; review_required vs approve_required; override_required; escalation_path when blocked.
- **Authority check API:** can_role_perform_action(role_id, action_class, scope_hint, surface_id?) → allowed | blocked with reason.
- **Explanation API:** explain_authority(role_id, surface_id or action_class) → human-readable why allowed or blocked and what would unblock.
- **Blocked-authority visibility:** Track or report blocked attempts (without cloud identity); mission_control slice for “active governance posture”, “current role map”, “most sensitive scopes”, “blocked authority attempts”, “next governance review”.
- **Single entry point:** governance CLI group and one mission_control slice so operators have one place to inspect role/scope/authority.

## 3. Exact file plan

- **New package:** `src/workflow_dataset/governance/` (does not replace trust, governed_operator, review_domains).
- **governance/models.py:** HumanRole, AuthorityScope, RoleAuthorityBinding, AllowedSurfaceSet, ForbiddenSurfaceSet, AllowedActionClass, ReviewRequirement, OverrideRequirement, EscalationPath, ScopeConflict. Role types: operator, reviewer, approver, maintainer, observer, support_reviewer.
- **governance/roles.py:** Built-in role definitions and get_role(role_id), list_roles().
- **governance/scope.py:** Scope levels (product_wide, vertical, project, workflow_routine, review_domain, operator_mode_routine), precedence, resolve_scope(scope_hint, repo_root), scope_conflict detection.
- **governance/bindings.py:** Default role–scope bindings (using production_cut, trust presets, review_domains); get_effective_binding(role_id, scope, repo_root).
- **governance/check.py:** can_role_perform_action(role_id, action_class, scope_hint=None, surface_id=None, repo_root=None) → CheckResult(allowed, reason, required_review, escalation_path). check_review_vs_approve(role_id, domain_id).
- **governance/explain.py:** explain_authority(role_id, surface_id=None, action_class=None, scope_hint=None, repo_root=None) → AuthorityExplanation(text, allowed_surfaces, blocked_surfaces, required_review, override_required, escalation_path).
- **governance/mission_control.py:** governance_slice(repo_root) → active_posture, role_map, most_sensitive_scopes, blocked_authority_attempts_count, next_recommended_governance_review.
- **governance/__init__.py:** Exports.
- **cli.py:** New group `governance` with commands: roles, role --id X, check --role X --action Y [--surface Z] [--scope S], explain --role X [--surface Y] [--action Z].
- **mission_control/state.py:** Add governance_state from governance_slice (additive).
- **mission_control/report.py:** Add “[Governance]” section (additive).
- **tests/test_governance.py:** Tests for role model, scope precedence, check allow/block, explain output, conflict handling, missing role/scope.
- **docs/M48A_M48D_GOVERNANCE_DELIVERABLE.md:** File list, CLI, sample role, sample check, sample explain, tests, gaps.

## 4. Safety/risk note

- **Local-first, inspectable:** All role and binding data is local (built-in + optional data/local/governance); no cloud identity or SSO. Blocked attempts can be logged locally for audit without sending off-box.
- **No weakening of trust/review:** Governance layer consumes trust presets, production cut, and review_domain policies; it does not bypass approval or audit. explain and check reflect existing boundaries.
- **Additive only:** Does not replace trust/*, governed_operator, review_domains; it provides a unified view and check/explain API on top of them.
- **Sensitive scope explicit:** Most sensitive scopes (e.g. commit_or_send, sensitive_gate) are explicitly modeled so operators see what is restricted and why.

## 5. Governance principles

- **Explicit over implicit:** Roles and scope-bound authority are named and queryable.
- **Scope-bound:** Authority is always in context of a scope (product, vertical, project, workflow, review domain, operator routine).
- **Review and override visible:** When a role may review but not approve, or when override is required, the layer explains it.
- **Escalation path clear:** When blocked, the layer can suggest escalation path (e.g. to approver or support_reviewer).
- **Local-first and inspectable:** No hidden cloud IAM; all state can be audited locally.

## 6. What this block will NOT do

- **No cloud IAM or identity provider:** No SSO, no cloud directory, no federation.
- **No enterprise admin UI:** No RBAC admin dashboard or tenant management.
- **No replacement of trust/policy:** Trust tiers, contracts, presets, and review_domain policies remain the source of truth; governance wraps them.
- **No hiding blocked behavior:** Blocked attempts are visible (e.g. in mission_control slice and explain output).
- **No broadening beyond chosen vertical:** Scope and bindings respect production cut and chosen vertical.
