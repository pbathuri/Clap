# M49H.1 — Reconcile Policies + Restore Playbooks: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/migration_restore/__init__.py` | Added imports for reconcile_policies (get_reconcile_policy, list_reconcile_policies, get_restore_playbook, list_restore_playbooks, POLICY_*) and operator_guidance (build_restore_operator_summary, format_operator_summary_text). |
| `tests/test_migration_restore.py` | Added tests: test_reconcile_policy_conservative, test_restore_playbook_same_machine, test_build_restore_operator_summary. |

## 2. Files created

| File | Purpose |
|------|---------|
| (M49H.1 models in existing `models.py`) | ReconcilePolicy, RestorePlaybook, RestorePlaybookStep. |
| `src/workflow_dataset/migration_restore/reconcile_policies.py` | Built-in reconcile policies (conservative_restore, balanced_restore, production_safe_restore); built-in playbooks (same_machine_restore, new_machine_restore, after_upgrade_restore, partial_failure_recovery); get/list for policies and playbooks; custom load from data/local/migration_restore. |
| `src/workflow_dataset/migration_restore/operator_guidance.py` | build_restore_operator_summary(restore_result, reconcile_result, restore_candidate_id, target_repo_root); format_operator_summary_text(summary). |
| `docs/M49H1_RECONCILE_POLICIES_RESTORE_PLAYBOOKS_DELIVERABLE.md` | This file. |

CLI commands (in existing `cli.py`): `migration policy` (list / show --id), `migration playbooks`, `migration playbook-show --id`, `migration operator-summary --id`.

## 3. Sample reconcile policy

**Policy id:** `production_safe_restore`  
**Name:** Production-safe restore  

- **Description:** No overwrite of critical state; rebuild requires explicit review; production-safe defaults.  
- **overwrite_target_allowed:** false  
- **skip_restored_allowed:** true  
- **rebuild_required_action:** require_review  
- **require_review_for_overwrite:** true  
- **production_safe:** true  
- **scope_note:** For production or high-trust targets; never auto-overwrite.  

## 4. Sample restore playbook

**Playbook id:** `new_machine_restore`  
**Name:** New-machine restore  
**Description:** Restore continuity state to a different machine or environment.  
**When to use:** You moved the bundle to a new machine; target repo is empty or you want to bring over state.  
**Suggested policy:** conservative_restore  
**Applicable conflict classes:** partial, conflicting, unsupported  

**Steps:**

| Order | Label | Command / action |
|-------|--------|-------------------|
| 1 | Validate bundle | workflow-dataset migration validate --bundle \<bundle_ref\> |
| 2 | Dry-run | workflow-dataset migration dry-run --bundle \<bundle_ref\> |
| 3 | Restore (approved) | workflow-dataset migration restore --bundle \<bundle_ref\> --approved |
| 4 | Reconcile | workflow-dataset migration reconcile --id \<restore_id\> |
| 5 | Operator summary | workflow-dataset migration operator-summary --id \<restore_id\> |

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_migration_restore.py -v
```

New/updated tests:

- `test_reconcile_policy_conservative` — get policy conservative_restore, list includes all three policies  
- `test_restore_playbook_same_machine` — get playbook same_machine_restore, steps and suggested_policy_id, list playbooks  
- `test_build_restore_operator_summary` — build_restore_operator_summary with restore_result, format_operator_summary_text  

All existing migration_restore tests plus the above should pass.

## 6. Next recommended step for the pane

- **Apply policy in flows:** When running restore or reconcile, accept an optional `--policy \<policy_id\>` and apply it (e.g. block overwrite when policy is conservative/production_safe; require_review for rebuild when policy says require_review).  
- **Suggest playbook from conflict classes:** After reconcile, suggest a playbook whose applicable_conflict_classes match the current conflict_classes (e.g. suggest partial_failure_recovery when unsupported/partial are present).  
- **Persist operator summary:** Optionally write the operator summary to `data/local/migration_restore/summaries/<restore_id>.json` or `.md` so operators can review it later and mission control can show “last restore summary.”
