# A4 — Workspace export contracts + downstream handoff spec

Export contracts define a stable structure for saved workspaces so downstream systems inside the repo can rely on required files, optional files, and manifest compatibility.

---

## 1. Files modified / created

| Path | Change |
|------|--------|
| **New** `src/workflow_dataset/release/workspace_export_contract.py` | `WORKSPACE_EXPORT_SCHEMA_VERSION = "1.0"`. `EXPORT_CONTRACTS` per workflow: manifest_file, required_manifest_keys, required_files, optional_files, optional required_at_least_one_of. `get_export_contract(workflow)`, `validate_workspace_export(workspace_path)` → valid, errors, warnings, contract_version, workflow, missing_required, missing_manifest_keys, manifest_compatible. |
| `src/workflow_dataset/cli.py` | `review validate-workspace <path>` — validate workspace against contract; exit 1 if invalid. `review export-contract [--workflow ops_reporting_workspace]` — print contract (schema version, required/optional files, manifest keys). |
| `tests/test_release.py` | `test_get_export_contract`, `test_validate_workspace_export_valid`, `test_validate_workspace_export_missing_required`, `test_validate_workspace_export_missing_manifest_key`, `test_review_validate_workspace_cli`. |
| `docs/A4_WORKSPACE_EXPORT_CONTRACTS.md` | This file. |

---

## 2. Exact export/validate CLI usage

**Validate a workspace against the export contract:**
```bash
workflow-dataset review validate-workspace ops_reporting_workspace/2025-03-15_1432_abc
workflow-dataset review validate-workspace /path/to/workspace_dir
```
Exits 0 if valid; 1 if invalid (errors printed).

**Print the export contract for a workflow:**
```bash
workflow-dataset review export-contract
workflow-dataset review export-contract --workflow ops_reporting_workspace
workflow-dataset review export-contract --workflow weekly_status
```

---

## 3. Sample contract (ops_reporting_workspace)

```yaml
# Schema version: 1.0
workflow: ops_reporting_workspace
manifest_file: workspace_manifest.json
required_manifest_keys:
  - workflow
  - timestamp
  - saved_artifact_paths
required_files:
  - workspace_manifest.json
  - source_snapshot.md
optional_files:
  - weekly_status.md
  - status_brief.md
  - action_register.md
  - stakeholder_update.md
  - decision_requests.md
description: Multi-artifact ops reporting workspace (M21S/A2).
```

---

## 4. Sample manifest (compliant)

```json
{
  "workflow": "ops_reporting_workspace",
  "timestamp": "2025-03-16T12:00:00.000000Z",
  "saved_artifact_paths": [
    "workspace_manifest.json",
    "source_snapshot.md",
    "weekly_status.md",
    "status_brief.md",
    "action_register.md",
    "stakeholder_update.md",
    "decision_requests.md"
  ],
  "grounding": "task_context_only",
  "input_sources_used": [],
  "retrieval_used": false,
  "retrieval_relevance_weak_or_mixed": false
}
```

Downstream consumers can rely on: (1) `workflow` and `timestamp` and `saved_artifact_paths` present, (2) `workspace_manifest.json` and `source_snapshot.md` on disk, (3) any of the optional `.md` files if listed in `saved_artifact_paths`.

---

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python -m pytest tests/test_release.py -v --tb=short -k "export_contract or validate_workspace_export or review_validate"
```

Or by name:
```bash
python -m pytest tests/test_release.py::test_get_export_contract tests/test_release.py::test_validate_workspace_export_valid tests/test_release.py::test_validate_workspace_export_missing_required tests/test_release.py::test_validate_workspace_export_missing_manifest_key tests/test_release.py::test_review_validate_workspace_cli -v --tb=short
```

---

## 6. Downstream handoff

- **Package builder** (`release/package_builder.py`): Can call `validate_workspace_export(ws)` before building; fail fast if contract not met.
- **Apply / review**: Use `get_export_contract(inv["workflow"])` to know required/optional files when listing or copying.
- **Schema version**: Bump `WORKSPACE_EXPORT_SCHEMA_VERSION` when making breaking changes to required keys or file set; downstream can check `contract_version` in validation result.
