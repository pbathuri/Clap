# M30 Before-Coding: Install Bundle + Upgrade / Migration Manager

## 1. What install/deployment/update behavior already exists

- **local_deployment**: `build_local_deployment_profile` (version "1", edge_profile, readiness, trust_summary, product_surfaces); `run_install_check` (edge + package readiness); `run_first_run` (ensure dirs, install-check, onboarding). `get_deployment_dir` = `data/local/deployment`; profile written as JSON. No product version field; no upgrade path.
- **distribution**: `InstallBundle` (bundle_id, version "1", description, required_capabilities, machine_assumptions, edge_profile_summary, readiness_summary, product_surfaces_summary); `build_install_bundle` from current profile; `write_install_bundle` to `data/local/distribution/bundles/<bundle_id>.json`. `UpdatePlan` (plan_id, current_state_summary, desired_state_summary, steps, risks, reversible_overall); `build_update_plan` compares current vs desired profile (readiness diff); no version-to-version upgrade. `PackAwareInstallProfile` / `FieldDeploymentProfile` for pack-specific install. `build_deploy_readiness`, `build_handoff_pack`, checklists.
- **apply/rollback_store**: `RollbackRecord` (rollback_token, apply_id, backups, affected_paths); `perform_rollback(rollback_token, store_path)` restores files from backup; used by assist rollback for apply manifests. Not tied to product version or install upgrade.
- **rollout**: `load_rollout_state` / `save_rollout_state` in `data/local/rollout/rollout_state.json`; target scenario, stage, checks. No version or migration.
- **release (cli)**: `release_group` has verify, run, demo, package, report, readiness, pack, supportability, triage, handoff-pack, workspace commands. No `install-bundle`, `current-version`, `upgrade-plan`, `upgrade-apply`, `rollback` (that rollback is assist rollback for apply), or `migration-report`.
- **pyproject.toml**: `version = "0.1.0"` — single source for package version; not yet used as "installed product version" on disk.
- **mission_control**: state aggregates product_state, evaluation_state, development_state, incubator_state, daily_inbox, review_studio, etc. No "installed_version" or "pending_upgrade" or "migration_warnings" block.

## 2. What is missing for a real versioned install/upgrade system

- **Product version on disk**: No persisted "current installed version" (e.g. `data/local/install/current_version.json` or similar) that survives runs; version is only in pyproject.toml at dev time.
- **Install bundle as versioned artifact**: Bundles are built ad hoc with version "1"; no convention for versioned bundle ids (e.g. `bundle_0.1.0`) or minimum schema version for migrations.
- **Upgrade plan from A → B**: No "current version" vs "target version" upgrade plan; UpdatePlan is current vs desired state (readiness), not version-to-version migration steps.
- **Migration steps and requirements**: No explicit migration step list (e.g. "migrate workspace schema", "backup pack registry"); no incompatible-state or blocked-upgrade reasons tied to versions.
- **Apply upgrade / rollback for install**: No "upgrade-apply" that runs migrations and records a rollback checkpoint; apply rollback is for file apply only, not for install/upgrade.
- **CLI**: No `release install-bundle`, `release current-version`, `release upgrade-plan`, `release upgrade-apply`, `release rollback` (for upgrade), `release migration-report`.
- **Mission control visibility**: No block showing installed version, pending upgrade plan, migration warnings, rollback availability, or blocked upgrade conditions.

## 3. Exact file plan

| Action | Path |
|--------|------|
| New | `src/workflow_dataset/install_upgrade/__init__.py` |
| New | `src/workflow_dataset/install_upgrade/models.py` — Phase A: InstallBundle (extend/alias), ProductVersion, InstallProfile, EnvRequirements, EnabledModulesSnapshot, PackRuntimeSnapshot, MigrationRequirement, RollbackCheckpoint |
| New | `src/workflow_dataset/install_upgrade/version.py` — read/write current version from data/local/install; read version from pyproject / bundle |
| New | `src/workflow_dataset/install_upgrade/upgrade_plan.py` — Phase B: current version detection, target selection, upgrade impact preview, migration step list, incompatible/blocked reasons |
| New | `src/workflow_dataset/install_upgrade/apply_upgrade.py` — Phase C: stage upgrade, apply migrations (stub/placeholder steps), preserve state, record failures, rollback checkpoint and revert |
| New | `src/workflow_dataset/install_upgrade/reports.py` — migration report formatting |
| New | `src/workflow_dataset/install_upgrade/cli.py` — Phase D: cmd_install_bundle, cmd_current_version, cmd_upgrade_plan, cmd_upgrade_apply, cmd_rollback, cmd_migration_report |
| Edit | `src/workflow_dataset/cli.py` — add release subcommands: install-bundle, current-version, upgrade-plan, upgrade-apply, rollback, migration-report (wire to install_upgrade.cli) |
| Edit | `src/workflow_dataset/mission_control/state.py` — Phase E: additive block install_upgrade (current_version, pending_upgrade_plan, migration_warnings, rollback_available, blocked_reasons) |
| Edit | `src/workflow_dataset/mission_control/report.py` — Phase E: print install_upgrade block when present |
| New | `tests/test_install_upgrade_m30.py` — Phase F |
| New | `docs/M30_INSTALL_UPGRADE.md` — Phase F |

## 4. Safety/risk note

- **No hidden auto-update**: All upgrade and rollback actions are explicit CLI (or future UI). No background process or auto-apply.
- **Reversibility**: Rollback checkpoint created before apply; revert restores from checkpoint where possible. Apply-upgrade will only run migrations that are marked reversible or have explicit rollback steps.
- **Risk**: First-draft migrations may be no-ops or stubs; real migrations (e.g. schema changes) require careful design later. Mitigation: migration steps are listed and confirmed; operator runs upgrade-apply explicitly.
- **Trust/acceptance**: No change to approval or trust boundaries; install/upgrade does not auto-approve or bypass policy.

## 5. What this block will NOT do

- Replace or redesign distribution/local_deployment; integrate additively (read current profile/bundle, write version and checkpoints under data/local/install).
- Add cloud release or package-manager (pip/npm) replacement.
- Auto-apply upgrades or run migrations without explicit operator command.
- Implement full migration logic for every subsystem (first-draft: stub steps and one or two concrete migrations, e.g. "ensure install dir", "write current version").
- Change apply/rollback_store behavior for apply manifests; upgrade rollback is separate (install_upgrade rollback checkpoint).
