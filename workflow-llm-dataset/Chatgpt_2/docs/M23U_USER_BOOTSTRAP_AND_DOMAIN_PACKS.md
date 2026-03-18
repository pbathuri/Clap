# M23U — User Bootstrap + Domain Pack Builder + Specialization Recipes

## Purpose

Turn a generic local operator system into one that understands the user’s **field**, **job family**, and likely **workflow profile** by:

- Bootstrapping a **user work profile** (explicit, editable)
- Mapping that profile to **domain packs**
- Mapping domain packs to job packs, routines, model/dataset/integration classes, and **specialization recipes**
- Providing a **policy layer** that filters by machine and safety posture
- **Recipe generation only** — no auto-download, no auto-training

All behavior is **local**, **inspectable**, and **operator-approved**.

---

## CLI usage

| Command | Description |
|--------|-------------|
| `workflow-dataset profile bootstrap` | Create or update user work profile (optionally `--field`, `--job-family`). |
| `workflow-dataset profile show` | Show current user work profile and bootstrap profile summary. |
| `workflow-dataset profile operator-summary` | Generate operator summary (recommended domain pack, models, specialization route, data usage, simulate-only scope). Optional `--output FILE` to write markdown. |
| `workflow-dataset packs domain list` | List built-in domain pack IDs and names. |
| `workflow-dataset packs domain recommend --field operations` | Recommend domain packs for a field (optional `--job-family`). |
| `workflow-dataset recipe build --pack founder_ops` | Build specialization recipe for a domain pack (output spec only). |
| `workflow-dataset recipe explain --id retrieval_only` | Explain a recipe by id (mode, data sources, licensing, steps). |

---

## Sample user work profile

Stored at `data/local/onboarding/user_work_profile.yaml`:

```yaml
field: operations
vertical: ""
job_family: founder_ops
daily_task_style: document_heavy
important_apps_tools: []
document_types: []
communication_reporting_style: ""
risk_safety_posture: conservative
preferred_automation_degree: simulate_first
hardware_runtime_constraints: []
preferred_edge_tier: local_standard
created_at: "2025-03-16T12:00:00Z"
updated_at: "2025-03-16T12:00:00Z"
notes: ""
```

---

## Sample domain pack definition

Built-in `founder_ops`:

- **domain_id**: founder_ops  
- **name**: Founder / small-team operations  
- **suggested_job_packs**: weekly_status, status_action_bundle, stakeholder_update_bundle, meeting_brief_bundle  
- **suggested_routines**: morning_reporting, weekly_review  
- **suggested_model_classes**: llama3.2, mistral, phi  
- **suggested_embedding_classes**: nomic-embed-text, mxbai-embed-large  
- **suggested_recipe_id**: retrieval_only  
- **expected_approvals**: path_workspace, apply_confirm  
- **trust_notes**: Simulate-first; real apply only after approval.

---

## Sample specialization recipe

**retrieval_only**:

- **mode**: retrieval_only  
- **data_sources**: `{ "local_only": true }`  
- **licensing_compliance_metadata**: `{ "source": "local" }`  
- **auto_download**: false  
- **auto_train**: false  
- **steps_summary**: Build/refresh embedding index from local corpus; use retrieval at inference.

---

## Sample model/dataset recommendation output

From `profile operator-summary` (or `build_operator_summary`):

- **recommended_domain_packs**: e.g. `[{ "domain_id": "founder_ops", "name": "Founder / small-team operations", "score": 0.8 }]`  
- **recommended_model_classes**: e.g. `["llama3.2", "mistral", "phi"]`  
- **recommended_embedding_classes**: e.g. `["nomic-embed-text", "mxbai-embed-large"]`  
- **recommended_specialization_route**: e.g. `retrieval_only`  
- **data_usage**: e.g. `["local user data only (corpus, SFT dirs)"]`  
- **simulate_only_scope**: e.g. `["All real apply requires explicit approval; recommended: run simulate first."]`  
- **training_inference_path**: e.g. retrieval-only by default; for adapter/SFT, build SFT from local data and run training backend with operator-approved config (no auto-train).  
- **catalog_filtered_models**: If a seed catalog (e.g. Ollama model list) is passed in, models filtered to allowed classes.

---

## Safety and constraints

- **Explicit only** — User work profile and domain pack selection are explicit and editable; no silent inference of high-risk approvals or cloud behavior.  
- **Recipe generation only** — No auto-download of datasets, no auto-launch of training. Licensing/compliance fields are for operator review.  
- **Catalog as input** — An external model/tool catalog (e.g. Ollama) is an optional input to the policy layer; we filter and recommend. We do not fetch catalogs by default.  
- **Local-only** — All outputs under `data/local/onboarding/`; domain pack and recipe definitions in code or local config.  
- **Gates preserved** — `check_job_policy` and the approval registry remain the execution gate; domain/recipe layer only recommends and configures.

---

## What this phase does NOT do

- **No auto-training** — Does not invoke training backends or start training jobs.  
- **No auto-download** — Does not download datasets or models; recipes may reference approved dataset/model IDs with licensing metadata for the operator to resolve.  
- **No auto-enable of external integrations** — Does not turn on Ollama or other runtimes; only recommends model classes that match policy.  
- **No silent high-risk approvals** — Does not add or assume approval registry entries.  
- **No cloud-default behavior** — All defaults remain local and simulate-first where applicable.

---

## Tests

- **test_user_work_profile.py** — Profile create, save, load, bootstrap.  
- **test_domain_packs.py** — Domain list, get, recommend by field, policy filtering, unsupported/refusal.  
- **test_specialization_recipes.py** — Recipe build, explain, licensing metadata, no auto-download/train.  
- **test_operator_summary.py** — Summary generation, machine/resource filtering.

Run:

```bash
pytest tests/test_user_work_profile.py tests/test_domain_packs.py tests/test_specialization_recipes.py tests/test_operator_summary.py -v
```

---

## Next step for the pane

- **Pane 1** (runtime/backend registry): Provide stable interfaces for **model class** and **tool/capability** registration so that domain packs and the policy layer can resolve “suggested_model_classes” and “suggested_embedding_classes” against a real catalog (e.g. Ollama model list) without depending on concrete implementation details.  
- This repo will consume that catalog (or a filtered subset) as input to `filter_models_by_policy` and `build_operator_summary(catalog_entries=...)` and will not auto-download or auto-enable any runtime.
