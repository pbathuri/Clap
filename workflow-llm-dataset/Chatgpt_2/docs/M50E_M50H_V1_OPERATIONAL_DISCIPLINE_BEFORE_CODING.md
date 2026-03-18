# M50E–M50H — v1 Operational Discipline + Support Finalization: Before Coding

## 1. What operational/support discipline already exists

| Area | What exists | Notes |
|------|-------------|--------|
| **release_readiness/supportability** | build_supportability_report, reproducible_state_summary, guidance (safe_to_continue / needs_operator / needs_rollback). | Supportability confidence and next support action; no explicit “v1 support posture” or ownership. |
| **stability_reviews** | ReviewCadence (daily, weekly, rolling_stability), RollbackPolicy, thresholds, pack_builder (continue/narrow/repair/pause/rollback), cadences.py (next_review_due). | Review cadence and rollback policy; no single “v1 maintenance rhythm” or “support path” aggregation. |
| **reliability** | RecoveryCase, RECOVERY_CASES (broken_pack, failed_upgrade, missing_runtime, blocked_approval, stuck_project, invalid_workspace), recovery playbooks. | Recovery steps by case; not framed as “v1 incident class” or “v1 escalation path.” |
| **deploy_bundle** | recovery_report (recovery posture, applicable recovery cases), validation, upgrade_rollback. | Bundle-level recovery; no v1-wide support posture. |
| **repair_loops** | BoundedRepairPlan, patterns (continuity_resume_reconciliation, etc.), mission_control slice (top repair-needed, next action). | Repair loops and escalation; no “v1 recovery path” or “rollback readiness” summary. |
| **production_launch** | post_deployment_guidance, sustained_use checkpoints. | Post-deploy and sustained-use; no “v1 support ownership” or “maintenance pack.” |
| **ops_jobs** | OpsJob, cadence, reliability_refresh, queue_calmness_review, issue_cluster_review, escalation_targets. | Maintenance jobs and cadences; no unified “v1 maintenance rhythm” or “review responsibilities” doc. |
| **rollout** | support_bundle, issues report, RECOVERY_ESCALATION.md (recovery path, escalation tree). | Rollout recovery and escalation; doc-only for path; no v1-ops CLI. |
| **governance/review_domains** | Review domains, policies, escalation packs. | Governance; not “support path” or “operator runbook” for v1. |
| **migration_restore** | Validate, dry-run, restore, reconcile, verify; reconcile policies; restore playbooks; operator summary. | Migration support; not “v1 support path” or “maintenance pack.” |

## 2. What is missing for true stable-v1 supportability

- **v1 support posture** — No single explicit model: how stable v1 is supported (support paths, maintenance rhythm, ownership). Supportability report and recovery cases exist but are not assembled into a “v1 support posture.”
- **Maintenance rhythm** — Ops jobs and stability cadences exist separately; no first-class “v1 maintenance rhythm” (daily/weekly tasks, review cadence, calendar hint).
- **Review cadence as v1 responsibility** — Cadences exist in stability_reviews; no “what to review daily/weekly for v1” or “review responsibilities” in one place.
- **Incident class + recovery path** — Recovery cases exist; no “incident class” (e.g. degradation, outage, drift) with a clear “recovery path” and “escalation path” for v1.
- **Rollback readiness** — Rollback policy exists in stability_reviews; no aggregated “rollback readiness posture” (ready / not_ready / prior_stable_ref) for v1 ops.
- **Support ownership note** — No “who owns v1 support” or “who does what” model.
- **Stable-v1 maintenance pack** — No single “maintenance pack” that lists: support paths, rhythm, review cadence, recovery path, escalation, rollback readiness, ownership.
- **Operator runbook finalization** — No consolidated “what to review daily/weekly,” “what to do when v1 degrades,” “what can be repaired safely,” “what requires rollback,” “what requires pause/narrow.”
- **v1-ops CLI and mission control** — No `v1-ops status`, `support-posture`, `maintenance-pack`, `review-cadence`, `recovery-path` or mission-control slice for v1.

## 3. Exact file plan

| Area | Path | Purpose |
|------|------|--------|
| Doc | `docs/M50E_M50H_V1_OPERATIONAL_DISCIPLINE_BEFORE_CODING.md` | This file. |
| Models | `src/workflow_dataset/v1_ops/models.py` | V1SupportPosture, MaintenanceRhythm, ReviewCadenceRef, IncidentClass, RecoveryPath, EscalationPath, RollbackReadiness, SupportOwnershipNote, StableV1MaintenancePack. |
| Posture | `src/workflow_dataset/v1_ops/posture.py` | build_v1_support_posture (from release_readiness, stability_reviews, reliability, repair_loops, ops_jobs). |
| Pack | `src/workflow_dataset/v1_ops/maintenance_pack.py` | build_stable_v1_maintenance_pack (support paths, rhythm, review cadence, recovery path, escalation, rollback readiness, ownership). |
| Runbook | `src/workflow_dataset/v1_ops/runbook.py` | Daily/weekly review items; when v1 degrades; safe repair; when rollback; when pause/narrow. |
| CLI | `src/workflow_dataset/cli.py` | v1_ops_group: status, support-posture, maintenance-pack, review-cadence, recovery-path. |
| Mission control | `src/workflow_dataset/mission_control/state.py` + report | v1_ops_state: current support posture, overdue maintenance/review, top v1 risk, recommended support action, rollback-readiness. |
| Tests | `tests/test_v1_ops.py` | Posture, maintenance pack, incident/recovery/escalation, rollback readiness, runbook, weak-support. |
| Deliverable | `docs/M50E_M50H_V1_OPERATIONAL_DISCIPLINE_DELIVERABLE.md` | Files, CLI, samples, tests, gaps. |

## 4. Safety/risk note

- **Do not override release/reliability/support** — This layer aggregates and presents; it does not replace release gates, recovery playbooks, or supportability logic.
- **Do not hide rollback or escalation** — Rollback readiness and escalation paths must remain visible; operator runbook must state when rollback or pause is required.
- **Do not invent support ownership** — Ownership note is explicit and configurable; avoid implying ownership where none is set.

## 5. Operational-discipline principles

- **Stable v1 is a supportable product** — v1 has defined support paths, maintenance rhythm, review cadence, recovery and escalation, and rollback readiness.
- **Operator ownership is explicit** — Who does what for v1 health is documented and queryable.
- **Reviewable and local-first** — All v1-ops outputs are inspectable via CLI and mission control; no hidden automation that changes production without review.

## 6. What this block will NOT do

- Implement enterprise ITSM or generic support documentation only.
- Rebuild release, reliability, support, deploy_bundle, or migration systems from scratch.
- Reopen product scope; focus is final support and operating discipline for stable v1.
