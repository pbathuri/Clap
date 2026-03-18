# M24A — External Capability Activation Planner

Planning layer for **what external capabilities are available**, **what can be safely activated**, **what is recommended** for a given user/domain/machine, and **what must NOT be activated**. No auto-download; no silent enablement. Local-first, explicit, approval-aware.

## 1. External capability source registry

Unified registry built from:

- **Integration manifests** (OpenClaw, coding_agent, ide_editor, notebook_rag)
- **Backend profiles** (ollama, repo_local, llama_cpp) as `backend_*` sources
- **Model catalog** (each Ollama/repo_local model as `ollama_<model_id>` or `model_<model_id>`)

Optional override file: `data/local/runtime/external_capability_sources.json` (per-source overrides for `activation_status`, `enabled`, etc.).

### Schema (ExternalCapabilitySource)

- `source_id`, `category` (ollama_model, openclaw, coding_agent, ide_editor, automation, embeddings, vision_ocr, optional_model_dataset)
- `local`, `optional_remote`
- `install_prerequisites`, `license_policy`, `usage_policy`
- `security_notes`, `approval_notes`, `trust_notes`
- `supported_task_classes`, `supported_domain_pack_ids`, `supported_tiers`
- `estimated_resource` (low/medium/high), `activation_status`, `enabled`, `display_name`, `notes`

### Sample registry entry (from integration)

```json
{
  "source_id": "openclaw",
  "category": "openclaw",
  "local": true,
  "optional_remote": false,
  "security_notes": "Reference-only in this repo; no live import.",
  "supported_task_classes": ["desktop_assistant", "orchestration"],
  "supported_tiers": ["dev_full", "local_standard"],
  "activation_status": "optional",
  "enabled": false,
  "display_name": "Openclaw"
}
```

## 2. Activation planner

**Inputs:** machine profile (tier, edge_profile), optional domain_pack_id, task_class, trust_posture (safe_to_expand, approval_registry_exists).

**Outputs:**

- `recommended` — sources to recommend (already available or recommended for activation)
- `blocked` — (reserved; currently combined with rejected/not_worth_it for display)
- `not_worth_it` — not useful for this profile/task
- `rejected_by_policy` — unsupported_license, resource_too_high, unsafe_trust_posture, incompatible_machine, remote_only_local_first, missing_approvals
- `prerequisite_steps` — install/activation steps to perform
- `resource_estimate` — low/medium/high counts and tier

## 3. Pull/install/enable plans

`build_activation_plan(source_id, repo_root)` returns a **list of steps only** (no execution):

- Ollama model: ensure Ollama running → pull model (plan only) → enable in config
- OpenClaw: enable compatibility (reference-only)
- coding_agent: prepare integration, prerequisites
- ide_editor: add metadata; no auto-enable
- backend_*: configure backend per install_prerequisites

All steps are **safe_local** when applicable; no blind downloads.

## 4. Policy and rejection layer

`apply_rejection_policy(source, machine_profile, trust_posture, domain_pack_id?, task_class?)` returns `(allowed, reason)`.

Rejection reasons:

- `unsupported_license`
- `resource_too_high` (e.g. high resource on constrained_edge/minimal_eval)
- `not_useful_for_profile` (domain/task not supported)
- `unsafe_trust_posture` (approval required but registry missing when safe_to_expand is False)
- `incompatible_machine` (tier not in supported_tiers)
- `remote_only_local_first` (source is remote-only)
- `missing_approvals`

## 5. CLI

All under `workflow-dataset capabilities external`:

| Command | Description |
|--------|-------------|
| `list` | List external capability sources |
| `recommend` | Recommend capabilities for this machine/domain/task |
| `plan --source <id>` | Show activation plan for a source (steps only) |
| `blocked` | List blocked and rejected capabilities |
| `explain --source <id>` | Explain a single source (metadata, policy, trust) |

### Exact CLI usage

```bash
workflow-dataset capabilities external list
workflow-dataset capabilities external list --repo-root /path/to/repo

workflow-dataset capabilities external recommend
workflow-dataset capabilities external recommend --domain founder_ops --task desktop_copilot

workflow-dataset capabilities external plan --source ollama_qwen2.5-coder
workflow-dataset capabilities external plan --source openclaw --repo-root /path

workflow-dataset capabilities external blocked
workflow-dataset capabilities external blocked --task codebase_task

workflow-dataset capabilities external explain --source openclaw
workflow-dataset capabilities external explain --source ollama_qwen2.5-coder
```

Note: `plan` and `explain` require `--source <source_id>`.

## 6. Sample outputs

### Sample activation recommendation output

```
Recommended external capabilities
---
  backend_ollama  reason=already_available  resource=medium
  openclaw  reason=recommended_activation  resource=medium
  ollama_qwen2.5-coder  reason=recommended_activation  resource=medium

Prerequisite steps:
  - Ensure Ollama is installed and running (e.g. http://127.0.0.1:11434)
  - Pull model 'qwen2.5-coder' via Ollama (e.g. ollama pull qwen2.5-coder). Plan only — no auto-download.

Resource estimate: {'low_count': 2, 'medium_count': 5, 'high_count': 1, 'tier': 'local_standard'}
```

### Sample blocked/rejected output

```
Blocked / rejected external capabilities
---
Rejected by policy:
  cloud_only  reason=remote_only_local_first  code=remote_only_local_first
  heavy  reason=resource_too_high  code=resource_too_high
Not worth it on this profile:
  some_source  reason=not_useful_for_task
```

### Sample activation plan (openclaw)

```
Activation plan for source: openclaw
---
  1. [enable_openclaw_compatibility] (safe local) Enable OpenClaw compatibility (reference-only in this repo; no live import). Update integration manifest if desired.
```

### Sample activation plan (Ollama model)

```
Activation plan for source: ollama_qwen2.5-coder
---
  1. [ensure_ollama_running] (safe local) Ensure Ollama is installed and running (e.g. http://127.0.0.1:11434).
  2. [pull_model] (safe local) Pull model 'qwen2.5-coder' via Ollama (e.g. ollama pull qwen2.5-coder). Plan only — no auto-download.
  3. [enable_in_config] (safe local) Add or confirm model in configs/settings.yaml or runtime model_catalog for this capability.
```

## 7. Mission control hooks

`get_mission_control_state(repo_root)` includes an additive section **external_capabilities**:

- `recommended` — list of recommended source ids
- `recommended_count`
- `blocked` — list of blocked/rejected source ids
- `blocked_count`
- `missing_prerequisites` — prerequisite steps
- `plans_pending_review` — source ids that are recommended but not yet installed
- `resource_estimate` — dict with low_count, medium_count, high_count, tier

## 8. Tests

Run:

```bash
pytest tests/test_external_capability.py -v
```

Covered:

- **Registry:** load, list, get; schema to_dict/from_dict
- **Policy:** rejection for remote_only, incompatible_machine, unsupported_license, resource_too_high
- **Planner:** plan returns PlannerResult; plan_activations convenience
- **Plans:** build_activation_plan for known source and unknown source
- **Report:** format_external_list, format_recommend, format_blocked, format_plan, format_explain

## 9. What this phase does NOT do

- **No auto-download** of models or assets
- **No silent enablement** of external integrations
- **No cloud/remote activation**; local-first only
- **No rewrite** of runtime mesh, trust, or approval logic
- **No execution** of install/pull/enable steps (plans only)

## 10. Next step for the pane

- **Optional:** Add `data/local/runtime/external_capability_sources.json` with operator overrides (activation_status, enabled) for specific sources.
- **Optional:** Wire mission control UI/dashboard to show `external_capabilities.recommended` and `plans_pending_review` with links to `capabilities external plan <id>`.
- **Optional:** Extend policy with more license/usage rules from OPEN_SOURCE_REJECTION_CRITERIA.md and wire capability_intake adoption_recommendation into the registry.
