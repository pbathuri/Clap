# M50E–M50H — v1 Operational Discipline + Support Finalization: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `v1_ops_group` and commands: status, support-posture, maintenance-pack, review-cadence, recovery-path. |
| `src/workflow_dataset/mission_control/state.py` | Added `v1_ops_state` slice: current_support_posture, overdue_maintenance_or_review, top_unresolved_v1_risk, recommended_stable_v1_support_action, rollback_readiness_posture. |
| `src/workflow_dataset/mission_control/report.py` | Added [v1 ops] section to report output. |

## 2. Files created

| File | Purpose |
|------|---------|
| `docs/M50E_M50H_V1_OPERATIONAL_DISCIPLINE_BEFORE_CODING.md` | Before-coding: existing discipline, gaps, file plan, safety, principles, what we do not do. |
| `src/workflow_dataset/v1_ops/__init__.py` | Package exports. |
| `src/workflow_dataset/v1_ops/models.py` | V1SupportPosture, MaintenanceRhythm, ReviewCadenceRef, IncidentClass, RecoveryPath, EscalationPath, RollbackReadiness, SupportOwnershipNote, StableV1MaintenancePack. |
| `src/workflow_dataset/v1_ops/posture.py` | build_v1_support_posture (from release_readiness, stability_reviews, deploy_bundle, repair_loops). |
| `src/workflow_dataset/v1_ops/maintenance_pack.py` | build_stable_v1_maintenance_pack (posture, rhythm, review cadence, recovery paths, escalation, rollback readiness, ownership). |
| `src/workflow_dataset/v1_ops/runbook.py` | Daily/weekly review items; when v1 degrades; safe repair; requires rollback; requires pause/narrow. |
| `src/workflow_dataset/v1_ops/mission_control.py` | get_v1_ops_state for mission-control slice. |
| `tests/test_v1_ops.py` | Tests for models, posture, maintenance pack, runbook, mission control state. |
| `docs/M50E_M50H_V1_OPERATIONAL_DISCIPLINE_DELIVERABLE.md` | This file. |

## 3. Exact CLI usage

```bash
# Current v1 status (posture, overdue, top risk, recommended action, rollback readiness)
workflow-dataset v1-ops status
workflow-dataset v1-ops status --json

# v1 support posture (level, paths, rhythm, cadence, recovery summary, rollback ready)
workflow-dataset v1-ops support-posture
workflow-dataset v1-ops support-posture --json

# Stable v1 maintenance pack (full pack: posture, rhythm, cadence, recovery paths, escalation, rollback, ownership)
workflow-dataset v1-ops maintenance-pack
workflow-dataset v1-ops maintenance-pack --json

# Review cadence (active cadence, next due, overdue)
workflow-dataset v1-ops review-cadence
workflow-dataset v1-ops review-cadence --json

# Recovery path: list all or show one case
workflow-dataset v1-ops recovery-path
workflow-dataset v1-ops recovery-path --case broken_pack_state
workflow-dataset v1-ops recovery-path --case failed_upgrade --json
```

## 4. Sample v1 support posture

```json
{
  "posture_id": "v1_stable_posture",
  "support_level": "sustained",
  "support_paths": [
    "release_readiness: workflow-dataset supportability",
    "stability_reviews: workflow-dataset stability-reviews latest (next_due=...)",
    "deploy_bundle: workflow-dataset deploy-bundle recovery-report"
  ],
  "maintenance_rhythm_id": "stable_v1_daily_weekly",
  "review_cadence_id": "rolling_stability",
  "recovery_posture_summary": "Run workflow-dataset deploy-bundle recovery-report for recovery steps.",
  "rollback_ready": false,
  "as_of_utc": "2025-03-16T12:00:00Z"
}
```

## 5. Sample maintenance pack (excerpt)

- **pack_id**: stable_v1_maintenance_pack  
- **support_posture**: (as above)  
- **maintenance_rhythm**: stable_v1_daily_weekly — daily: supportability, repair-loops list, v1-ops status; weekly: stability-reviews generate, stability-decision pack, v1-ops maintenance-pack  
- **review_cadence_ref**: rolling_stability, next_due_iso from stability_reviews  
- **recovery_paths**: from reliability RECOVERY_CASES (broken_pack_state, failed_upgrade, missing_runtime_capability, blocked_approval_policy, stuck_project_session_agent, invalid_workspace_state)  
- **escalation_paths**: guidance_rollback, repair_failed, blocked_approval  
- **rollback_readiness**: ready, prior_stable_ref, reason, recommended_action  
- **ownership_notes**: Operator/release owner, Reliability owner  

## 6. Sample recovery / escalation output

**Recovery path (one case):**

```
broken_pack_state  Broken or incompatible pack
  incident_class: broken_pack_state
  1. Run: workflow-dataset packs list (or workflow-dataset kits list)...
  2. Identify the pack causing errors from logs or reliability report...
  3. Run: workflow-dataset packs suspend --id <pack_id>...
```

**Escalation paths (from maintenance pack):**

- **guidance_rollback**: Post-deployment guidance = needs_rollback or rollback → escalate to Operator/release owner; handoff: support_bundle  
- **repair_failed**: Repair loop failed and rollback not sufficient → Operator/reliability owner; handoff: repair_loop_id + support_bundle  
- **blocked_approval**: Blocked approval or policy mode → Trust/approval owner; handoff: support_bundle  

## 7. Exact tests run

```bash
pytest tests/test_v1_ops.py -v
```

Tests:  
- test_v1_support_posture_model  
- test_maintenance_rhythm_model  
- test_recovery_path_model  
- test_rollback_readiness_model  
- test_stable_v1_maintenance_pack_roundtrip  
- test_build_v1_support_posture  
- test_build_stable_v1_maintenance_pack  
- test_runbook_daily_weekly  
- test_runbook_when_degrades_safe_rollback_pause  
- test_get_v1_ops_state  
- test_incident_class_enum  

## 8. Remaining gaps for later refinement

- **Configurable ownership** — Ownership notes are default list; no persisted config (e.g. data/local/v1_ops/ownership.json) for site-specific owners.  
- **Overdue logic** — Overdue uses review_cadence next_due only; could include ops_jobs overdue.  
- **Top v1 risk** — Currently repair_slice + support_level + blocked_deployment_risks; could integrate stability decision (pause/rollback) and quality guidance.  
- **Runbook as data** — Runbook is code constants; could be loaded from YAML/JSON for customization.  
- **Incident class mapping** — Recovery paths use reliability case_id as incident_class; no formal mapping from “degradation/outage/drift” to recovery case.  
- **Weak-support / missing-owner** — No explicit “weak support” or “missing owner” flag in posture; could add when no active bundle or no ownership_notes configured.  
