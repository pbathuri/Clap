# Capability pack manifest schema (M21)

Minimal schema for a capability pack manifest. Used for validation and future pack installer.

---

## Required fields

| Field | Type | Description |
|-------|------|-------------|
| pack_id | string | Unique pack identifier |
| name | string | Human-readable name |
| version | string | Semver or date-based (e.g. 0.1.0) |

---

## Optional fields

| Field | Type | Description |
|-------|------|-------------|
| description | string | Short description |
| recommended_models | list[string] | Model ids or paths (local) |
| prompts | list[object] | Prompt templates or refs |
| retrieval_config | object | top_k, corpus_filter, etc. |
| parser_config | object | Adapter or parser settings |
| workflow_templates | list[string] | Task ids or scenario ids |
| evaluation_tasks | list[string] | Eval task ids |
| safety_policies | object | sandbox_only, require_apply_confirm, no_network_default |
| orchestration | object | Optional multi-step config (future) |
| output_adapters | list[string] | e.g. ops_handoff, document |
| release_modes | list[string] | baseline, adapter, retrieval, adapter_retrieval |
| license | string | Pack license |
| source_repo | string | Optional canonical URL of source |
| role_industry_workflow_tags | list[string] | e.g. ops, creative, reporting |
| installer_recipes | list[object] | Steps to install pack locally |
| dependencies | list[string] | Pack or repo dependencies |
| supported_os_hardware | list[string] | e.g. macos, linux, cpu, gpu |

---

## Safety defaults

- **sandbox_only:** true
- **require_apply_confirm:** true
- **no_network_default:** true

A pack manifest must not override these to false unless explicitly allowed by policy (and we do not allow that in M21).

---

## Example (minimal)

```json
{
  "pack_id": "ops_reporting_v1",
  "name": "Operations reporting assistant",
  "version": "0.1.0",
  "description": "Narrow release pack: ops reporting, status scaffold, next steps.",
  "recommended_models": [],
  "output_adapters": ["ops_handoff"],
  "release_modes": ["adapter", "baseline"],
  "safety_policies": {
    "sandbox_only": true,
    "require_apply_confirm": true,
    "no_network_default": true
  }
}
```

---

## Validation

Use `workflow-dataset packs validate-manifest <path>` to validate a manifest file against this schema (see pack_models.py).
