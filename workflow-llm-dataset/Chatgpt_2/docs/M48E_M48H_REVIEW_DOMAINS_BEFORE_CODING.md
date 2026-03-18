# M48E–M48H — Review Domains + Shared Approval Boundaries: Before Coding

## 1. What review/approval chain behavior already exists

| Area | What exists | Notes |
|------|-------------|--------|
| **sensitive_gates** | SensitiveActionGate (commit/send/apply), stage_candidate, review_candidate; SignOffRequirement(authority_tier_id); ReviewRationale(decision, operator_id); AuditLedgerEntry with approval_chain (ApprovalChainEntry), OperatorSignOff, authority_tier. | Gate-level approval and ledger; no domain grouping; no “who may approve” by role. |
| **trust/tiers** | AuthorityTier (observe_only … commit_or_send_candidate), approval_required, audit_required, allowed/forbidden action classes. | Tier defines scope of allowed actions and that approval/audit are required; no “reviewer role” or “escalation route.” |
| **capability_discovery** | ApprovalRegistry (approved_paths, approved_action_scopes); check_execution_allowed(adapter_id, action_id, params). | Path/scope allowlist for execution; no review-domain or role. |
| **review_studio** | InterventionItem kinds: approval_queue, blocked_run, replan, skill_candidate, policy_exception, stalled, graph_routine_confirmation, graph_pattern_review; build_inbox from queue, blocked runs, etc. | Inbox aggregates items for review; no domain-based “who may review this.” |
| **supervised_loop** | QueuedAction, OperatorPolicy (batch_approve_max_risk, always_manual_review_action_types, requires_manual_review); approve_batch. | Policy says what must be manual vs batch; no domain or role-based “approver.” |
| **conversational/roles** | ROLE_OPERATOR, ROLE_REVIEWER; role_suggested_commands. | UI hint for commands; not used for gating who may approve. |
| **human_policy** | HumanPolicyConfig, action-class policies, approval requirements, delegation. | Policy layer; no explicit review domains or approval boundaries per domain. |

## 2. What is missing for role-safe shared review boundaries

- **Review domains** — No first-class grouping of “operator routine review,” “sensitive gate approval,” “production repair approval,” “trusted-routine audit review,” “adaptation/promotion review” with clear scope.
- **Who may review/approve** — authority_tier is on the gate; no “allowed_reviewer_roles” or “allowed_approver_roles” per domain, and no “observer” vs “reviewer” vs “approver” distinction.
- **Self-approval block** — No rule that “the same role that initiated the action cannot approve it” for sensitive domains.
- **Escalation route** — No “escalate to higher-trust reviewer” or “escalation_route” per domain.
- **Multi-review requirement** — No “requires N distinct reviewers” or “second approver” for highest-sensitivity domains.
- **Cross-domain block** — No “blocked cross-domain action” when an action spans domains or a role tries to act outside its domain.
- **Domain-specific audit** — Audit is per gate/ledger; no grouping by review_domain for queries or explanation.
- **Explanation** — No “who may review,” “who may approve,” “why chain is blocked,” “why escalation required,” “why comment-but-not-approve.”

## 3. Exact file plan

| Area | Path | Purpose |
|------|------|--------|
| Doc | `docs/M48E_M48H_REVIEW_DOMAINS_BEFORE_CODING.md` | This file. |
| Models | `src/workflow_dataset/review_domains/models.py` | ReviewDomain, ApprovalDomain, ReviewParticipantRole, EscalationRoute, MultiReviewRequirement, SensitiveActionDomain, DomainAuditTrace, BlockedCrossDomainAction. |
| Registry | `src/workflow_dataset/review_domains/registry.py` | Built-in domains (operator_routine, sensitive_gate, production_repair, trusted_routine_audit, adaptation_promotion); get_domain(id), list_domains(). |
| Boundaries | `src/workflow_dataset/review_domains/boundaries.py` | allowed_reviewers/approvers per domain; role_safe_approval_chain; self_approve_block; escalation_to_higher_trust; cross_domain_block; domain_audit_trace. |
| Explain | `src/workflow_dataset/review_domains/explain.py` | who_may_review(domain_id, role), who_may_approve(domain_id, role), why_chain_blocked(domain_id, context), why_escalation_required(domain_id), why_comment_only(domain_id, role). |
| CLI | `src/workflow_dataset/cli.py` | review-domains list, show --id, check --role --domain, explain --id. |
| Mission control | `src/workflow_dataset/mission_control/state.py` | review_domains slice: active_domains, domain_blocked_approvals, required_escalations, most_sensitive_pending, next_recommended_adjustment. |
| Tests | `tests/test_review_domains.py` | Domain creation, role/domain compatibility, escalation, self-approval block, cross-domain conflict, explanation. |
| Deliverable | `docs/M48E_M48H_REVIEW_DOMAINS_DELIVERABLE.md` | Files, CLI, samples, tests, gaps. |

## 4. Safety/risk note

- **Do not hide blocked approval reasons** — When a chain is blocked or escalation is required, the explanation must be visible (e.g. “Role X cannot self-approve in domain Y”).
- **Do not weaken sensitive-action boundaries** — The layer adds explicit domains and boundaries; it must not relax existing sensitive_gates or trust tiers.
- **Do not rebuild approval/audit** — We consume existing gates and ledger; we add domain metadata and checks that call into existing systems, not replace them.

## 5. Review-domain principles

- **Explicit domains** — Each review/approval context (operator routine, sensitive gate, production repair, trusted-routine audit, adaptation/promotion) is a named domain with allowed roles and rules.
- **Role-safe chains** — Approval chains respect “who may approve”; one role cannot self-approve in sensitive domains when configured.
- **Inspectable** — Domain definitions and “why blocked / why escalate” are queryable and reportable.
- **Local-first** — No cloud workflow engine; domains and boundaries are configurable under data/local/review_domains.

## 6. What this block will NOT do

- Rebuild approval, audit, review_studio, or trust systems from scratch.
- Implement a cloud workflow engine or generic ticketing/collaboration.
- Open broad collaborative SaaS features.
- Replace sensitive_gates or trust tiers; we add a domain/boundary layer on top and optionally feed into existing gates.
