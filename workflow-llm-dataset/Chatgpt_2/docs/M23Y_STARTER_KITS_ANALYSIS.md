# M23Y — Field Starter Kits + Immediate-Value Packs (pre-coding)

## 1. What existing domain-pack and job-pack infrastructure already supports

### Domain packs (M23U)
- **Registry** (`domain_packs/registry.py`): `BUILTIN_DOMAIN_PACKS` — founder_ops, office_admin, logistics_ops, research_analyst, coding_development, document_knowledge_worker, multilingual, document_ocr_heavy. Each has: `domain_id`, `name`, `description`, `suggested_job_packs`, `suggested_routines`, `suggested_model_classes`, `suggested_embedding_classes`, `suggested_ocr_vision_classes`, `suggested_integration_classes`, `suggested_recipe_id`, `expected_approvals`, `trust_notes`, `field_keywords`, `job_family_keywords`.
- **Recommendation**: `recommend_domain_packs(field, job_family, daily_task_style)` → list of `(DomainPack, score)`; `resolve_domain_pack_for_field(...)` → primary pack or None.
- **Policy**: `get_allowed_options_for_machine(repo_root, tier, domain_pack)` → allowed model/embedding/OCR/integration classes; `get_safety_posture_from_profile(risk_safety_posture, preferred_automation_degree)` → simulate_only | benchmark_first | trusted_real.

### Specialization
- **Recipes** (`specialization/registry.py`): retrieval_only, adapter_finetune, embedding_refresh, ocr_doc, coding_agent, local_user_data_only, etc. Each recipe has `recipe_id`, `mode`, `data_sources`, `steps_summary`, `auto_download=False`, `auto_train=False`.
- **Recipe builder**: `build_recipe_for_domain_pack(domain_pack)`, `explain_recipe(recipe)`.

### Job packs (M23J)
- **Schema**: JobPack with job_pack_id, title, description, required_adapters, simulate_support, real_mode_eligibility, trust_level, etc. Jobs loaded from `data/local/job_packs/*.yaml`.
- **Seed**: `seed_example_job_pack()` creates `weekly_status_from_notes`; `seed_task_demo_job_pack()` creates `replay_cli_demo`. Domain packs reference names like `weekly_status`, `status_action_bundle`, `meeting_brief_bundle` — these are **suggested** IDs; actual job files may not exist until seeded or user-created.
- **Report**: `job_packs_report()`, `list_job_packs()`, `get_job_pack()`, `check_job_policy()`.

### Copilot / routines / macros (M23K, M23V)
- **Routines**: YAML under `data/local/copilot/routines/`; `list_routines()`, `get_routine()`, `get_ordered_job_ids()`.
- **Macros**: 1:1 with routines; `list_macros()`, `macro_preview(id)`, `macro_run(id, mode)`.

### Runtime mesh (M23T)
- **Policy**: `recommend_for_task_class(task_class, repo_root)` → backend_id, model_class, model_ids, missing, reason. Task classes: desktop_copilot, inbox, codebase_task, coding_agent, local_retrieval, document_workflow, vision, plan_run_review, lightweight_edge.

### Onboarding / profile
- **UserWorkProfile**: field, job_family, daily_task_style, risk_safety_posture, preferred_automation_degree, etc. Persisted at `data/local/onboarding/user_work_profile.yaml`.
- **BootstrapProfile**: machine_id, adapters, approvals, trusted_real_actions, recommended_job_packs, edge_ready.
- **Operator summary**: `build_operator_summary(user_profile, bootstrap_profile, catalog_entries, repo_root)` → recommended_domain_packs, recommended_model_classes, recommended_specialization_route, safety_posture, etc.

### Inbox / trust / package readiness (M23V)
- **Inbox**: `build_daily_digest()`; relevant jobs/routines, blocked, reminders, recommended next action.
- **Trust cockpit**: benchmark trust, approval readiness, job/macro trust state, release gates.
- **Package readiness**: machine readiness, product readiness, ready_for_first_real_user_install, experimental.

---

## 2. What is missing for immediate end-user value

- **Single “starter kit” concept**: No one bundle that says “for founder/operator: use this domain pack, these jobs/routines, this runtime recommendation, this first workflow.” Domain packs suggest job/routine IDs and recipe; they do not define a first-value flow or “run this first, get this back.”
- **Profile → kit recommendation**: We have profile → domain_pack (via recommend_domain_packs). We do not have profile → **starter kit** with alternatives and “why chosen.”
- **First-value flow**: No explicit “first run” flow: what to run first, what the user gets back, why it’s useful, what to do next. Operator summary and inbox are generic.
- **Missing-prerequisite reporting per kit**: We have package_readiness and trust cockpit globally; we do not have “for this kit, you need: approval registry, job X seeded, routine Y; missing: ….”
- **Kit registry**: No registry of named starter kits (founder_ops_starter, analyst_starter, developer_starter, document_worker_starter) that tie domain_pack + jobs + routines + runtime + first-value flow + trust/readiness notes.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/starter_kits/__init__.py` |
| Create | `src/workflow_dataset/starter_kits/models.py` — `StarterKit` dataclass: kit_id, name, target_field, target_job_family, domain_pack_id, recommended_profile_defaults (dict), recommended_runtime_task_class, recommended_model_class, recommended_domain_pack_ids (list), recommended_job_ids, recommended_routine_ids, first_simulate_only_workflow (workflow_id or routine_id), trusted_real_eligibility_notes, expected_outputs, approvals_likely_needed, first_value_flow (see below). |
| Create | `src/workflow_dataset/starter_kits/first_value_flow.py` — `FirstValueFlow`: first_run_command, what_user_gets_back, why_useful, what_to_do_next. Optional: embed in StarterKit or separate list per kit. |
| Create | `src/workflow_dataset/starter_kits/registry.py` — BUILTIN_STARTER_KITS (founder_ops_starter, analyst_starter, developer_starter, document_worker_starter); list_kits(), get_kit(kit_id). Each kit references existing domain_pack IDs and job/routine IDs (may not exist yet; report missing). |
| Create | `src/workflow_dataset/starter_kits/recommend.py` — recommend_kit_from_profile(profile, repo_root) → (StarterKit, score, reason), alternatives (list of (kit, score)), missing_prerequisites (list). Use recommend_domain_packs + map domain_id to kit_id; optionally load UserWorkProfile from disk. |
| Create | `src/workflow_dataset/starter_kits/report.py` — format_kit_show(kit), format_recommendation(recommendation result), format_first_run_flow(kit). |
| Modify | `src/workflow_dataset/cli.py` — Add `kits_group` with commands: `list`, `recommend`, `show --id`, `first-run --id`. |
| Create | `tests/test_starter_kits.py` — registry list/get, recommend from profile, first-value flow, missing prerequisites, unsupported/missing job or routine. |
| Create | `docs/M23Y_STARTER_KITS.md` — usage, sample kit definition, sample recommendation, sample first-value flow, CLI, safety. |

---

## 4. Safety/risk note

- **No auto-download / auto-enable**: Kits only reference existing domain packs, job IDs, routine IDs, and runtime policy. They do not download models or enable external integrations.
- **Explicit and inspectable**: Kit definitions are in code (registry); first-run command is a suggested CLI command string, not an auto-executed script.
- **Preserve gates**: trusted_real_eligibility_notes and approvals_likely_needed are advisory; real execution still requires approval registry and check_job_policy. first_simulate_only_workflow emphasizes simulate-first.
- **Local-first**: All data from existing local sources; no cloud or telemetry.

---

## 5. What this phase will NOT do

- **No auto-download of models or datasets**: Kits recommend model classes and recipe; operator still runs setup/llm/copilot explicitly.
- **No auto-enable of external integrations**: Integration recommendations remain opt-in.
- **No broadening to every field**: Only a small set of built-in kits (founder/operator, analyst/researcher, developer, document-heavy); no generic “create your own kit” UI in this phase.
- **No cloud default**: All kit logic is local; no cloud behavior.
- **No change to approval or trust gates**: Real mode and apply still require explicit approval and policy checks.
