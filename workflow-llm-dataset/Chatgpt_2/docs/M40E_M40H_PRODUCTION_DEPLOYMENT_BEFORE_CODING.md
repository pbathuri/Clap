# M40E–M40H — Production Deployment Bundle: Before Coding

## 1. What deployment/upgrade/recovery structures already exist

### Release
- **release/**: dashboard_data, handoff_profiles, package_compare, package_revision, reporting_workspaces (REPORTING_WORKFLOWS), staging_board, review_state, review_metrics, workspace_export_contract, lane_views.

### Local deployment
- **local_deployment/**: profile (build_local_deployment_profile, get_deployment_dir, write_deployment_profile), install_check (run_install_check), first_run (run_first_run: ensure dirs, install-check, onboarding bootstrap). Local-only; no cloud.

### Install / upgrade
- **install_upgrade/models.py**: ProductVersion, EnvRequirements, EnabledModulesSnapshot, PackRuntimeSnapshot, InstallProfile, MigrationRequirement, RollbackCheckpoint, ReleaseChannel (stable/preview/internal).
- **install_upgrade/version.py**: read_current_version, write_current_version, get_package_version_from_pyproject, get_install_dir, get_current_version_path.
- **install_upgrade/upgrade_plan.py**: UpgradePlan (current/target version, migration_steps, impact_preview, incompatible_warnings, blocked_reasons, can_proceed, reversible_overall), build_upgrade_plan.
- **install_upgrade/compatibility.py**: get_unsafe_upgrade_warnings, check_upgrade_path, build_compatibility_matrix; channels, version comparison.
- **install_upgrade/apply_upgrade.py**: create_rollback_checkpoint, apply_upgrade, rollback_to_checkpoint; checkpoints dir, version backup, state_snapshot.
- **install_upgrade/channels.py**: get_channel, list_channels, RELEASE_CHANNELS.
- **install_upgrade/reports.py**, **install_upgrade/cli.py**: upgrade/rollback CLI and reports.

### Distribution
- **distribution/models.py**: InstallBundle (bundle_id, version, description, edge_profile_summary, readiness_summary, required_capabilities, required_approvals_setup, machine_assumptions, product_surfaces_summary), FieldDeploymentProfile, PackAwareInstallProfile.
- **distribution/bundle.py**: build_install_bundle (from local deployment profile + readiness), write_install_bundle → data/local/distribution/bundles/<bundle_id>.json.
- **distribution/install_profile.py**: PACK_DEFAULTS (founder_ops_starter, analyst_starter, developer_starter, document_worker_starter), get_pack_aware_install_profile, build_field_deployment_profile.
- **distribution/readiness.py**, **distribution/update_planner.py**, **distribution/checklists.py**, **distribution/install_profile.py**.

### Release readiness
- **release_readiness/models.py**: ReleaseReadinessStatus, ReleaseBlocker, ReleaseWarning, SupportedWorkflowScope, KnownLimitation, SupportabilityStatus, READINESS_READY/BLOCKED/DEGRADED, GUIDANCE_*.
- **release_readiness/readiness.py**: build_release_readiness (rollout, package_readiness, env health, acceptance → blockers, warnings, supported_scope).
- **release_readiness/handoff_pack.py**: build_handoff_pack (readiness + user release pack + supportability, artifacts: support bundle, OPERATOR_RUNBOOKS, RECOVERY_ESCALATION).
- **release_readiness/supportability.py**: build_supportability_report.
- **release_readiness/pack.py**: build_user_release_pack.

### Reliability / recovery
- **reliability/models.py**: GoldenPathScenario, ReliabilityRunResult, RecoveryCase (case_id, name, when_to_use, steps_guide, related_subsystems).
- **reliability/recovery_playbooks.py**: RECOVERY_CASES (broken_pack_state, failed_upgrade, missing_runtime_capability, blocked_approval_policy, stuck_project_session_agent, invalid_workspace_state); suggest_recovery, get_recovery_guide.
- **reliability/degraded_profiles.py**, **reliability/fallback_matrix.py**, **reliability/harness.py**, **reliability/golden_paths.py**.

### Packs / vertical
- **packs/**: pack_models, registry, install_flows, certification, gallery, pack_installer, pack_activation, pack_resolver, etc.
- **vertical_packs/**: CuratedVerticalPack, first_value_path, playbooks (recovery paths, operator guidance when stalled), apply_vertical_defaults, progress.

### Runtime / support
- **runtime_mesh/**: backend_registry, summary, policy, integration_registry, llama_cpp_check.
- **rollout/**: readiness, support-bundle, runbooks, tracker, launcher, demos.
- **progress/recovery.py**: build_stalled_recovery, format_stalled_recovery (M27L.1).
- **triage/**: health, playbooks (mitigation), operator do-now.

---

## 2. What is missing for a true production deployment bundle

- **Single “production deployment bundle” abstraction** per chosen vertical (e.g. founder_operator_prod) that: (1) pins the vertical (curated pack + value pack), (2) lists required workflows/packs/assets, (3) declares required runtime profile and allowed trust posture, (4) pins queue/day/workspace settings references, (5) includes support/recovery references and excluded/quarantined surface metadata. Today: InstallBundle is generic; FieldDeploymentProfile is pack-centric but not “production cut” with upgrade/rollback/recovery posture.
- **Explicit supported upgrade path and supported rollback path** for the bundle (min/max product version, channel constraints, “risky upgrade” detection). install_upgrade has UpgradePlan and check_upgrade_path but no bundle-scoped “this bundle supports upgrades from X to Y” and “rollback readiness” summary.
- **Recovery posture** for the bundle: which recovery cases apply, link to vertical playbook recovery, degraded startup guidance. Reliability has RECOVERY_CASES and suggest_recovery; no bundle-level “recovery posture” and “recovery-report” for the deployment cut.
- **Deployment health summary** aggregating: bundle id, validation status, upgrade readiness, rollback readiness, recovery posture, blocked deployment risks. Mission control and handoff pack are global; no “active deployment bundle” and “blocked deployment risks” for the cut.
- **CLI**: deploy-bundle show, build --id, validate, upgrade-path, recovery-report; and **mission control** section for active deployment bundle, upgrade/rollback readiness, recovery posture, blocked risks.
- **Packaging output**: A written bundle manifest (e.g. data/local/deploy_bundle/active.json or data/local/distribution/bundles/<bundle_id>.json) that includes vertical defaults, required workflows, allowed trust, support/recovery refs, excluded surfaces. distribution/bundle.build_install_bundle exists but does not take a vertical id or produce a “production cut” manifest.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/deploy_bundle/models.py` — ProductionDeploymentBundle, BundleContents, RequiredRuntimeProfile, RequiredPacksAssets, SupportedUpgradePath, SupportedRollbackPath, RecoveryPosture, DeploymentHealthSummary, ExcludedSurfaceMetadata. |
| Create | `src/workflow_dataset/deploy_bundle/registry.py` — BUILTIN_DEPLOYMENT_BUNDLES (e.g. founder_operator_prod), get_deployment_bundle(bundle_id), list_deployment_bundle_ids(); build bundle from vertical_packs + distribution + install_upgrade + release_readiness + reliability. |
| Create | `src/workflow_dataset/deploy_bundle/packaging.py` — build_bundle_manifest(bundle_id, repo_root), write_bundle_manifest(); contents: vertical defaults, required_workflows, required_pack_ids, allowed_trust_preset_ids, required_queue_day_workspace_refs, support_recovery_refs, excluded_surfaces. |
| Create | `src/workflow_dataset/deploy_bundle/validation.py` — validate_bundle(bundle_id, repo_root) → validation result (errors, warnings, ready); check required runtime, packs, trust, readiness. |
| Create | `src/workflow_dataset/deploy_bundle/upgrade_rollback.py` — get_supported_upgrade_path(bundle_id, repo_root), get_rollback_readiness(bundle_id, repo_root), get_risky_upgrade_warnings(bundle_id, target_version, repo_root); delegate to install_upgrade. |
| Create | `src/workflow_dataset/deploy_bundle/recovery_report.py` — build_recovery_report(bundle_id, repo_root): recovery posture, applicable recovery cases, vertical playbook recovery refs, degraded startup guidance; delegate to reliability + vertical_packs playbooks. |
| Create | `src/workflow_dataset/deploy_bundle/health.py` — build_deployment_health_summary(bundle_id, repo_root): active bundle, validation status, upgrade readiness, rollback readiness, recovery posture, blocked_risks. |
| Create | `src/workflow_dataset/deploy_bundle/store.py` — get_active_bundle(repo_root), set_active_bundle(bundle_id, repo_root); data/local/deploy_bundle/active.json. |
| Create | `src/workflow_dataset/deploy_bundle/__init__.py` — Re-export models, registry, packaging, validation, upgrade_rollback, recovery_report, health, store. |
| Modify | `src/workflow_dataset/cli.py` — Add deploy-bundle Typer: show, build --id, validate, upgrade-path, recovery-report. |
| Modify | `src/workflow_dataset/mission_control/state.py` — Add deploy_bundle_state: active_bundle_id, upgrade_readiness, rollback_readiness, recovery_posture_summary, blocked_deployment_risks. |
| Modify | `src/workflow_dataset/mission_control/report.py` — Add [Deploy bundle] section. |
| Create | `tests/test_deploy_bundle.py` — test_bundle_model, test_bundle_validation, test_upgrade_path, test_rollback_readiness, test_recovery_report, test_invalid_bundle. |
| Create | `docs/samples/M40_deployment_bundle_sample.json` — Sample production deployment bundle (founder_operator_prod). |
| Create | `docs/samples/M40_upgrade_path_sample.json` — Sample upgrade-path report. |
| Create | `docs/samples/M40_recovery_rollback_readiness_sample.json` — Sample recovery/rollback readiness. |
| Create | `docs/M40E_M40H_PRODUCTION_DEPLOYMENT_DELIVERABLE.md` — Deliverable (files, CLI, samples, tests, gaps). |

---

## 4. Safety / risk note

- **Build and apply** are local-only: writing manifest and setting active_bundle_id under data/local/deploy_bundle. No cloud deploy, no automatic upgrade execution; upgrade/rollback execution remains via existing install_upgrade CLI with operator control.
- **Validation** only reads state and reports errors/warnings; it does not change trust, approval scope, or runtime. Recovery-report is read-only guidance.
- **No new execution surface**: deploy_bundle orchestrates existing release_readiness, install_upgrade, reliability, vertical_packs; no new sandbox or network calls. Excluded surface metadata is advisory (no enforcement in this block).

---

## 5. Deployment-hardening principles

- **One primary vertical for first-draft**: founder_operator_prod as the chosen production cut; reuse founder_operator_core curated pack and existing install/upgrade/recovery flows.
- **Explicit over implicit**: Supported upgrade path, rollback readiness, and recovery posture are first-class fields; we do not hide unsupported or risky upgrade paths.
- **Reuse over reinvention**: Production bundle = reference to vertical_packs + distribution InstallBundle/FieldDeploymentProfile + install_upgrade UpgradePlan/RollbackCheckpoint + release_readiness + reliability RECOVERY_CASES and vertical playbooks.
- **Recovery and rollback visible**: Recovery-report and mission control show recovery posture and rollback readiness; operator can act on them.

---

## 6. What this block will NOT do

- **No cloud deployment**: No AWS/GCP/Azure or container orchestration; local deployment bundle and manifest only.
- **No package-manager replacement**: Pip/uv/poetry remain as-is; we only define and validate the deployment cut.
- **No rebuild of install/upgrade/recovery**: install_upgrade, distribution, release_readiness, reliability, vertical_packs remain unchanged; we add a layer that references and orchestrates them.
- **No enforcement of excluded surfaces**: Excluded/quarantined surface metadata is stored and reported; enforcement (e.g. hiding surfaces) is out of scope for this block.
- **No polish**: First-draft bundle manifest and CLI; no UI beyond CLI and mission-control report.
