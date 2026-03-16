# M23U — Pre-coding analysis (User Bootstrap + Domain Pack Builder + Specialization Recipes)

## 1. What onboarding/profile/building blocks already exist

- **Bootstrap profile (M23N Phase 1)** — `onboarding/bootstrap_profile.py`:
  - `BootstrapProfile`: machine_id, repo_root, created_at; adapter_ids, adapters_available; capabilities_summary; approval_registry_*; trusted_real_actions, ready_for_real; simulate_only_adapters/actions; recommended_job_packs, recommended_routines; edge_ready, edge_checks_*; setup_session_id, setup_stage.
  - `build_bootstrap_profile()`, `save_bootstrap_profile()`, `load_bootstrap_profile()`, `get_bootstrap_profile_path()`.
  - Persisted at `data/local/onboarding/bootstrap_profile.yaml`. Machine/capability/approval/edge focused; **no user work profile** (field, job family, task style, etc.).

- **Onboarding package** — `onboarding/__init__.py` currently imports `onboarding_flow`, `product_summary`, `approval_bootstrap`; **those modules do not exist** (only planned in M23N). Only `bootstrap_profile.py` exists.

- **Setup pipeline** — `setup/setup_models.py`: SetupStage (bootstrap → inventory → parsing → interpretation → graph_enrichment → llm_prep → summary). `DiscoveredDomain`: domain_id, label, confidence, evidence_count, signals. Used for artifact-based domain inference, not user-declared field/vertical.

- **Job packs** — `job_packs/`: JobPack (trust_level, required_adapters, simulate_support, real_mode_eligibility), SpecializationMemory (per-job preferred_params, preferred_paths, preferred_output_style, last_successful_run), load/save/update_from_successful_run/update_from_operator_override, check_job_policy, job_packs_report, list_job_packs, get_job_pack.

- **Capability packs (packs/)** — PackManifest: role_tags, industry_tags, workflow_tags, task_tags; supported_modes (baseline, adapter, retrieval, adapter_retrieval); required_models, recommended_models; recipe_steps, safety_policies. CLI: packs list/show/install/activate/resolve/validate. **No “domain pack” registry** (founder_ops, office_admin, etc.) as first-class verticals.

- **Copilot** — routines (Routine with job_pack_ids), plan (build_plan_for_job, build_plan_for_routine), recommend_jobs (recent_successful, trusted_for_real, etc.).

- **Context** — WorkState (job/review/intake/approvals/copilot summary), build_work_state, snapshots, triggers.

- **Intake** — registry (add_intake, list_intakes, get_intake), load_intake_content, intake_report.

- **LLM** — CorpusDocument, SFTExample, TrainingRunConfig; corpus_builder, sft_builder; configs/llm_training.yaml. No explicit “specialization recipe” types (retrieval-only, adapter fine-tune, embedding refresh, etc.).

- **Edge** — tiers (dev_full, local_standard, constrained_edge, minimal_eval), build_edge_profile, workflow availability per tier.

---

## 2. What specialization memory already exists

- **Per-job specialization** — `job_packs/specialization.py`: `SpecializationMemory` per job_pack_id: preferred_params, preferred_paths, preferred_apps, preferred_output_style, operator_notes, last_successful_run, recurring_failure_notes, confidence_notes, update_history. Stored under `data/local/job_packs/<job_pack_id>/specialization.yaml`. Updated only via explicit paths: update_from_successful_run, update_from_operator_override, save_as_preferred. Corrections layer can propose updates to specialization_params/paths/output_style.

- **No domain-level or user-level specialization memory** — No single “user work profile” or “domain pack preference” store that says “this user is in founder_ops” or “preferred automation level: high.”

---

## 3. What is missing for user-specific domain adaptation

- **User work profile (explicit, editable)** — Field/vertical, job family, daily task style, important apps/tools, document types, communication/reporting style, risk/safety posture, preferred degree of automation, hardware/runtime constraints. BootstrapProfile is machine/capability only.

- **Domain pack registry** — First-class “domain packs” (e.g. founder_ops, office_admin, logistics_ops, research_analyst, coding_development, document_knowledge_worker, multilingual, document_ocr_heavy) with: suggested job packs, routines, model classes, embeddings/OCR/vision classes, external integration classes, suggested training/specialization recipe, expected approvals/capabilities, trust notes.

- **Specialization recipe builder** — Explicit recipe kinds: local user data only; local + approved open datasets; local + approved public model class; retrieval-only; adapter fine-tune; embedding refresh; OCR/doc mode; coding-agent mode. Recipe **generation only** (no auto-download, no auto-training). Licensing/compliance metadata for dataset/model sources.

- **Dataset/model mapping policy** — user field → domain pack; domain pack → model classes / dataset classes / integration classes; machine profile → allowed practical options; safety posture → simulate-only vs benchmark-first vs trusted-real. Use external catalog (e.g. Ollama model/tool list) as **seed input**, filtered by policy.

- **CLI and operator summaries** — profile bootstrap/show; packs domain list/recommend; recipe build/explain; operator-facing summary (recommended domain pack, model/tool classes, specialization route, data usage, simulate-only scope, training/inference path).

---

## 4. Exact file plan

| Action | Path |
|--------|------|
| Fix | `src/workflow_dataset/onboarding/__init__.py` — export only existing symbols (bootstrap_profile); remove imports of non-existent onboarding_flow, product_summary, approval_bootstrap. |
| Create | `src/workflow_dataset/onboarding/user_work_profile.py` — UserWorkProfile dataclass (field, job_family, task_style, apps_tools, document_types, reporting_style, risk_posture, automation_preference, hardware_constraints, etc.); build (defaults + optional load), save, load; path under data/local/onboarding/user_work_profile.yaml. |
| Create | `src/workflow_dataset/domain_packs/__init__.py` — Public API for domain pack registry and recommendation. |
| Create | `src/workflow_dataset/domain_packs/models.py` — DomainPack dataclass (domain_id, name, suggested_job_packs, suggested_routines, suggested_model_classes, suggested_embedding_classes, suggested_ocr_vision_classes, suggested_integration_classes, suggested_recipe_id, expected_approvals, trust_notes). |
| Create | `src/workflow_dataset/domain_packs/registry.py` — Built-in domain pack definitions (founder_ops, office_admin, logistics_ops, research_analyst, coding_development, document_knowledge_worker, multilingual, document_ocr_heavy); list_domain_packs(), get_domain_pack(), recommend_domain_packs(field, job_family, ...). |
| Create | `src/workflow_dataset/domain_packs/policy.py` — Mapping: user field → domain pack(s); domain pack → model/dataset/integration class IDs; machine profile (edge tier) → allowed options; safety posture → simulate_only | benchmark_first | trusted_real. Filter external catalog (passed in) to allowed recommendations. |
| Create | `src/workflow_dataset/specialization/__init__.py` — Public API for recipe builder. |
| Create | `src/workflow_dataset/specialization/recipe_models.py` — SpecializationRecipe dataclass (recipe_id, name, mode: retrieval_only | adapter_finetune | embedding_refresh | ocr_doc | coding_agent | local_only | local_plus_approved_datasets | local_plus_approved_model); data_sources (local_only, approved_dataset_refs, approved_model_refs); licensing_compliance_metadata; no auto_download, no auto_train. |
| Create | `src/workflow_dataset/specialization/recipe_builder.py` — build_recipe_for_domain_pack(domain_pack_id, ...), explain_recipe(recipe_id); generate recipe spec only. |
| Create | `src/workflow_dataset/specialization/registry.py` — Built-in recipe definitions keyed by mode; list_recipes(), get_recipe(). |
| Create | `src/workflow_dataset/onboarding/operator_summary.py` — build_operator_summary(user_profile, bootstrap_profile, domain_packs, catalog_filter, machine_tier): recommended domain pack(s), recommended model/tool classes, recommended specialization route, data_used, simulate_only_scope, training_inference_path. |
| Modify | `src/workflow_dataset/cli.py` — Add profile_group: `profile bootstrap`, `profile show`. Add under packs or new group: `packs domain list`, `packs domain recommend --field X`. Add recipe_group: `recipe build --pack X`, `recipe explain --id X`. Add operator summary command (e.g. `profile operator-summary` or `workflow-dataset summary operator`). |
| Create | `tests/test_user_work_profile.py` — profile create, save, load, show. |
| Create | `tests/test_domain_packs.py` — domain list, get, recommend by field, policy filtering, refusal/unsupported. |
| Create | `tests/test_specialization_recipes.py` — recipe build, explain, licensing metadata, no auto-download/train. |
| Create | `tests/test_operator_summary.py` — summary generation, machine/resource filtering. |
| Create | `docs/M23U_USER_BOOTSTRAP_AND_DOMAIN_PACKS.md` — usage, sample user work profile, sample domain pack, sample recipe, sample recommendation output, safety, what this phase does not do. |

---

## 5. Safety/risk note

- **Explicit only** — User work profile and domain pack selection are explicit and editable; no silent inference of high-risk approvals or cloud behavior.
- **Recipe generation only** — Specialization recipe builder produces specs only; no auto-download of datasets, no auto-launch of training. Licensing/compliance fields are for operator review.
- **Catalog as input** — External model/tool catalog (e.g. Ollama) is an optional input to the policy layer; we filter and recommend. We do not fetch catalogs by default; caller provides or leaves empty.
- **Local-only** — All outputs under data/local/onboarding/, domain pack and recipe definitions in code or local config; no cloud, no telemetry.
- **Gates preserved** — check_job_policy and approval registry remain the execution gate; domain/recipe layer only recommends and configures.

---

## 6. What this phase will NOT do

- **No auto-training** — Will not invoke training backends or start training jobs.
- **No auto-download** — Will not download datasets or models; recipe may reference approved dataset/model IDs with licensing metadata for operator to resolve.
- **No auto-enable of external integrations** — Will not turn on Ollama or other runtimes; only recommend model classes that match policy.
- **No silent high-risk approvals** — Will not add or assume approval registry entries; operator must approve explicitly.
- **No cloud-default behavior** — All defaults remain local and simulate-first where applicable.
- **No replacement of Pane 1 contracts** — We depend on stable interfaces (e.g. runtime/backend registry) only; no reliance on concrete implementation details from another pane.
