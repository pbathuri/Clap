# M24R–M24U — Distribution / Installer / Update / Field Deployment — Pre-coding analysis

## 1. What install/deployment/update infrastructure already exists

- **local_deployment (M23R)** — `run_install_check` (edge checks + package readiness), `run_first_run` (dirs, install-check, onboarding bootstrap, first_run_summary), `build_local_deployment_profile` (edge profile, readiness, trust summary, product_surfaces), `write_deployment_profile` (JSON + optional report MD). CLI: `package local-deploy`, `package install-check`, `package first-run`.
- **package_readiness** — `build_readiness_summary` (current_machine_readiness, ready_for_first_real_user_install, not_ready_reasons, experimental). CLI: `package readiness-report`.
- **runtime_mesh** — Backend registry, model catalog, integrations, summary; used by edge and local deployment.
- **onboarding** — Bootstrap profile, onboarding flow, user work profile; used by first_run.
- **starter_kits** — BUILTIN_STARTER_KITS (founder_ops_starter, analyst_starter, developer_starter, document_worker_starter); kit_id, first_value_flow, recommended_job_ids, etc. CLI: kits list | recommend | show | first-run.
- **value_packs** — Golden bundles, pack recommend; CLI value-packs golden-bundle (optional if package present).
- **rollout** — Demos (required_pack = starter_kit_id), support bundle, readiness, runbooks. CLI: rollout demos list | launch | status | support-bundle | readiness | runbooks | issues report.
- **acceptance** — Scenarios per pack/scenario; used by rollout launch.
- **trust** — Trust cockpit; used by deployment profile and readiness.
- **edge** — Profile, readiness checks, tier; used by install_check and deployment profile.

**Gaps:** No dedicated “install bundle” or “field deployment profile” model; no pack-aware install profile; no update planner (current vs desired, what would change, staging); no field deployment checklists per pack; no single `deploy` CLI group for bundle / install-profile / update-plan / checklist / readiness.

---

## 2. What is missing for a coherent distribution layer

- **Install bundle model** — Definition of an installable local product bundle (contents, version, required capabilities, machine assumptions). Today deployment profile is a snapshot, not a declared “bundle” artifact.
- **Field deployment profile / pack-aware install profile** — Profile that names a target pack (e.g. founder_ops_starter) and lists required capabilities, approvals/setup, runtime prerequisites, and machine assumptions. Today profile is machine-centric, not pack-centric.
- **Update planner** — Compare current install state (from deployment profile or current readiness) vs desired state (e.g. from a bundle or profile); list what would change, risks; stage an update plan; support reversible/local-safe where possible. Not present.
- **Field deployment checklists** — Per-role (founder/operator, analyst, developer, document worker) checklists: runtime prerequisites, pack provisioning prerequisites, trust/readiness checks, first-value run after install. Rollout runbooks are generic; no pack-specific deployment checklist generator.
- **Deploy CLI** — Single entry: `deploy bundle`, `deploy install-profile`, `deploy update-plan`, `deploy checklist --pack <id>`, `deploy readiness`. Today deploy-related commands live under package/ and local-deploy.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/distribution/__init__.py` — Public API. |
| Create | `src/workflow_dataset/distribution/models.py` — InstallBundle, FieldDeploymentProfile, PackAwareInstallProfile (pack_id, required_capabilities, required_approvals_setup, machine_assumptions). |
| Create | `src/workflow_dataset/distribution/bundle.py` — build_install_bundle(repo_root): produce bundle definition from current profile + version; optional write to data/local/distribution/bundles/. |
| Create | `src/workflow_dataset/distribution/install_profile.py` — build_pack_aware_install_profile(pack_id, repo_root), build_field_deployment_profile(pack_id, repo_root): combine pack deps, runtime prereqs, trust/readiness, machine assumptions. |
| Create | `src/workflow_dataset/distribution/update_planner.py` — build_update_plan(current_state, desired_state or bundle), format_update_plan(): what would change, risks, staged steps; no execution. |
| Create | `src/workflow_dataset/distribution/checklists.py` — build_field_checklist(pack_id, repo_root): runtime prereqs, pack provisioning prereqs, trust/readiness checks, first-value run; output for founder_ops_starter, analyst_starter, developer_starter, document_worker_starter. |
| Create | `src/workflow_dataset/distribution/readiness.py` — format_deploy_readiness(repo_root): aggregate install check + package readiness + rollout readiness one-liner for deploy. |
| Modify | `src/workflow_dataset/cli.py` — Add deploy_group: deploy bundle, deploy install-profile [--pack], deploy update-plan [--desired], deploy checklist --pack, deploy readiness. |
| Create | `tests/test_distribution.py` — Bundle/profile generation, update plan structure, checklist generation, readiness format, partial/blocked behavior. |
| Create | `docs/M24R_M24U_DISTRIBUTION.md` — Usage, sample install profile, update plan, checklist, readiness, gaps. |

---

## 4. Safety/risk note

- **Local-only** — All artifacts under data/local/distribution/ or repo; no cloud, no auto-update.
- **No auto-execution** — Update planner stages a plan only; it does not run migrations or install steps. Checklist and install-profile are descriptive.
- **Reuse only** — Uses existing install_check, package_readiness, local_deployment profile, rollout, starter_kits; no rewrite of those systems.
- **Operator-controlled** — Bundle generation and update plan are explicit; operator runs deploy commands.

---

## 5. What this block will NOT do

- No cloud SaaS deployment or remote telemetry.
- No hidden auto-update service or background updater.
- No automatic migration execution; update plan is advisory/staged only.
- No full package-manager rewrite; first-draft distribution discipline only.
- No polish; remaining gaps documented for later refinement.
