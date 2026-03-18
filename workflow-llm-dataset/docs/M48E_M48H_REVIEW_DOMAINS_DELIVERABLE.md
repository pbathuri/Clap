# M48E–M48H — Review Domains + Shared Approval Boundaries: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `docs/M48E_M48H_REVIEW_DOMAINS_BEFORE_CODING.md` | New: before-coding doc (existing behavior, gaps, file plan, safety, principles, what we will not do). |
| `src/workflow_dataset/mission_control/state.py` | Added 6k: `review_domains_state` from `review_domains_mission_control_slice`. |
| `src/workflow_dataset/mission_control/report.py` | Added [Review domains] section: active domains, domain-blocked approvals, required escalations, most sensitive pending, next adjustment. |
| `src/workflow_dataset/cli.py` | Added `review_domains_group` and commands: list, show, check, explain. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/review_domains/__init__.py` | Package exports. |
| `src/workflow_dataset/review_domains/models.py` | ReviewDomain, ApprovalDomain, ReviewParticipantRole, EscalationRoute, MultiReviewRequirement, SensitiveActionDomain, DomainAuditTrace, BlockedCrossDomainAction. |
| `src/workflow_dataset/review_domains/registry.py` | Built-in domains (operator_routine, sensitive_gate, production_repair, trusted_routine_audit, adaptation_promotion); get_domain, list_domains; custom load from data/local/review_domains. |
| `src/workflow_dataset/review_domains/boundaries.py` | allowed_reviewers_for_domain, allowed_approvers_for_domain, role_safe_approval_chain, self_approve_blocked, escalation_required, cross_domain_block, check_role_in_domain. |
| `src/workflow_dataset/review_domains/explain.py` | who_may_review, who_may_approve, why_chain_blocked, why_escalation_required, why_comment_only. |
| `src/workflow_dataset/review_domains/mission_control.py` | review_domains_mission_control_slice: active domains, domain-blocked approvals, required escalations, most_sensitive_pending, next_recommended_adjustment. |
| `tests/test_review_domains.py` | Tests: domain creation, role/domain compatibility, escalation, self-approval block, cross-domain block, explanation, mission control slice. |
| `docs/M48E_M48H_REVIEW_DOMAINS_DELIVERABLE.md` | This file. |

## 3. Exact CLI usage

```bash
# List all review domains (built-in + custom from data/local/review_domains)
workflow-dataset review-domains list
workflow-dataset review-domains list --repo-root /path/to/repo

# Show one domain by id
workflow-dataset review-domains show --id sensitive_gate
workflow-dataset review-domains show --id operator_routine

# Check whether a role may review/approve in a domain; show escalation if required
workflow-dataset review-domains check --role reviewer --domain trusted_routine_audit
workflow-dataset review-domains check --role operator --domain sensitive_gate

# Explain who may review/approve and why blocked or escalation required
workflow-dataset review-domains explain --id sensitive_gate
workflow-dataset review-domains explain --id production_repair
```

## 4. Sample review domain

**Domain id:** `sensitive_gate`  
**Name:** Sensitive gate approval  
**Description:** Commit, send, apply candidates; requires explicit sign-off.  
**Scope:** SensitiveActionGate (commit/send/apply) candidates.  
**Self-approve blocked:** Yes  
**Allowed roles:**  
- operator: observe, review (may not approve)  
- approver: observe, review, approve, reject  
- auditor: observe  
**Escalation:** Operator must escalate to approver for sign-off (self_approve_blocked).  

## 5. Sample approval-boundary output

**Check:** `workflow-dataset review-domains check --role operator --domain sensitive_gate`

```
Role: operator  Domain: sensitive_gate
  May review: True
  May approve: False
  Escalation required: Escalate to approver for sign-off. (or "Operator must escalate to approver for sign-off.")
```

## 6. Sample blocked / escalated review output

**Explain:** `workflow-dataset review-domains explain --id sensitive_gate`

```
┌─ Review domain ─────────────────────────────────────────┐
│ Sensitive gate approval — sensitive_gate                 │
└─────────────────────────────────────────────────────────┘
Who may review:
  - operator: Operator — May review and comment; cannot self-approve sensitive gate.
  - approver: Approver — May approve or reject sensitive actions.
  - auditor: Auditor — Observe only; audit trail visibility.
Who may approve: approver
Self-approve blocked: True
  Role operator must escalate: Escalate to approver for sign-off.
```

**Blocked cross-domain record (programmatic):**  
`cross_domain_block("operator_routine", "sensitive_gate", "operator", "gate_123", "self_approve_blocked", "Initiator cannot approve.")`  
produces a `BlockedCrossDomainAction` with `reason_code=self_approve_blocked`, `action_ref=gate_123`.

## 7. Exact tests run

```bash
cd workflow-llm-dataset
python -m pytest tests/test_review_domains.py -v
```

Tests included:  
- `test_review_domain_creation`  
- `test_builtin_domains_list`  
- `test_get_domain_sensitive_gate`  
- `test_role_domain_compatibility`  
- `test_allowed_reviewers_approvers`  
- `test_escalation_required`  
- `test_self_approve_blocked`  
- `test_operator_routine_self_approve_allowed`  
- `test_cross_domain_block_record`  
- `test_who_may_review_approve`  
- `test_why_chain_blocked_self_approve`  
- `test_why_escalation_required`  
- `test_why_comment_only`  
- `test_get_approval_domain`  
- `test_get_sensitive_action_domain`  
- `test_review_domains_mission_control_slice`  

## 8. Remaining gaps for later refinement

- **Persistence of blocked cross-domain actions** — We create `BlockedCrossDomainAction` in memory; no store yet under `data/local/review_domains` (e.g. `blocked.jsonl`).  
- **Domain-specific audit trail persistence** — `DomainAuditTrace` is modeled but not appended from sensitive_gates flows; ledger remains gate-centric.  
- **Wiring into sensitive_gates flows** — Gates do not yet call `self_approve_blocked(domain_id, initiator_role, approver_role)` or `cross_domain_block` before recording approval; this layer is ready for callers.  
- **Custom domains from YAML/JSON** — Supported in registry via `data/local/review_domains/domains.yaml` or `domains.json`; no CLI add/edit for custom domains.  
- **Multi-review requirement enforcement** — `MultiReviewRequirement` (min_reviewers, min_approvers, distinct_roles) is on the model and built-in domains; no enforcement in approval chain yet.  
- **Mission control report** — Review domains slice is in state and report; next_action/recommendation does not yet prioritize “review sensitive gate” from this slice.
