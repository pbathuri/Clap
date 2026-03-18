# M30A–M30D — Install Bundle + Upgrade / Migration Manager

## Overview

First-draft local-first install/upgrade layer: versioned install bundles, current-version tracking, upgrade planning and apply, migration report, rollback from checkpoints. Operator-controlled; no hidden auto-updates.

## CLI usage

| Command | Description |
|--------|-------------|
| `workflow-dataset release install-bundle` [ `--bundle-id <id>` ] | Build and write install bundle to data/local/distribution/bundles. Version from pyproject. |
| `workflow-dataset release current-version` [ `--json` ] | Show current installed version (data/local/install or pyproject). |
| `workflow-dataset release upgrade-plan` [ `--target <ver>` ] [ `--bundle-id <id>` ] | Show upgrade plan (current → target, migration steps, blocked). No execution. |
| `workflow-dataset release upgrade-apply` [ `--target <ver>` ] | Apply upgrade: create checkpoint, run migrations, write current version. |
| `workflow-dataset release rollback` [ `--checkpoint <id>` ] | Roll back to checkpoint (default: latest). |
| `workflow-dataset release migration-report` [ `--json` ] | Migration/upgrade status: current version, upgrade available, checkpoints, blocked. |

## Sample install bundle

Written to `data/local/distribution/bundles/<bundle_id>.json`:

```json
{
  "bundle_id": "local_bundle",
  "version": "0.1.0",
  "description": "Local installable product bundle (first-draft).",
  "repo_root": "/path/to/repo",
  "generated_at": "2025-01-15T12:00:00Z",
  "required_capabilities": ["config_exists", "edge_checks", "approval_registry_optional"],
  "machine_assumptions": {"local_only": true, "python_required": true},
  "edge_profile_summary": {},
  "readiness_summary": {},
  "product_surfaces_summary": {}
}
```

## Sample upgrade plan

```
=== Upgrade plan ===

Current version: 0.1.0
Target version:  0.2.0
Target bundle:   bundle_0_2_0
Generated:       2025-01-15T12:00:00Z

[Migration steps]
  - ensure_install_dir: Ensure data/local/install exists.  (reversible=True)
  - write_current_version: Write current_version.json with target version.  (reversible=True)

[Impact preview]
  - Current version file will be updated.

Can proceed: True  Reversible overall: True
(Operator-controlled. Run 'workflow-dataset release upgrade-apply' to apply.)
```

## Sample migration report

```
=== Migration / upgrade report ===

Current version:     0.1.0  (source: install)
Package (pyproject): 0.2.0
Target version:      0.2.0
Upgrade available:   True
Migration steps:     2
Rollback checkpoints: 0

(Operator-controlled. Use release upgrade-plan and release upgrade-apply to upgrade.)
```

## Sample rollback output

After `workflow-dataset release upgrade-apply` then `workflow-dataset release rollback`:

```
Rolled back to version 0.1.0
```

Or with `--checkpoint ck_xxxx`:

```
Restored version file from backup (from_version=0.1.0)
```

## Files modified / created

| Action | Path |
|--------|------|
| New | `src/workflow_dataset/install_upgrade/__init__.py` |
| New | `src/workflow_dataset/install_upgrade/models.py` |
| New | `src/workflow_dataset/install_upgrade/version.py` |
| New | `src/workflow_dataset/install_upgrade/upgrade_plan.py` |
| New | `src/workflow_dataset/install_upgrade/apply_upgrade.py` |
| New | `src/workflow_dataset/install_upgrade/reports.py` |
| New | `src/workflow_dataset/install_upgrade/cli.py` |
| Edit | `src/workflow_dataset/cli.py` — release install-bundle, current-version, upgrade-plan, upgrade-apply, rollback, migration-report |
| Edit | `src/workflow_dataset/mission_control/state.py` — install_upgrade block |
| Edit | `src/workflow_dataset/mission_control/report.py` — [Install / upgrade] section |
| New | `tests/test_install_upgrade_m30.py` |
| New | `docs/M30_BEFORE_CODING.md` |
| New | `docs/M30_INSTALL_UPGRADE.md` |

## Tests run

```bash
pytest tests/test_install_upgrade_m30.py -v
```

- ProductVersion / RollbackCheckpoint roundtrip  
- read_current_version (empty), get_package_version_from_pyproject, write_current_version  
- build_upgrade_plan (same version blocked, upgrade path with steps)  
- apply_upgrade + perform_rollback  
- build_migration_report, format_migration_report  
- cmd_install_bundle, cmd_current_version, cmd_upgrade_plan  

## Remaining gaps for later refinement

- **Richer migration steps**: Today only ensure_install_dir and write_current_version; add schema/data migrations (e.g. workspace, pack registry) as needed.
- **Downgrade**: Blocked in first-draft; support downgrade with explicit migration steps and compatibility checks.
- **Bundle versioning**: Convention for versioned bundle ids (e.g. bundle_0_2_0) and loading a bundle by version for upgrade.
- **Env requirements**: EnvRequirements / InstallProfile are modeled but not yet enforced during upgrade.
- **Pack/runtime snapshot**: PackRuntimeSnapshot and backup of pack state before upgrade for full rollback.
- **Mission control next-action**: Optionally recommend "release upgrade-apply" when upgrade_available and no blockers.
