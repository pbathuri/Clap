# M40I–M40L Production Runbooks + Release Gates + Launch Decision Pack — Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `production-runbook` group with `show`; `production-gates` group with `evaluate`; `launch-decision` group with `pack` and `explain`; top-level `production-readiness` command. |
| `src/workflow_dataset/mission_control/state.py` | Added `production_launch` block: `recommended_decision`, `failed_gate_ids`, `failed_gates_count`, `highest_severity_blocker`, `support_readiness`, `next_launch_review_action`. |
| `src/workflow_dataset/mission_control/report.py` | Added `[Production launch]` section: decision, failed_gates count, highest_blocker, support, next action. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M40I_M40L_PRODUCTION_LAUNCH_BEFORE_CODING.md` | Before-coding: existing structures, gaps, file plan, safety, principles, will NOT do. |
| `src/workflow_dataset/production_launch/__init__.py` | Package exports. |
| `src/workflow_dataset/production_launch/models.py` | ProductionRunbook, OperatingChecklistItem, DailyOperatingReviewStep, RecoveryEscalationPath, SupportPath, TrustedRoutineReviewStep, LaunchGateResult, LaunchBlocker, LaunchWarning, LaunchDecision (enum). |
| `src/workflow_dataset/production_launch/runbooks.py` | get_production_runbook(vertical_id): static checklist, daily review, recovery/support paths, trusted steps; merges vertical playbook recovery paths when vertical set. |
| `src/workflow_dataset/production_launch/gates.py` | Production gate IDs and labels; evaluate_production_gates(repo_root) → list[LaunchGateResult]; gates: release_readiness_not_blocked, supported_surface_freeze, deployment_bundle_valid, upgrade_recovery_posture, trust_review_posture, reliability_golden_path, operator_playbooks_ready, chosen_vertical_first_value. |
| `src/workflow_dataset/production_launch/decision_pack.py` | build_launch_decision_pack(repo_root), explain_launch_decision(), write_launch_decision_pack_to_dir(). |
| `tests/test_production_launch.py` | 12 tests: runbook creation, gate evaluation, decision pack structure, blockers affect decision, explain, write pack, blocker/warning to_dict, incomplete state. |
| `docs/M40I_M40L_PRODUCTION_LAUNCH_AND_DECISION_PACK.md` | This deliverable doc. |

## 3. Exact CLI usage

```bash
# Production runbook for active (or specified) vertical
workflow-dataset production-runbook show
workflow-dataset production-runbook show --vertical founder_operator_core
workflow-dataset production-runbook show --repo-root /path/to/repo --json

# Evaluate all production release gates
workflow-dataset production-gates evaluate
workflow-dataset production-gates evaluate --json

# Build launch decision pack (and optionally write to data/local/production_launch/)
workflow-dataset launch-decision pack
workflow-dataset launch-decision pack --write
workflow-dataset launch-decision pack --json

# Explain why current decision is launch / pause / repair
workflow-dataset launch-decision explain

# Aggregate production readiness (release readiness + gates + launch decision)
workflow-dataset production-readiness
```

## 4. Sample production runbook (excerpt)

```json
{
  "vertical_id": "founder_operator_core",
  "label": "Production runbook: Founder/operator vertical playbook",
  "description": "First-draft production runbook for operating and supporting the chosen vertical after release.",
  "operating_checklist": [
    {"id": "env_health", "label": "Environment health required_ok", "command_or_ref": "workflow-dataset health", "required": true},
    {"id": "release_readiness", "label": "Release readiness not blocked", "command_or_ref": "workflow-dataset release readiness", "required": true},
    {"id": "vertical_scope", "label": "Vertical scope and surface policy known", "command_or_ref": "workflow-dataset verticals scope-report", "required": true},
    {"id": "trust_cockpit", "label": "Trust/approval registry present", "command_or_ref": "workflow-dataset trust cockpit", "required": true},
    {"id": "first_value_path", "label": "First-value path progress acceptable", "command_or_ref": "workflow-dataset vertical-packs first-value", "required": false}
  ],
  "daily_operating_review": [
    {"id": "mission_control", "label": "Mission control snapshot", "command_or_ref": "workflow-dataset mission-control", "frequency": "daily"},
    {"id": "release_readiness", "label": "Release readiness status", "command_or_ref": "workflow-dataset release readiness", "frequency": "daily"},
    {"id": "launch_decision", "label": "Launch decision pack", "command_or_ref": "workflow-dataset launch-decision pack", "frequency": "daily"}
  ],
  "recovery_paths": [
    {"path_id": "recovery_guide", "label": "Recovery guide", "first_step_command": "workflow-dataset recovery guide --case failed_upgrade"},
    {"path_id": "vertical_stalled", "label": "Path stalled — operator commands", "first_step_command": "workflow-dataset vertical-packs recovery --id founder_operator_core --step 3"}
  ],
  "support_paths": [
    {"path_id": "release_triage", "label": "Release triage", "command_or_ref": "workflow-dataset release triage"},
    {"path_id": "supportability", "label": "Supportability report", "command_or_ref": "workflow-dataset release supportability"}
  ],
  "trusted_routine_review_steps": [
    {"step_id": "trust_cockpit", "label": "Trust cockpit and approvals", "command_or_ref": "workflow-dataset trust cockpit", "when": "pre_launch"},
    {"step_id": "reliability_run", "label": "Reliability golden-path run", "command_or_ref": "workflow-dataset reliability run", "when": "pre_launch"}
  ]
}
```

## 5. Sample release-gate report (excerpt)

```
Production gates  6/8 passed
  PASS  release_readiness_not_blocked: release_readiness=degraded
  PASS  supported_surface_freeze_complete: vertical=founder_operator_core scope defined
  PASS  deployment_bundle_valid: no bundle dir; optional for local-first
  FAIL  upgrade_recovery_posture: package not ready for first real user install
  PASS  trust_review_posture: registry_exists=true
  PASS  reliability_golden_path_health_acceptable: outcome=pass
  PASS  operator_playbooks_supportability_ready: playbooks=3 guidance=ok
  PASS  chosen_vertical_first_value_proof_acceptable: vertical=founder_operator_core first-value path ok
```

## 6. Sample launch decision pack (excerpt)

```json
{
  "chosen_vertical_summary": {"active_vertical_id": "founder_operator_core", "label": "founder_operator_core"},
  "supported_scope": {"vertical_id": "founder_operator_core", "core_surfaces": [...], "hidden_or_non_core_surfaces": [...]},
  "release_gate_results": [
    {"gate_id": "release_readiness_not_blocked", "label": "Release readiness not blocked", "passed": false, "detail": "release_readiness=blocked"},
    {"gate_id": "supported_surface_freeze_complete", "label": "Supported surface freeze complete", "passed": true, "detail": "vertical=founder_operator_core scope defined"}
  ],
  "open_blockers": [
    {"id": "block_0", "summary": "Rollout first_user_ready false", "source": "rollout", "remediation_hint": "Run workflow-dataset rollout status and address blocks.", "severity": "blocker"}
  ],
  "open_warnings": [],
  "recovery_posture": "Recovery guide and vertical recovery paths available; run workflow-dataset recovery guide / vertical-packs recovery.",
  "trust_posture": "Trust cockpit: registry_exists checked; supportability guidance=needs_operator",
  "support_posture": "workflow-dataset release triage",
  "recommended_decision": "repair_and_review",
  "explain": "Blockers present (1): Rollout first_user_ready false. Resolve blockers then re-run launch-decision-pack."
}
```

## 7. Exact tests run

```bash
python3 -m pytest tests/test_production_launch.py -v
```

- test_runbook_creation_empty_vertical  
- test_runbook_creation_with_vertical  
- test_runbook_to_dict  
- test_gate_evaluation_returns_list  
- test_gate_result_to_dict  
- test_launch_decision_pack_structure  
- test_launch_decision_pack_blockers_affect_decision  
- test_launch_decision_explain_returns_string  
- test_launch_decision_explain_with_pack  
- test_write_launch_decision_pack_to_dir  
- test_launch_blocker_and_warning_to_dict  
- test_incomplete_readiness_state_behavior  

All 12 passed.

## 8. Remaining gaps for later refinement

- **Gate weighting**: All production gates are treated equally for “critical” vs “advisory”; could add gate severity or required vs optional.
- **Deployment bundle**: `deployment_bundle_valid` is optional (passes if no bundle dir); could tighten when Pane 2 bundle is present.
- **First-value proof**: Vertical first-value gate uses milestone progress; could align with a dedicated “first-value proof” run or checklist.
- **Runbook persistence**: Runbook is built on demand; no persisted customization or per-vertical overrides in `data/local`.
- **Mission control next action**: `next_launch_review_action` is generic; could be more contextual (e.g. “fix gate X” when only one gate fails).
- **Rollback**: No explicit rollback decision or rollback runbook step; recovery paths point to recovery guide and vertical recovery.
- **Narrow launch**: `launch_narrowly` is recommended when warnings exist but no blockers; no separate “narrow scope” definition (e.g. single cohort or single workflow) yet.
