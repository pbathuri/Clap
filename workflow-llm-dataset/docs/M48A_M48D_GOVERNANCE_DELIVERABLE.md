# M48A–M48D Governance Layer — Deliverable

## 1. Files modified

- **src/workflow_dataset/cli.py** — Added `governance_group` and commands: `governance roles`, `governance role --id <id>`, `governance check --role X --action Y [--surface Z] [--scope S]`, `governance explain --role X [--surface Y] [--action Z]`.
- **src/workflow_dataset/mission_control/state.py** — Added `governance_state` from `governance_slice(repo_root)`.
- **src/workflow_dataset/mission_control/report.py** — Added "[Governance]" section: posture, roles count, sensitive_scopes, blocked_authority_attempts, next review.

## 2. Files created

- **docs/M48A_M48D_BEFORE_CODING_ANALYSIS.md** — Before-coding analysis (current concepts, gaps, file plan, safety, principles, out-of-scope).
- **src/workflow_dataset/governance/__init__.py** — Package exports.
- **src/workflow_dataset/governance/models.py** — HumanRole, AuthorityScope, RoleAuthorityBinding, ReviewRequirement, OverrideRequirement, EscalationPath, ScopeConflict, CheckResult, AuthorityExplanation; RoleType, ScopeLevelId enums.
- **src/workflow_dataset/governance/roles.py** — Built-in roles (observer, operator, reviewer, approver, maintainer, support_reviewer); get_role, list_roles.
- **src/workflow_dataset/governance/scope.py** — Scope levels (product_wide, vertical, project, workflow_routine, review_domain, operator_mode_routine); resolve_scope, scope_precedence_rank.
- **src/workflow_dataset/governance/bindings.py** — get_effective_binding(role_id, scope_hint, repo_root); uses production_cut and trust presets.
- **src/workflow_dataset/governance/check.py** — can_role_perform_action; check_review_vs_approve.
- **src/workflow_dataset/governance/explain.py** — explain_authority.
- **src/workflow_dataset/governance/mission_control.py** — governance_slice.
- **tests/test_governance.py** — Tests for roles, scope, bindings, check, explain, slice, missing role/scope.
- **docs/M48A_M48D_GOVERNANCE_DELIVERABLE.md** — This file.

## 3. Exact CLI usage

```bash
# List roles
workflow-dataset governance roles
workflow-dataset governance roles --json

# Show one role
workflow-dataset governance role --id operator
workflow-dataset governance role --id reviewer --json

# Check whether role may perform action
workflow-dataset governance check --role operator --action execute_simulate
workflow-dataset governance check --role reviewer --action commit_or_send --scope vertical --json
workflow-dataset governance check --role operator --action queued_execute --surface workspace_home

# Explain authority for role
workflow-dataset governance explain --role operator
workflow-dataset governance explain --role approver --surface review_studio --scope vertical
workflow-dataset governance explain --role operator --action commit_or_send --json
```

## 4. Sample role definition

```json
{
  "role_id": "operator",
  "role_type": "operator",
  "label": "Operator",
  "description": "Execute within approved scope; queue and simulate; real run after approval.",
  "allowed_surface_ids": ["workspace_home", "day_status", "queue_summary", "continuity_carry_forward", "operator_mode", "inbox"],
  "forbidden_surface_ids": ["review_studio_approve", "trust_cockpit_approve", "sensitive_gate_approve"],
  "allowed_action_classes": ["observe", "suggest", "draft", "sandbox_write", "execute_simulate", "queued_execute"],
  "forbidden_action_classes": ["commit_or_send"],
  "may_review": true,
  "may_approve": false,
  "may_execute": true,
  "default_authority_tier_id": "queued_execute"
}
```

## 5. Sample authority check output

**Allowed:**
```
[green]Allowed[/green]  role=operator  action=execute_simulate  scope=product_wide
  Role has effective binding and action is permitted.
```

**Blocked:**
```
[red]Blocked[/red]  role=operator  action=commit_or_send
  Action 'commit_or_send' is forbidden for role 'operator'.
  required_approval=True
  escalate: approver — Approver may grant or execute in designated domain.
```

## 6. Sample governance explanation

```
[bold]Role 'operator' at scope product_wide: tier=queued_execute, trust_preset=supervised_operator. May review=True, override_required=False.[/bold]
  scope: product_wide
  allowed_surfaces: workspace_home, day_status, queue_summary, continuity_carry_forward, operator_mode, inbox
  blocked_surfaces: review_studio_approve, trust_cockpit_approve, sensitive_gate_approve
  escalation: Escalate to approver or maintainer if blocked.
```

## 7. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_governance.py -v
```

Tests: test_list_roles, test_get_role_operator, test_get_role_unknown, test_scope_precedence_rank, test_resolve_scope_product_wide, test_resolve_scope_project, test_get_effective_binding_operator, test_can_role_perform_action_observer_blocked, test_can_role_perform_action_operator_simulate, test_can_role_perform_action_operator_commit_blocked, test_explain_authority_operator, test_explain_authority_unknown_role, test_governance_slice, test_missing_role_check, test_missing_scope_binding.

## 8. Exact remaining gaps for later refinement

- **Persistence of blocked attempts:** governance_slice currently computes a simple “blocked count” (roles that cannot do commit_or_send); no persistent log of actual blocked attempts. A local log (e.g. data/local/governance/blocked_attempts.json) could be added for audit.
- **Role–domain binding:** review_domains policies (initiator_cannot_approve, separation of duties) are not yet wired into check_review_vs_approve for a specific domain; only role.may_review/may_approve are used. Future: pass domain_id into bindings and check.
- **Override requirement model:** OverrideRequirement is in models but not yet populated from review_domains or trust; explain could surface “override by role X required” from policy.
- **Custom roles:** Roles are built-in only; data/local/governance/roles.json could allow custom role definitions with same schema.
- **Surface registry:** allowed/forbidden_surface_ids are string ids; no central registry of surface definitions yet. Production cut included_surface_ids are used in bindings; a single surface registry would align naming.
- **Scope conflict resolution:** ScopeConflict is modeled but no conflict detection or resolution is run when multiple scopes apply; currently single scope from resolve_scope is used.
