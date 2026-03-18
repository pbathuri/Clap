# M40E–M40H — Production Deployment Bundle + Upgrade/Recovery Hardening (Deliverable)

First-draft production deployment layer: bundle model, packaging, validation, upgrade/rollback hardening, recovery report, CLI, mission control. Does not rebuild install/upgrade/recovery; extends with a coherent deployment cut for the chosen vertical (founder_operator_prod).

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added **deploy-bundle** Typer: show, build --id, validate, upgrade-path, recovery-report. |
| `src/workflow_dataset/mission_control/state.py` | Added **deploy_bundle_state**: active_bundle_id, bundle_id, validation_passed, upgrade_readiness, rollback_readiness, recovery_posture_summary, blocked_deployment_risks. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Deploy bundle]** section: active_bundle, validation_passed, upgrade/rollback_readiness, blocked_risks. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/deploy_bundle/models.py` | ProductionDeploymentBundle, BundleContents, RequiredRuntimeProfile, RequiredPacksAssets, SupportedUpgradePath, SupportedRollbackPath, RecoveryPosture, DeploymentHealthSummary, ExcludedSurfaceMetadata. |
| `src/workflow_dataset/deploy_bundle/registry.py` | BUILTIN_DEPLOYMENT_BUNDLES (founder_operator_prod), get_deployment_bundle, list_deployment_bundle_ids. |
| `src/workflow_dataset/deploy_bundle/store.py` | data/local/deploy_bundle/active.json; get_active_bundle, set_active_bundle, get_deploy_bundle_dir. |
| `src/workflow_dataset/deploy_bundle/packaging.py` | build_bundle_manifest, write_bundle_manifest (manifest.json). |
| `src/workflow_dataset/deploy_bundle/validation.py` | validate_bundle → BundleValidationResult (install check, release readiness, curated pack). |
| `src/workflow_dataset/deploy_bundle/upgrade_rollback.py` | get_supported_upgrade_path, get_rollback_readiness, get_risky_upgrade_warnings; delegates to install_upgrade. |
| `src/workflow_dataset/deploy_bundle/recovery_report.py` | build_recovery_report (posture, recovery cases, vertical playbook ref, degraded startup). |
| `src/workflow_dataset/deploy_bundle/health.py` | build_deployment_health_summary for mission control. |
| `src/workflow_dataset/deploy_bundle/__init__.py` | Re-exports. |
| `tests/test_deploy_bundle.py` | test_bundle_model, test_bundle_validation, test_upgrade_path, test_rollback_readiness, test_recovery_report, test_invalid_bundle, test_build_manifest_and_active, test_deployment_health_summary. |
| `docs/samples/M40_deployment_bundle_sample.json` | Sample production deployment bundle (founder_operator_prod). |
| `docs/samples/M40_upgrade_path_sample.json` | Sample upgrade-path report. |
| `docs/samples/M40_recovery_rollback_readiness_sample.json` | Sample recovery report + rollback readiness + deployment health. |
| `docs/M40E_M40H_PRODUCTION_DEPLOYMENT_BEFORE_CODING.md` | Before-coding: assets, gaps, file plan, safety, principles, scope. |
| `docs/M40E_M40H_PRODUCTION_DEPLOYMENT_DELIVERABLE.md` | This deliverable. |

---

## 3. Exact CLI usage

```bash
# Show active or default deployment bundle
workflow-dataset deploy-bundle show
workflow-dataset deploy-bundle show --json

# Build manifest and set active bundle
workflow-dataset deploy-bundle build --id founder_operator_prod
workflow-dataset deploy-bundle build --id founder_operator_prod --no-set-active
workflow-dataset deploy-bundle build --id founder_operator_prod --json

# Validate bundle (install check, readiness, curated pack)
workflow-dataset deploy-bundle validate
workflow-dataset deploy-bundle validate --id founder_operator_prod --json

# Upgrade path (current/target version, can_proceed, warnings)
workflow-dataset deploy-bundle upgrade-path
workflow-dataset deploy-bundle upgrade-path --id founder_operator_prod --json

# Recovery posture and rollback readiness
workflow-dataset deploy-bundle recovery-report
workflow-dataset deploy-bundle recovery-report --id founder_operator_prod --json
```

---

## 4. Sample deployment bundle

See `docs/samples/M40_deployment_bundle_sample.json`. Summary:

- **bundle_id**: founder_operator_prod  
- **curated_pack_id**: founder_operator_core  
- **contents**: required_runtime (min_python 3.11, required_capabilities), required_packs (value_pack_id founder_ops_plus, workflow_ids, required_approvals_setup), allowed_trust_preset_ids, required_queue_day_workspace_refs, support_recovery_refs.  
- **supported_upgrade_path**: from_version_min 0.1.0, to_version_max 1.x, channel_ids stable/preview, reversible True.  
- **supported_rollback_path**: supported True, checkpoint_required_before_upgrade True.  
- **recovery_posture**: applicable_recovery_case_ids, vertical_playbook_id founder_operator_playbook, degraded_startup_guidance, recovery_doc_refs.  

---

## 5. Sample upgrade-path report

See `docs/samples/M40_upgrade_path_sample.json`. Keys: bundle_id, supported_upgrade_path, current_version, target_version, can_proceed, warnings, blocked_reasons. CLI: `workflow-dataset deploy-bundle upgrade-path --json`.

---

## 6. Sample recovery/rollback readiness output

See `docs/samples/M40_recovery_rollback_readiness_sample.json`. Contains recovery_report (recovery_posture, applicable_recovery_cases, vertical_playbook_recovery_ref, degraded_startup_guidance), rollback_readiness (supported_rollback_path, ready, latest_checkpoint_id, rollback_hints), deployment_health (validation_passed, upgrade_readiness, rollback_readiness, blocked_deployment_risks). CLI: `workflow-dataset deploy-bundle recovery-report --json`.

---

## 7. Exact tests run

```bash
cd /Users/prady/Desktop/Clap/workflow-llm-dataset
python3 -m pytest tests/test_deploy_bundle.py -v
```

**Result:** 8 passed (test_bundle_model, test_bundle_validation, test_upgrade_path, test_rollback_readiness, test_recovery_report, test_invalid_bundle, test_build_manifest_and_active, test_deployment_health_summary).

---

## 8. Exact remaining gaps for later refinement

- **Apply bundle**: build writes manifest and can set active_bundle_id; it does not apply workday/experience/trust or run first-run. A later “deploy-bundle apply” could apply vertical defaults and run install-check.
- **Risky upgrade in CLI**: get_risky_upgrade_warnings is implemented but not yet exposed as a dedicated CLI command (e.g. deploy-bundle risky-upgrade --target 0.3.0).
- **Excluded surface enforcement**: Excluded/quarantined surface metadata is in the model and contents; no enforcement (e.g. hiding surfaces in workspace) in this block.
- **Additional verticals**: Only founder_operator_prod is built-in; analyst_prod, developer_prod, document_worker_prod can be added by extending BUILTIN_DEPLOYMENT_BUNDLES.
- **Version pinning**: supported_upgrade_path uses generic 0.1.0–1.x; could be driven from pyproject or a version manifest for the cut.
- **Recovery-report link to vertical playbook**: Report includes vertical_playbook_recovery_ref; mission control could link “blocked deployment risks” to recovery-report and vertical-packs recovery when appropriate.
