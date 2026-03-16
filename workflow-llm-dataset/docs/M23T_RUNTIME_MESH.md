# M23T — Ollama Runtime Mesh + Integration Registry

## Objective

Build a runtime/integration mesh so the product can understand and manage:

- Ollama-backed local model execution
- Optional OpenClaw assistant compatibility
- Optional coding-agent / IDE / automation integration manifests
- Model capability routing
- Local runtime profiles
- Future optional llama.cpp compatibility

This phase provides the **control plane** for model/tool/runtime selection. It does not force full integration of every external tool.

## What was built

### 1. Runtime backend registry

- **Module:** `src/workflow_dataset/runtime_mesh/backend_registry.py`
- **Seed profiles:** `repo_local`, `ollama`, `llama_cpp`
- **Fields:** backend_id, backend_family, local, optional_remote, tool_calling, thinking_reasoning, vision, embedding, ocr, coding_agent_suitable, desktop_assistant_suitable, hardware_profile_requirements, install_prerequisites, notes, risk_trust_notes, **status** (available | configured | missing | unsupported)
- **Storage:** Optional `data/local/runtime/backend_profiles.json`; built-in seed if missing

### 2. Ollama model capability catalog

- **Module:** `src/workflow_dataset/runtime_mesh/model_catalog.py`
- **Capability classes:** general_chat_reasoning, coding_agentic_coding, embeddings, vision_ocr, safety_guardrail, lightweight_edge, high_context, multilingual_translation
- **Seed entries:** llama3.2, qwen2.5-coder, qwen3-coder-next, nomic-embed-text, llava, local/small
- **Storage:** Optional `data/local/runtime/model_catalog.json`; built-in seed if missing
- No hardcoding of every model in product logic; catalog is the single store.

### 3. Integration manifest registry

- **Module:** `src/workflow_dataset/runtime_mesh/integration_registry.py`
- **Manifest fields:** integration_id, local, optional_remote, supported_job_categories, required_runtime_classes, required_model_classes, required_approvals, supported_adapters, security_notes, install_status, enabled
- **Seed manifests:** openclaw, coding_agent, ide_editor, notebook_rag (reference/compatibility only; no full implementation)

### 4. Runtime selection policy

- **Module:** `src/workflow_dataset/runtime_mesh/policy.py`
- **Task classes:** desktop_copilot, inbox, codebase_task, coding_agent, local_retrieval, document_workflow, vision, plan_run_review, lightweight_edge
- **Answers:** which backend for which task class, which model class is suitable, which integrations are available, what is missing and why

### 5. CLI

| Command | Description |
|--------|-------------|
| `workflow-dataset runtime backends` | List backend profiles and status |
| `workflow-dataset runtime catalog` | List model catalog (optional `--capability`) |
| `workflow-dataset runtime integrations` | List integration manifests and enable state |
| `workflow-dataset runtime recommend --task-class <class>` | Recommend backend and model class for task |
| `workflow-dataset runtime profile --backend <id>` | Full profile for a backend |
| `workflow-dataset runtime compatibility --model <id>` | Compatibility report for a model |

### 6. Mission control

- **State:** `mission_control/state.py` adds `runtime_mesh`: available_backends, missing_runtimes, recommended_backend_desktop_copilot, recommended_model_class_desktop_copilot, recommended_backend_codebase_task, recommended_model_class_codebase_task, integrations_count, integrations_local_only, integrations_enabled_count
- **Report:** `mission_control/report.py` prints a [Runtime mesh] section

## Constraints (respected)

- No rewrite of the inference stack
- Ollama and llama.cpp are optional, not mandatory
- No auto-download of models
- No auto-enable of OpenClaw or other integrations
- No hidden cloud behavior
- Backend-aware, explicit runtime/integration state, local-first, safety and inspectability preserved

## Optional seed files

To override built-in defaults, create under `data/local/runtime/`:

- `backend_profiles.json` — list of backend profile objects
- `model_catalog.json` — list of model entries (or `{"models": [...]}`)
- `integration_manifests.json` — list of integration manifests (or `{"integrations": [...]}`)

User-provided Ollama model lists can be merged into `model_catalog.json` as the seed catalog.
