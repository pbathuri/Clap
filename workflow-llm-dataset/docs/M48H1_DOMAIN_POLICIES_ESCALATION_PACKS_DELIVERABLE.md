# M48H.1 — Domain Policies + Escalation Packs: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/review_domains/models.py` | Added ReviewDomainPolicy, EscalationPackEntry, EscalationPack. |
| `src/workflow_dataset/review_domains/__init__.py` | Exported policy, escalation pack, and summary APIs. |
| `src/workflow_dataset/cli.py` | Added review-domains policy, escalation-packs, escalation-pack-show, separation-summary. |
| `tests/test_review_domains.py` | Added tests for domain policy, escalation pack, separation-of-duties summary. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/review_domains/policies.py` | Built-in domain policies and escalation packs; get_domain_policy, list_domain_policies, get_escalation_pack, list_escalation_packs, get_escalation_entries_for_action; custom load from data/local/review_domains (policies.yaml/json, escalation_packs.yaml/json). |
| `src/workflow_dataset/review_domains/summaries.py` | separation_of_duties_summary(domain_id), separation_of_duties_summary_all(), format_separation_summary_text(); clearer summaries of which approvals require separation and why. |
| `docs/M48H1_DOMAIN_POLICIES_ESCALATION_PACKS_DELIVERABLE.md` | This file. |

## 3. Sample domain policy

**Policy id:** `sensitive_gate_policy`  
**Domain:** `sensitive_gate`  
**Name:** Sensitive gate separation of duties  

- **Description:** Commit, send, and apply actions require a distinct approver; initiator cannot self-approve.  
- **Separation of duties required:** true  
- **Initiator cannot approve:** true  
- **Min distinct approvers:** 1  
- **Policy rationale:** Sensitive actions (commit/send/apply) must be signed off by a role other than the initiator to reduce single-party risk and preserve audit clarity.  
- **Scope note:** SensitiveActionGate candidates.  

## 4. Sample escalation pack

**Pack id:** `sensitive_actions`  
**Name:** Sensitive actions escalation  
**Description:** Escalation steps for commit, send, apply, production repair, and promotion.  
**Sensitivity label:** high  

**Entries (summary):**

| action_kind        | domain_id           | target_role_id | trigger_condition   | description                                          |
|--------------------|---------------------|----------------|---------------------|------------------------------------------------------|
| commit             | sensitive_gate      | approver       | self_approve_blocked | Operator must escalate to approver for commit sign-off. |
| send               | sensitive_gate      | approver       | self_approve_blocked | Operator must escalate to approver for send sign-off.  |
| apply              | sensitive_gate      | approver       | self_approve_blocked | Operator must escalate to approver for apply sign-off. |
| production_repair  | production_repair   | approver       | manual              | Escalate to approver for production repair sign-off.   |
| adaptation_promotion | adaptation_promotion | approver     | manual              | Escalate to approver for promotion.                   |

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_review_domains.py -v
```

New/updated tests:

- `test_domain_policy_sensitive_gate` — policy exists, separation of duties and rationale present  
- `test_escalation_pack_sensitive_actions` — pack exists, entries for commit/send/apply, get_escalation_entries_for_action("commit")  
- `test_separation_of_duties_summary` — summary for sensitive_gate, format_separation_summary_text, separation_of_duties_summary_all  

All existing review_domains tests plus the above should pass.

## 6. Next recommended step for the pane

- **Wire policies into gate flows:** When recording an approval in sensitive_gates (or supervised_loop), optionally call `get_domain_policy(domain_id)` and enforce or log policy_rationale; and when blocking self-approve, attach the policy id and rationale to the blocked reason so operators see “why” in the same place as “blocked.”  
- **Use escalation pack in explain/CLI:** For `review-domains explain --id sensitive_gate`, include the relevant escalation pack entries (e.g. “For commit/send/apply: escalate to approver”) so one command gives both domain rules and escalation steps.  
- **Persistence of custom policies/packs:** Document the schema for `data/local/review_domains/policies.yaml` and `escalation_packs.yaml` (with one example each) so operators can add or override policies and packs without code changes.
