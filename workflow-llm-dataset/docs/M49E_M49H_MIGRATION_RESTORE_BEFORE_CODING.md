# M49E–M49H — Migration Validation + Restore/Reconcile Flows: Before Coding

## 1. What validation/restore/recovery behavior already exists

| Area | What exists | Notes |
|------|-------------|--------|
| **state_durability** | StartupReadiness, RecoverablePartialState, PersistenceBoundary, build_startup_readiness, build_reconcile_report, build_durable_snapshot; SUBSYSTEM_BOUNDARIES (workday, continuity_*, project_current, background_queue). | Health checks and reconcile *report* (no writes); no bundle export/import or target-environment validation. |
| **continuity_engine** | Store: last_shutdown, carry_forward, next_session, rhythm; load/save per file. | No portable bundle format; no restore-from-bundle. |
| **install_upgrade** | Upgrade plan, migration steps, migration report, compatibility matrix, check_upgrade_path. | Product *version* upgrade/migration, not continuity state restore across environments. |
| **deploy_bundle** | validate_bundle (install check, release readiness, pack); recovery_report (recovery cases, playbooks). | Deployment bundle validation; not continuity bundle or restore. |
| **reliability** | Recovery playbooks (broken_pack, failed_upgrade, missing_runtime, blocked_approval, stuck_project, invalid_workspace). | Recovery *steps*; no restore candidate or reconcile flow. |
| **repair_loops** | pattern_continuity_resume_reconciliation (state reconcile command); no bundle. | Runs state reconcile; does not validate/restore a bundle. |

## 2. What is missing for true migration-safe restore

- **Continuity bundle as portable artifact** — No explicit format for “bundle” (manifest + subsystem payloads) that can be validated and restored; state_durability boundaries define *what* to consider but not a packable bundle.
- **Target environment profile** — No model for “target” (paths, product version, runtime, optional trust/governance constraints) to validate a bundle against.
- **Restore candidate + validation report** — No “restore candidate” (bundle ref + target) with a structured validation report (version compat, runtime compat, missing backend, local-only exclusion, trust compat, experimental warnings).
- **Restore blocker / restore confidence** — No explicit “blocker” or “confidence score” for restore; startup readiness is local health only.
- **Reconcile action + conflict class** — Reconcile report suggests actions but no first-class “reconcile action” or “conflict” (partial, stale, conflicting, unsupported) for post-restore reconciliation.
- **Rebuild-required component** — No “this component cannot be restored; must be rebuilt on target.”
- **Dry-run restore / restore with review** — No dry-run or review-before-write restore flow.
- **Post-restore verification** — No explicit verify step after restore.

## 3. Exact file plan

| Area | Path | Purpose |
|------|------|--------|
| Doc | `docs/M49E_M49H_MIGRATION_RESTORE_BEFORE_CODING.md` | This file. |
| Models | `src/workflow_dataset/migration_restore/models.py` | TargetEnvironmentProfile, RestoreCandidate, RestoreValidationReport, ReconcileAction, ConflictClass, StaleStateNote, RebuildRequiredComponent, RestoreConfidence, RestoreBlocker; ContinuityBundleManifest (minimal). |
| Bundle | `src/workflow_dataset/migration_restore/bundle.py` | Bundle manifest build from state_durability boundaries + continuity store; list_bundles (e.g. from data/local/migration_restore/bundles/ or “latest” from snapshot). |
| Validation | `src/workflow_dataset/migration_restore/validation.py` | validate_bundle_for_target (version, runtime, missing backend, local-only exclusion, trust compat, experimental warnings); produce RestoreValidationReport. |
| Flows | `src/workflow_dataset/migration_restore/flows.py` | dry_run_restore, restore_with_review, partial_restore, conflict_aware_reconcile, rebuild_on_target_components, post_restore_verify. |
| CLI | `src/workflow_dataset/cli.py` | migration_group: validate, dry-run, restore, reconcile, verify. |
| Mission control | `src/workflow_dataset/mission_control/state.py` + report | migration_restore_state: latest_restore_candidate, restore_blockers, reconcile_required_components, restore_confidence_score, next_recommended_restore_action. |
| Tests | `tests/test_migration_restore.py` | Validation, compatibility mismatch, partial restore, reconcile, rebuild-required, failed/weak-confidence. |
| Deliverable | `docs/M49E_M49H_MIGRATION_RESTORE_DELIVERABLE.md` | Files, CLI, samples, tests, gaps. |

## 4. Safety/risk note

- **Do not silently overwrite incompatible local state** — Restore must validate first; dry-run and restore-with-review must be explicit; blockers must prevent unsafe restore.
- **Do not bypass trust/governance/policy** — Validation must include trust/governance compatibility; restore must not skip approval/review boundaries.
- **Do not hide restore uncertainty** — Restore confidence and blockers must be visible; partial restore and rebuild-required must be clearly reported.

## 5. Reconcile principles

- **Explicit restore and reconcile** — Restore is an explicit operation; reconcile is the process of aligning restored state with target-machine realities (conflicts, stale, rebuild-required).
- **Reviewable** — Dry-run and validation report are inspectable; operator approves restore.
- **Local-first** — No cloud sync; bundle and target are local or explicitly specified paths/environments.
- **Safe device/environment change** — Support moving continuity state to another machine or environment with clear compatibility and conflict handling.

## 6. What this block will NOT do

- Replace install_upgrade, state_durability, or recovery playbooks wholesale.
- Implement generic backup/restore software or hidden auto-sync restore.
- Bypass trust/policy/audit; restore respects validation and review.
- Optimize for cloud sync; focus is local-first migration and restore/reconcile path.
