# M40H.1 — Deployment Profiles + Production Maintenance Modes (Deliverable)

First-draft support for deployment profiles (demo, internal production-like, careful production cut), maintenance modes (upgrade, recovery, audit review, safe pause), and clearer operator guidance for when to pause or repair. Extends M40E–M40H; does not rebuild the production deployment bundle layer.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/deploy_bundle/models.py` | Added DeploymentProfile, MaintenanceMode, MaintenanceModeReport; PROFILE_* and MODE_* constants. |
| `src/workflow_dataset/deploy_bundle/store.py` | get_active_bundle now returns deployment_profile_id, maintenance_mode_id; added set_deployment_profile, set_maintenance_mode. set_active_bundle preserves profile and mode. |
| `src/workflow_dataset/deploy_bundle/__init__.py` | Exported profiles, maintenance_modes, store helpers, new models. |
| `src/workflow_dataset/cli.py` | Added deploy-bundle profiles, deploy-bundle profile --id [--set], deploy-bundle maintenance-mode [--set mode] (report + optional set). |
| `tests/test_deploy_bundle.py` | Added test_deployment_profile, test_maintenance_mode, test_maintenance_mode_report. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/deploy_bundle/profiles.py` | BUILTIN_DEPLOYMENT_PROFILES (demo, internal_production_like, careful_production_cut), get_deployment_profile, list_deployment_profile_ids. |
| `src/workflow_dataset/deploy_bundle/maintenance_modes.py` | BUILTIN_MAINTENANCE_MODES (upgrade, recovery, audit_review, safe_pause), get_maintenance_mode, list_maintenance_mode_ids, build_maintenance_mode_report. |
| `docs/samples/M40H1_deployment_profile_sample.json` | Sample deployment profile (careful_production_cut). |
| `docs/samples/M40H1_maintenance_mode_report_sample.json` | Sample maintenance mode report (active profile, mode, should_pause, should_repair, operator guidance). |
| `docs/M40H1_DEPLOYMENT_PROFILES_MAINTENANCE_MODES_DELIVERABLE.md` | This deliverable. |

---

## 3. Sample deployment profile

See `docs/samples/M40H1_deployment_profile_sample.json`. Summary for **careful_production_cut**:

- **profile_id**: careful_production_cut  
- **name**: Careful production cut  
- **description**: Frozen scope, validated bundle, upgrade/rollback readiness required.  
- **profile_type**: careful_production_cut  
- **recommended_bundle_ids**: ["founder_operator_prod"]  
- **allow_operator_mode**, **allow_real_run_with_approval**: true  
- **pause_guidance**: When to pause (e.g. when validate fails, upgrade in progress, rollback lost).  
- **repair_guidance**: Run validate and recovery-report; fix errors; ensure checkpoint; resume when validation_passed and upgrade_readiness.  

CLI: `workflow-dataset deploy-bundle profile --id careful_production_cut` (optionally `--set` to set active, `--json` for full JSON).

---

## 4. Sample maintenance-mode report

See `docs/samples/M40H1_maintenance_mode_report_sample.json`. Summary:

- **active_profile_id**: default careful_production_cut if not set  
- **active_maintenance_mode_id**: current mode or empty  
- **should_pause**, **should_repair**: derived from mode and deployment health  
- **pause_reason**, **repair_reason**: operator guidance text  
- **operator_guidance_summary**: when to pause or repair  
- **recommended_actions**: list of CLI commands  
- **profile**, **maintenance_mode**: full profile and mode dicts  

CLI: `workflow-dataset deploy-bundle maintenance-mode` (report) or `workflow-dataset deploy-bundle maintenance-mode --set safe_pause` (set mode and show report), `--json` for full output.

---

## 5. Exact tests run

```bash
cd /Users/prady/Desktop/Clap/workflow-llm-dataset
python3 -m pytest tests/test_deploy_bundle.py -v
```

**Result:** 11 passed (existing 8 + test_deployment_profile, test_maintenance_mode, test_maintenance_mode_report).

---

## 6. Next recommended step for the pane

- **Mission control**: Add a short **[Deploy profile / Maintenance]** line to the mission control report: active_profile_id, active_maintenance_mode_id, and when should_pause or should_repair is true, show a one-line operator guidance (e.g. “Pause: …” or “Repair: …”) and a link to `workflow-dataset deploy-bundle maintenance-mode`.
- **Enforcement**: Optionally gate real runs or operator mode in executor/operator when active_maintenance_mode blocks_real_run or blocks_operator_mode (read from store and check before run). This would be a small extension in the executor or operator_mode layer that consults deploy_bundle store.
- **Profile–bundle link**: When setting active bundle, optionally suggest or set a default deployment profile (e.g. careful_production_cut for founder_operator_prod) and document the pairing in the profile’s recommended_bundle_ids.
