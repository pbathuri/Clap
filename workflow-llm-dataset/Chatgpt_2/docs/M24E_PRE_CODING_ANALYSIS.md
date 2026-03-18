# M24E — Specialization Recipe Runner + Domain Provisioning — Pre-coding analysis

## 1. What profile/domain/recipe layers already exist

### Profile
- **User work profile:** `onboarding/user_work_profile` — load/save; field, job_family, daily_task_style, risk_safety_posture, preferred_automation_degree, preferred_edge_tier.
- **Operator summary:** `onboarding/operator_summary` — `build_operator_summary()` uses profile + domain pack recommendation; recommended_domain_packs, model/embedding/OCR classes, recommended_specialization_route, data_usage, simulate_only_scope, training_inference_path, machine_tier.

### Domain
- **Domain packs:** `domain_packs/` — `DomainPack` (domain_id, suggested_job_packs, suggested_routines, suggested_model/embedding/OCR/integration_classes, suggested_recipe_id, expected_approvals, trust_notes, field_keywords, job_family_keywords). `list_domain_packs()`, `get_domain_pack()`, `recommend_domain_packs(field, job_family, daily_task_style)`.
- **Value packs:** `value_packs/` — `ValuePack` with starter_kit_id, domain_pack_id, recommended_*, first_value_sequence, sample_asset_paths. `list_value_packs()`, `get_value_pack()`, `recommend_value_pack()`, `build_first_run_flow()`, `compare_value_packs()`, `get_sample_asset_path()`.
- **Starter kits:** `starter_kits/` — `StarterKit` (kit_id, domain_pack_id, recommended_job_ids, recommended_routine_ids, first_value_flow). `recommend_kit_from_profile()`, list/show/first-run.

### Recipe (specialization)
- **Recipe model:** `specialization/recipe_models.py` — `SpecializationRecipe` (recipe_id, name, description, mode, data_sources, licensing_compliance_metadata, auto_download=False, auto_train=False, steps_summary). Modes: local_user_data_only, retrieval_only, adapter_finetune, embedding_refresh, ocr_doc, coding_agent, etc.
- **Recipe registry:** `specialization/registry.py` — `BUILTIN_RECIPES`, `list_recipes()`, `get_recipe()`.
- **Recipe builder:** `specialization/recipe_builder.py` — `build_recipe_for_domain_pack(domain_pack_id)`, `explain_recipe(recipe_id)`. Generation only; no side effects.
- **CLI:** `workflow-dataset recipe build --pack founder_ops`, `workflow-dataset recipe explain <id>`. No `recipe runs list`, `recipe run`, `recipe preview`, `recipe report`.

### Runtime / external / intake / job packs / acceptance
- **Runtime mesh:** `runtime_mesh/` — backends, task_class policy, `build_runtime_summary()`, `recommend_for_task_class()`.
- **External capability:** `external_capability/` — registry, activation (no auto-enable).
- **Intake:** `intake/` — registry, snapshot from local paths; no arbitrary execution.
- **Job packs:** `job_packs/` — execute (preview_job, run_job), specialization memory, policy checks.
- **Packs (install):** `packs/` — `install_pack(manifest_path)`, `apply_recipe_steps()` (declarative only: create_config, register_templates, register_prompts, etc.); no run_shell/execute_script.
- **Acceptance:** `acceptance/` — runner, storage, journeys.
- **Mission control:** `mission_control/state.py` — aggregate product/eval/dev/incubator state; `report.py` + `next_action`. No explicit “provisioned packs” or “failed provisioning runs” yet.

---

## 2. What is missing for actual provisioning

- **Recipe run model:** No persisted “recipe run” (run id, source recipe, target domain/value pack, machine assumptions, approvals required, steps, outputs, reversible, status). Recipes are metadata only; nothing records “this recipe was run at T for pack X”.
- **Provisioning runner:** No single flow that (a) checks prerequisites (jobs, routines, approval registry, sample assets), (b) prepares local sample/demo assets, (c) provisions local pack files/manifests (e.g. value-pack-specific configs under data/local), (d) stages specialization inputs (e.g. corpus dirs, intake refs), (e) writes a provisioning summary and optional rollback notes. Pack installer is manifest-based; there is no “provision value pack X” that creates dirs/configs and sample assets for a vertical.
- **Domain environment summary:** No “what is now provisioned for this domain,” “what jobs/routines/macros are ready,” “what still needs activation,” “what remains simulate-only,” “what the first-value run should be now.” Value pack first-run flow is static steps; no post-provision “readiness” view.
- **Recipe execution surface:** No `recipe run --id <recipe_id>` or `recipe run --id founder_ops_recipe` that performs safe local provisioning steps (prepare samples, write manifests/configs, register refs) and records the run. No `recipe runs list` or `recipe report --latest`.
- **Pack provisioning CLI:** No `packs provision --id founder_ops_plus` that runs the value-pack provisioning flow (sample assets, local config, first-value readiness).
- **Mission control / onboarding hooks:** Mission control does not yet expose “provisioned packs,” “failed provisioning runs,” “recommended next first-value flow,” or “missing prerequisites” in one place.

---

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|---------|
| **Create** | `src/workflow_dataset/specialization/recipe_run_models.py` | Recipe run model: run_id, source_recipe_id, target_domain_pack_id, target_value_pack_id, target_starter_kit_id, machine_assumptions, approvals_required, steps_done, outputs_expected, reversible, status, started_at, finished_at, rollback_notes. |
| **Create** | `src/workflow_dataset/specialization/recipe_runs_storage.py` | Persist recipe runs under `data/local/specialization/recipe_runs/` (e.g. JSON per run); list_runs(), get_run(run_id), save_run(run). |
| **Create** | `src/workflow_dataset/provisioning/runner.py` | Provisioning runner: check_prerequisites(value_pack_id or domain_pack_id, repo_root) → missing list; run_provisioning(value_pack_id, repo_root, dry_run=False) → prepare sample assets, write pack manifest/config under data/local/provisioning/<pack_id>/, stage specialization inputs (stub dirs if needed), write summary; refuse if prerequisites missing (configurable strict). |
| **Create** | `src/workflow_dataset/provisioning/domain_environment.py` | domain_environment_summary(pack_id, repo_root): what is provisioned, jobs/routines/macros ready, what needs activation, simulate-only set, recommended_first_value_run. |
| **Create** | `src/workflow_dataset/provisioning/report.py` | Format provisioning summary, domain environment summary, recipe run report for CLI. |
| **Create** | `src/workflow_dataset/provisioning/__init__.py` | Re-export runner, domain_environment, report. |
| **Modify** | `src/workflow_dataset/specialization/__init__.py` | Export recipe run model and runs storage (or keep runs in provisioning if preferred; here we keep run model in specialization, runner in provisioning). |
| **Modify** | `src/workflow_dataset/cli.py` | Add: `recipe runs list`, `recipe run --id <recipe_id>` (with optional --pack for domain/value pack), `recipe preview --id <recipe_id>`, `recipe report --latest`. Add: `packs provision --id <value_pack_id>` (and optionally --dry-run). Use existing recipe_group and add to existing packs_group or new provision group. |
| **Modify** | `src/workflow_dataset/mission_control/state.py` | Add provisioning state: provisioned_packs (from data/local/provisioning or recipe_runs), failed_provisioning_runs, recommended_next_first_value_flow (from value pack + domain_environment), missing_prerequisites (from runner check). |
| **Modify** | `src/workflow_dataset/mission_control/report.py` | Add section for provisioned packs, failed runs, next first-value, missing prereqs. |
| **Create** | `docs/M24E_PROVISIONING.md` | Operator doc: recipe run model, how to run recipe, preview, report; packs provision; domain environment summary; mission control visibility; safety (no auto-download, no auto-train, approval-aware). |
| **Create** | `tests/test_recipe_runs.py` | Tests: recipe run model save/load, list runs, get latest. |
| **Create** | `tests/test_provisioning.py` | Tests: prerequisite check (blocked when missing), provisioning run (dry_run), domain environment summary, first-value readiness; sample asset creation when safe. |

Optional: map “founder_ops_recipe” style IDs to existing recipe IDs (e.g. founder_ops → retrieval_only) so `recipe run --id founder_ops_recipe` resolves to domain pack founder_ops + recipe retrieval_only.

---

## 4. Safety/risk note

- **No auto-download / no auto-train:** Provisioning only prepares local paths, copies or creates local sample assets, and writes config/manifest files. It does not download models or datasets or start training. Recipe run records “what was done” for audit.
- **Explicit and inspectable:** All writes under `data/local/` (e.g. `data/local/provisioning/<pack_id>/`, `data/local/specialization/recipe_runs/`). Operator can inspect and delete.
- **Approval-aware:** Runner checks existing approval registry and job/routine presence; can refuse to mark “real” readiness if approvals missing; does not bypass trust boundaries.
- **Reversible:** Rollback notes in recipe run; uninstall/removal is directory removal and state file updates only; no hidden state elsewhere.
- **Risk:** If provisioning creates symlinks or references to user paths, ensure we do not expose sensitive paths in reports. Prefer creating only under repo data/local.

---

## 5. What this phase will NOT do

- **Will not:** Auto-download large models or datasets; auto-train or auto fine-tune; run arbitrary shell scripts or non-declarative steps; enable cloud-managed specialization; broaden to dozens of verticals; weaken approval or trust boundaries; rebuild or replace domain_packs, starter_kits, value_packs, or specialization recipe definitions.
- **Will:** Add recipe run persistence, a local provisioning runner for value/domain packs, domain environment summaries, CLI (recipe runs list, recipe run, recipe preview, recipe report; packs provision), and mission control visibility for provisioning and next first-value.
