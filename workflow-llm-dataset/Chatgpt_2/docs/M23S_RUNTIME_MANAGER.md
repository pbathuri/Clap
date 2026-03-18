# M23S — Local Runtime / Backend Manager with Optional llama.cpp Compatibility

## Objective

Make the product’s local inference/runtime layer easier to manage across machines:

1. **Summarize** available local backends  
2. **Show** which product surfaces (task classes) depend on which runtime  
3. **Validate** model/runtime compatibility  
4. **Optional** llama.cpp compatibility check and config profile path  
5. **Expose** backend assumptions to operators  
6. **Improve** portability across developer machines and edge builds  

Constraints: **Backend-agnostic**; **no runtime rewrite**; **llama.cpp is optional**; **no hidden downloads**; **no remote provider dependence**.

---

## CLI

```bash
workflow-dataset runtime summary [--repo-root PATH] [--output FILE]
workflow-dataset runtime validate [--repo-root PATH] [--output FILE] [--skip-models]
workflow-dataset runtime profiles [--repo-root PATH]
workflow-dataset runtime llama-cpp-check [--repo-root PATH] [--output FILE]
```

- **runtime summary** — Available backends and which task classes (product surfaces) depend on them.  
- **runtime validate** — Compatibility check for each task class and (by default) each model in the catalog; exits 1 if any fail. Use `--skip-models` to validate only task classes.  
- **runtime profiles** — List backend profiles with status and install prerequisites; show task class → backend preference.  
- **runtime llama-cpp-check** — Optional check: llama.cpp available via PATH or LAMMACPP_PATH; reports config profile path. Not mandatory.

---

## Runtime summary

- **Backends**: from `runtime_mesh.backend_registry` (repo_local, ollama, llama_cpp, etc.) with status (available, configured, missing, unsupported).  
- **Product surfaces**: task classes (desktop_copilot, codebase_task, local_retrieval, …) with recommended backend and status.  
- Output: available/missing/unsupported backend ids and a short dependency list.

---

## Compatibility validation

- For each **task class**: recommend backend; pass if status is available or configured and there are no missing deps.  
- Optionally for each **model** in the catalog: check backend status; pass if available or configured.  
- Report: PASS/FAIL per task class (and per model if not `--skip-models`).

---

## Optional llama.cpp

- **Check**: `LAMMACPP_PATH` or `LLAMA_CPP_PATH` env; else `which llama-cli`, `llama-cpp-cli`, `main`, `llama-server`. No execution, no download.  
- **Config profile**: optional path `data/local/runtime/llama_cpp_profile.json` (reported if present or as default path).  
- **Status**: `available` (found) or `optional` (not found; product does not require it).

---

## Mission control

`get_mission_control_state()` **runtime_mesh** section now includes:

- **runtime_validation_passed** (bool)  
- **task_class_dependencies_count**  
- **llama_cpp_available** (bool)  
- **llama_cpp_status** (e.g. available, optional)

---

## Sample runtime summary

```
=== Runtime summary ===

[Backends]
  repo_local  family=repo_local  status=configured  local=True
  ollama  family=ollama  status=missing  local=True
  llama_cpp  family=llama_cpp  status=unsupported  local=True

[Product surfaces (task classes) → runtime]
  desktop_copilot → backend=repo_local  status=configured
  codebase_task → backend=repo_local  status=configured
  ...

Available: ['repo_local']  Missing: ['ollama']  Unsupported: ['llama_cpp']
```

---

## Sample compatibility report

```
=== Runtime compatibility validation ===

Some task classes or models have missing/unsupported backends.

[Task class → backend]
  PASS  desktop_copilot  backend=repo_local  status=configured
  PASS  codebase_task  backend=repo_local  status=configured
  FAIL  vision  backend=ollama  status=missing
       missing: No backend available for task_class=vision (preference: ['ollama'])

[Model → backend]
  PASS  local/small  backend=repo_local  status=configured
  FAIL  llava  backend=ollama  status=missing
  ...

(Backend-agnostic; no mandatory backends. Optional backends are opt-in.)
```

---

## Sample llama-cpp-check output

```
=== llama.cpp compatibility check (optional) ===

llama.cpp is optional. Set LAMMACPP_PATH or install llama-cli in PATH; add llama_cpp_profile.json for config.

Available: False  Status: optional
Config profile: /path/to/repo/data/local/runtime/llama_cpp_profile.json

(Optional local runtime. Not mandatory; no download.)
```

---

## Tests

```bash
pytest tests/test_runtime_mesh.py -v
```

Covers: existing M23T backend/catalog/policy tests; M23S **build_runtime_summary**, **format_runtime_summary**, **run_runtime_validate**, **format_validation_report**, **llama_cpp_check**, **format_llama_cpp_check_report**; mission_control **runtime_validation_passed** and **llama_cpp_status**.

---

## Files modified / created

| Action | Path |
|--------|------|
| Created | `src/workflow_dataset/runtime_mesh/summary.py` — build_runtime_summary, format_runtime_summary |
| Created | `src/workflow_dataset/runtime_mesh/validate.py` — run_runtime_validate, format_validation_report |
| Created | `src/workflow_dataset/runtime_mesh/llama_cpp_check.py` — llama_cpp_check, format_llama_cpp_check_report |
| Modified | `src/workflow_dataset/runtime_mesh/__init__.py` — exports for summary, validate, llama_cpp_check |
| Modified | `src/workflow_dataset/cli.py` — runtime summary, validate, profiles, llama-cpp-check |
| Modified | `src/workflow_dataset/mission_control/state.py` — runtime_mesh: runtime_validation_passed, task_class_dependencies_count, llama_cpp_available, llama_cpp_status |
| Modified | `tests/test_runtime_mesh.py` — M23S tests and mission_control assertions |
| Created | `docs/M23S_RUNTIME_MANAGER.md` — this doc |

---

## Next phase

- **llama_cpp_profile.json schema**: Optional JSON schema and docs for `data/local/runtime/llama_cpp_profile.json` (model path, n_ctx, etc.) when operators opt into llama.cpp.  
- **Dashboard runtime widget**: Surface runtime summary and validation result in the operator dashboard (e.g. backends, validation passed, llama_cpp status).  
- **Per-backend health**: Optional lightweight “ping” for backends that support it (e.g. Ollama /api/tags already used for status) without changing the stack.
