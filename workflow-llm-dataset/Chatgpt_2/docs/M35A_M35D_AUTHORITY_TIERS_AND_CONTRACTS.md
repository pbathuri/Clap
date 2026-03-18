# M35A–M35D Authority Tiers and Trusted Routine Contracts

First-draft trust-contract layer: authority tiers, trusted routine contracts, scope and inheritance, CLI, mission control visibility, tests and docs.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/trust/__init__.py` | Exported authority tier and contract API (tiers, contracts, scope, explain). |
| `src/workflow_dataset/cli.py` | Added `trust tiers`, `trust contracts list/show/validate`, `trust explain --routine`. |
| `src/workflow_dataset/mission_control/state.py` | Added `authority_contracts_state` (active_tier_posture, trusted_routines_in_effect, routines_blocked_by_contract, highest_authority_scope, next_trust_review). |
| `src/workflow_dataset/mission_control/report.py` | Added "[Authority / Trust contracts]" section to mission control report. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/trust/tiers.py` | Authority tier model and BUILTIN_TIERS. |
| `src/workflow_dataset/trust/contracts.py` | TrustedRoutineContract, load/save, get_contract, get_contracts_for_routine, validate_contract. |
| `src/workflow_dataset/trust/scope.py` | effective_contract, merge_contract_with_tier, SCOPE_ORDER. |
| `src/workflow_dataset/trust/explain_contract.py` | explain_why_allowed, explain_why_blocked, explain_routine. |
| `tests/test_trust_authority_contracts.py` | Tests for tiers, contract validation, scope precedence, explain. |
| `docs/M35A_M35D_AUTHORITY_TIERS_BEFORE_CODING.md` | Pre-coding analysis (existing). |
| `docs/M35A_M35D_AUTHORITY_TIERS_AND_CONTRACTS.md` | This document. |

Contracts are stored in `data/local/trust/contracts.json` (created on first save).

---

## 3. Exact CLI usage

```bash
# List built-in authority tiers
workflow-dataset trust tiers

# List all trusted routine contracts
workflow-dataset trust contracts list

# Show one contract
workflow-dataset trust contracts show --id morning_digest_contract

# Validate one contract
workflow-dataset trust contracts validate --id morning_digest_contract

# Explain trust/contract status for a routine (optional project/pack/workflow context)
workflow-dataset trust explain --routine morning_digest
workflow-dataset trust explain --routine blocked_followup --project proj_alpha --pack founder_ops
```

Optional `--repo-root` is supported on all of the above.

---

## 4. Sample authority tier definition

One built-in tier as dict-like structure:

```json
{
  "tier_id": "sandbox_write",
  "name": "Sandbox write",
  "description": "Writes in sandbox only; simulate execution allowed.",
  "allowed_action_classes": ["observe", "suggest", "draft", "sandbox_write", "execute_simulate"],
  "forbidden_action_classes": ["execute_trusted_real", "commit_or_send"],
  "approval_required": false,
  "reversibility_expected": "optional",
  "audit_required": false,
  "valid_scopes": ["global", "project", "pack", "workflow", "recurring_routine"],
  "order": 3
}
```

---

## 5. Sample trusted routine contract

Example contract (as would appear in `data/local/trust/contracts.json`):

```json
{
  "contract_id": "morning_digest_contract",
  "label": "Morning digest",
  "description": "Daily morning digest routine; sandbox and simulate only.",
  "scope": "global",
  "scope_id": "",
  "authority_tier_id": "sandbox_write",
  "routine_id": "morning_digest",
  "permitted_action_classes": ["observe", "suggest", "execute_simulate"],
  "excluded_action_classes": [],
  "required_approvals": [],
  "required_review_gates": ["inbox_studio"],
  "allowed_targets": [],
  "excluded_targets": [],
  "stop_conditions": ["artifact_produced"],
  "audit_required": false,
  "fallback_behavior": "downgrade_to_simulate",
  "enabled": true,
  "created_utc": "",
  "updated_utc": ""
}
```

---

## 6. Sample validation and explanation output

**Validate (valid):**
```
$ workflow-dataset trust contracts validate --id morning_digest_contract
Valid
```

**Validate (invalid – unknown tier):**
```
$ workflow-dataset trust contracts validate --id bad_contract
Unknown authority_tier_id: invalid_tier
```

**Explain – routine allowed:**
```
routine_id: morning_digest
contract_id: morning_digest_contract
authority_tier_id: sandbox_write
blocked: False
permitted: ['observe', 'suggest', 'draft', 'sandbox_write', 'execute_simulate']
excluded: []
required_approvals: []
explanation: Governed by contract morning_digest_contract and tier sandbox_write
```

**Explain – routine blocked (no contract):**
```
routine_id: blocked_followup
contract_id: —
authority_tier_id: —
blocked: True
permitted: []
excluded: []
required_approvals: []
explanation: No contract or tier
```

**Explain – why blocked (no_contract):**
```
reason: no_contract
explanation: ["No trusted routine contract found for this routine; actions are blocked by default."]
```

---

## 7. Exact tests run

```bash
cd workflow-llm-dataset
python -m pytest tests/test_trust_authority_contracts.py -v
# or: python3 -m pytest tests/test_trust_authority_contracts.py -v
```

Test names:

- `test_builtin_tiers_present`
- `test_tier_allows_action_observe`
- `test_tier_allows_action_sandbox`
- `test_validate_contract_valid`
- `test_validate_contract_unknown_tier`
- `test_validate_contract_permitted_excluded_conflict`
- `test_validate_contract_permitted_beyond_tier`
- `test_scope_precedence_project_over_global`
- `test_explain_why_blocked_no_contract`
- `test_explain_why_allowed_with_contract`
- `test_explain_routine_blocked_when_no_contract`
- `test_merge_contract_with_tier_excluded_wins`
- `test_scope_order_defined`

---

## 8. Remaining gaps for later refinement

- **Enforcement at runtime**: Planner/executor/background runner do not yet consult authority tiers or contracts before executing; this layer is additive and inspectable only until wired into execution gates.
- **Human policy integration**: No automatic mapping from human_policy presets to authority tiers or contracts; operator must keep policy and trust contracts aligned.
- **Worker-lane and recurring_routine scope**: Scope precedence and matching for `worker_lane` and `recurring_routine` could be refined with more context fields (e.g. lane_id, trigger_id).
- **Audit logging**: `audit_required` is stored but no audit log writer or reader is implemented.
- **Fallback behavior**: `fallback_behavior` is stored; no executor or background runner interprets it yet.
- **Allowed/excluded targets**: `allowed_targets` and `excluded_targets` are not enforced (path/resource checks).
- **Stop conditions**: `stop_conditions` are not interpreted by the executor.
- **CLI create/edit**: No `workflow-dataset trust contracts add` or `edit`; contracts must be edited in `data/local/trust/contracts.json` or via code.
- **Next trust review**: Heuristic is fixed to "trust contracts list" or "add contracts..."; could be driven by audit_required or last_updated_utc.
