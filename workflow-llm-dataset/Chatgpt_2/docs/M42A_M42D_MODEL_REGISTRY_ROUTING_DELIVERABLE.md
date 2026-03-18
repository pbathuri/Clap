# M42A–M42D Local Model Registry + Task-Aware Runtime Routing — Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/runtime_mesh/model_catalog.py` | Extended `ModelEntry` with `task_families`, `tool_use`, `latency_tier`, `hardware_assumptions`, `trust_notes`, `production_safe`, `experimental_safe`, `fallback_model_id`, `version`, `provenance`. Seed catalog and load/serialize updated. |
| `src/workflow_dataset/runtime_mesh/__init__.py` | Exported `route_for_task`, `availability_check`, `build_fallback_report`, `explain_route`, `TASK_FAMILIES`. |
| `src/workflow_dataset/cli.py` | Added under `models` group: `models list`, `models show --id`, `models route --task`, `models availability`, `models fallback-report`. |
| `src/workflow_dataset/mission_control/state.py` | Extended `runtime_mesh` state with `active_registry_count`, `production_safe_route_count`, `degraded_or_missing_runtimes`, `most_used_route_task`, `next_recommended_runtime_review`. |
| `src/workflow_dataset/mission_control/report.py` | Report block for runtime mesh now includes registry_models, production_safe_routes, degraded_or_missing, next_recommended_runtime_review. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/runtime_mesh/routing.py` | `TASK_FAMILIES`, `TASK_FAMILY_TO_CLASS`, `route_for_task()`, `availability_check()`, `build_fallback_report()`, `explain_route()`. |
| `docs/M42A_M42D_READ_FIRST.md` | Read-first analysis: existing structures, Karpathy fit/reject, file plan, safety, routing principles. |
| `tests/test_model_registry_routing.py` | 10 tests: registry load, task_families/safe flags, get_model_info, route structure, family→class mapping, availability, fallback report, production_safe filtering, invalid family, missing runtime degraded. |
| `docs/M42A_M42D_MODEL_REGISTRY_ROUTING_DELIVERABLE.md` | This file. |

---

## 3. Exact CLI usage

```bash
# List local model registry entries
workflow-dataset models list
workflow-dataset models list --json

# Show one model
workflow-dataset models show --id llama3.2
workflow-dataset models show --id local/small --json

# Route by task family (optionally with explanation)
workflow-dataset models route --task planning
workflow-dataset models route --task vertical_review --explain
workflow-dataset models route --task council --trust experimental --json

# Availability and fallback report
workflow-dataset models availability
workflow-dataset models availability --json
workflow-dataset models fallback-report
workflow-dataset models fallback-report --json
```

Task families: `planning`, `summarization`, `review`, `suggestion`, `vertical_workflow`, `evaluation`, `council`, `adaptation_comparison`.

---

## 4. Sample model registry entry

```json
{
  "model_id": "llama3.2",
  "backend_family": "ollama",
  "capability_classes": ["general_chat_reasoning", "lightweight_edge"],
  "tags": ["chat"],
  "recommended_usage": ["desktop_copilot", "inbox"],
  "context_size": 128000,
  "notes": "General chat; edge-friendly.",
  "task_families": ["planning", "summarization", "suggestion"],
  "production_safe": true,
  "experimental_safe": true,
  "fallback_model_id": "local/small"
}
```

---

## 5. Sample routing explanation

**CLI:** `workflow-dataset models route --task planning --explain`

Example output (structure):

```
Route   task_family=planning
  primary_model=llama3.2  primary_backend=ollama  status=missing
  fallback_chain=[]  is_degraded=True
  task_family=planning -> task_class=plan_run_review -> capability=safety_guardrail; backend_preference=...; primary=llama3.2 backend=ollama status=missing.
```

**JSON** (`--json`):

```json
{
  "task_family": "planning",
  "task_class": "plan_run_review",
  "primary_model_id": "llama3.2",
  "primary_backend_id": "ollama",
  "backend_status": "missing",
  "fallback_chain": [],
  "explanation": "task_family=planning -> task_class=plan_run_review -> capability=safety_guardrail; ...",
  "degraded_route": { "model_id": "llama3.2", "reason": "Backend missing or unsupported; install or enable backend for this model." },
  "is_degraded": true,
  "missing": ["No backend available for task_class=plan_run_review ..."]
}
```

---

## 6. Sample fallback report

**CLI:** `workflow-dataset models fallback-report`

Example:

```
Fallback report   Routes OK: 2; Degraded: 6.
  planning: primary=llama3.2 backend=ollama [degraded]
  summarization: primary=llama3.2 backend=ollama [degraded]
  review: primary=— backend=— [degraded]
  ...
  recommended: Install or enable backends: ollama, repo_local; Degraded task families (add model or backend): planning, summarization, ...
```

**JSON** (`--json`): `availability`, `per_task_family` (list of { task_family, primary_model_id, primary_backend_id, backend_status, fallback_chain, is_degraded, degraded_route, explanation_short }), `recommended_actions`, `summary`.

---

## 7. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_model_registry_routing.py -v --tb=short
```

**Result:** 10 passed.

- test_registry_loads_entries  
- test_registry_entry_has_task_families_and_safe_flags  
- test_get_model_info  
- test_route_for_task_returns_structure  
- test_route_for_task_maps_family_to_class  
- test_availability_check_returns_backends_and_task_families  
- test_fallback_report_has_per_task_family_and_recommended_actions  
- test_production_safe_filtering  
- test_invalid_task_family_uses_default_class  
- test_missing_runtime_degraded  

---

## 8. Remaining gaps for later refinement

- **Cohort / production-cut constraints**: Routing does not yet filter by cohort_id or production-cut vertical; add optional params and filter by pack/vertical when needed.  
- **Hardware/runtime availability**: Availability uses existing backend status only; no separate “hardware profile” check (e.g. 8gb_ram).  
- **Most-used route**: Mission control `most_used_route_task` is a heuristic (desktop_copilot vs codebase_task by backend); real usage stats would require instrumentation.  
- **Call-site adoption**: Planner, executor, council, learning lab do not yet call `route_for_task()`; they keep using existing recommend_for_task_class or hardcoded choices. Wire routing where product tasks should be task-family aware.  
- **Persisted overrides**: User overrides (e.g. “prefer model X for planning”) are not persisted; only catalog and backend registry are persisted.  
- **Version/provenance**: Fields exist on ModelEntry but are not yet used in routing or reports.
