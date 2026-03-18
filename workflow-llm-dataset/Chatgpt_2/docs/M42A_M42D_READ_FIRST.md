# M42A–M42D Local Model Registry + Task-Aware Runtime Routing — Read First

## 1. What model/runtime/routing structures already exist

- **runtime_mesh/** (M23T/M23S):  
  - **backend_registry**: `BackendProfile` (backend_id, backend_family, local, tool_calling, vision, embedding, coding_agent_suitable, desktop_assistant_suitable, status=available|configured|missing|unsupported). Load from `data/local/runtime/backend_profiles.json` or built-in seed. `get_backend_status(backend_id)`.  
  - **model_catalog**: `ModelEntry` (model_id, backend_family, capability_classes, tags, recommended_usage, context_size, notes). Load from `data/local/runtime/model_catalog.json` or built-in seed. `list_models_by_capability`, `get_model_info`.  
  - **policy**: `TASK_CLASS_POLICY` maps task_class (e.g. desktop_copilot, codebase_task, inbox, plan_run_review, lightweight_edge) → capability + backend_preference. `recommend_for_task_class(task_class)` → backend_id, backend_status, model_class, model_ids[], missing[], reason. `recommend_backend_for_task`, `compatibility_for_model`.  
  - **integration_registry**: IntegrationManifest (supported_job_categories, required_runtime_classes, required_model_classes).  
  - **summary**: `build_runtime_summary` → backends, task_class_dependencies, available/missing/unsupported backend_ids.  
  - **validate**: `run_runtime_validate` → passed, task_class_results, model_results.

- **CLI**: Under `workflow-dataset runtime`: backends, catalog, integrations, recommend (--task-class), profile, compatibility, summary, validate, profiles, llama-cpp-check.  
- **Mission control**: `state["runtime_mesh"]` has available_backends, missing_runtimes, recommended_backend_desktop_copilot/codebase_task, runtime_validation_passed, etc. Report prints backends, desktop_copilot/codebase_task, integrations.

- **Gaps**: No explicit “local model entry” with version/provenance; no “runtime entry” separate from backend profile; no capability profile with context/tool/latency/hardware; no task families (planning, summarization, review, council, adaptation); no production_safe vs experimental_safe; no fallback chain; no route explanation; no availability or fallback-report; no degraded-mode route; no `workflow-dataset models list|show|route|availability|fallback-report`.

---

## 2. Which useful repo patterns fit this layer

- **karpathy/nanochat**: “Single complexity dial; eval metrics and task-based eval structure” — already mapped to eval.board / learning_lab. For M42: use **task-based structure** (task families + recommended model/backend) without adopting training or inference code. Fit: task families and a single “complexity” or capability tier per route.  
- **karpathy/autoresearch**: “Experiment loop; program/context as human-editable” — already in learning_lab. For M42: **no direct use**; routing does not run experiments.  
- **karpathy/jobs**: “Score with rubric + rationale; dataset slice → LLM eval” — already in learning_lab/safe_adaptation. For M42: **job categories** align with task_class / task family (e.g. codebase_task, document_workflow). Use job-category-style task families, no OpenRouter/Playwright.  
- **karpathy/llm-council**: “Multi-LLM → review/rank → Chairman synthesizes” — already in council. For M42: **council roles** as a task family (e.g. review, critique, synthesis) so routing can recommend which local model backs council perspectives. Conceptual only; no code pull.

**Selective reuse**: No vendoring. Adopt only: (1) task-family + capability-tier structure (nanochat-style), (2) job-category-style task classification (jobs-style), (3) council role as a task family for routing (llm-council conceptual). No inference code, no cloud, no training.

---

## 3. Which do not fit and why

- **karpathy/nanochat**: Full training/tokenization/finetuning/inference — **rejected**; would require GPU and change product to training platform.  
- **karpathy/autoresearch**: Agent editing train.py, 5-min GPU training — **rejected**; self-modifying code and GPU.  
- **karpathy/jobs**: OpenRouter API, Playwright, BLS — **rejected**; cloud and external API.  
- **Any repo**: Auto-download models, cloud inference, hidden routing — **rejected**; local-first and inspectable only.

---

## 4. Exact file plan

| Action | File | Purpose |
|--------|------|--------|
| **Extend** | `runtime_mesh/model_catalog.py` | Add fields to ModelEntry (or add LocalModelEntry): task_families[], context_length, tool_use, latency_tier, hardware_assumptions, trust_notes, production_safe, experimental_safe, fallback_model_id, version, provenance. Keep backward compatibility with existing catalog load. |
| **Extend** | `runtime_mesh/backend_registry.py` | Add runtime_entry_id or keep BackendProfile; add production_safe / experimental_safe if needed. Optional: RuntimeEntry dataclass for “runtime” as first-class (backend + status + safe tier). |
| **Create** | `runtime_mesh/routing.py` | Task families (planning, summarization, review, suggestion, vertical_workflow, evaluation, council, adaptation_comparison). route_for_task(task_family, trust_posture, cohort_constraint, repo_root) → primary_model_id, primary_backend_id, fallback_chain[], explanation, degraded_route. availability_check(repo_root). build_fallback_report(repo_root). |
| **Extend** | `runtime_mesh/policy.py` | Map task_family → task_class (or capability) and call existing recommend_for_task_class; add trust_posture and production_safe filtering; integrate with routing.py. |
| **Create** | `runtime_mesh/registry_models.py` | Optional: LocalModelEntry, RuntimeEntry, CapabilityProfile, FallbackChain as first-class dataclasses if we don’t want to overload model_catalog. (Alternative: everything in model_catalog.py + backend_registry.py.) |
| **Extend** | `runtime_mesh/__init__.py` | Export routing module (route_for_task, availability_check, build_fallback_report) and any new models. |
| **CLI** | `cli.py` | Add under **models** group (existing benchmark group): `models list`, `models show --id`, `models route --task <family> [--explain]`, `models availability`, `models fallback-report`. Keep existing models promote/rollback/quarantine/reject. |
| **Mission control** | `mission_control/state.py` | Extend runtime_mesh (or add model_registry) block: active_registry_count, production_safe_route_count, degraded_or_missing_runtimes[], most_used_route_task, next_recommended_runtime_review. |
| **Mission control** | `mission_control/report.py` | Add line(s) for model registry: e.g. production_safe_routes, degraded_runtimes, next_review. |
| **Tests** | `tests/test_model_registry_routing.py` | Registry entry creation, routing by task family, fallback selection, degraded routing, production_safe vs experimental_safe, invalid/missing-runtime cases. |
| **Docs** | `docs/M42A_M42D_MODEL_REGISTRY_ROUTING.md` | Sample registry entry, routing explanation, fallback report, CLI usage, remaining gaps. |

---

## 5. Safety/risk note

- **Local-only**: No new cloud or auto-download; registry and routing use existing runtime_mesh data and local files.  
- **Inspectable**: Route explanation and fallback report are explicit; no silent override of operator choices.  
- **Trust boundaries**: production_safe vs experimental_safe keeps experimental models from being recommended for production paths unless explicitly allowed.  
- **No wholesale replace**: Extend existing backend_registry and model_catalog; add routing layer on top without removing current recommend_for_task_class usage.  
- **Risk**: If downstream code starts to “always use route_for_task” without fallback handling, missing runtimes could cause failures; mitigation: routing returns degraded_route and explanation so callers can decide.

---

## 6. Routing principles

- **Task family first**: Route by task family (planning, summarization, review, council, adaptation, etc.); map family to existing task_class/capability where possible.  
- **Trust posture**: Prefer production_safe models for production-cut/cohort-constrained contexts; allow experimental_safe only when explicitly permitted.  
- **Availability**: Prefer backends with status available/configured; if primary is missing, use fallback_chain.  
- **Degraded mode**: When no preferred model/backend is available, return a degraded_route (e.g. next-best or “none”) and clear explanation so caller can fail gracefully or warn.  
- **Explicit and reversible**: Every route has an explanation; no hidden overrides; operator can inspect and change registry/config.

---

## 7. What this block will NOT do

- **Will not** rewrite the current runtime stack (planner, executor, packs, trust, policy, approvals) or replace runtime_mesh backend/catalog/policy.  
- **Will not** add cloud model dependencies or auto-download.  
- **Will not** vendor large external code from Karpathy or others.  
- **Will not** silently change routing without explanation.  
- **Will not** implement actual inference calls; only registry + routing recommendations.  
- **Will not** enforce routing in every call site; callers adopt routing optionally.

---

*Proceeding to implement Phases A–E per the file plan above.*
