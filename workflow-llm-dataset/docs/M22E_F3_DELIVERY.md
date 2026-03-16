# M22E-F3 — Template Import/Export + Typed Parameters: Delivery

## 1. Files modified

- `src/workflow_dataset/templates/registry.py` — Normalize `parameters` list in `load_template` (ensure list of dicts).
- `tests/test_templates.py` — Added `test_resolve_template_params_defaults_filled`.

## 2. Files created

- (None this step; export/import and parameters were added in prior steps.)
- This doc: `docs/M22E_F3_DELIVERY.md`.

## 3. Import / Export / Param CLI usage

```bash
# Export a registered template to a local file
workflow-dataset templates export --id ops_reporting_core --out ./ops_reporting_core.tmpl.json
workflow-dataset templates export --id ops_reporting_core --out ./out.tmpl.yaml --format yaml

# Import from file (validates before registration)
workflow-dataset templates import --file ./ops_reporting_core.tmpl.json
workflow-dataset templates import --file ./ops_reporting_core.tmpl.json --overwrite
workflow-dataset templates import --file ./ops_reporting_core.tmpl.json --id my_local_copy

# Run release demo with template and typed parameters
workflow-dataset release demo --template ops_reporting_core --param owner=Alex --param label=sprint_12 --save-artifact
```

## 4. Sample exported template file (`.tmpl.json`)

```json
{
  "id": "ops_reporting_core",
  "version": "1.0",
  "name": "Ops reporting core",
  "description": "Core ops reporting workspace template",
  "workflow_id": "ops_reporting_workspace",
  "artifacts": [
    "weekly_status",
    "status_brief",
    "action_register",
    "stakeholder_update",
    "decision_requests"
  ],
  "parameters": [
    {
      "name": "owner",
      "type": "string",
      "required": false,
      "default": null,
      "description": "Owner or team label"
    },
    {
      "name": "label",
      "type": "string",
      "required": false,
      "default": "default",
      "description": "Run label for artifact naming"
    }
  ],
  "deprecated": false,
  "compatibility_note": null,
  "migration_hints": []
}
```

## 5. Sample import validation result

**Success:**

- `workflow-dataset templates import --file ./ops_reporting_core.tmpl.json`  
  → Output: `Imported: ops_reporting_core` and path to `data/local/templates/ops_reporting_core.yaml`.
- Validation runs before registration; invalid templates raise `ValueError` and are not written.

**Failure (invalid workflow):**

- File content: `{"id": "bad", "workflow_id": "nonexistent_workflow", "artifacts": []}`  
  → `ValueError: Template validation failed: ...` (exit 1). Template not written.

**Collision (id already exists):**

- `workflow-dataset templates import --file ./ops_reporting_core.tmpl.json` when `ops_reporting_core` already exists  
  → `FileExistsError: Template already exists: ops_reporting_core. Use --overwrite to replace.`  
  → Use `--overwrite` to replace or `--id other_id` to import under a new id.

## 6. Sample parameterized run

```bash
workflow-dataset release demo --template ops_reporting_core --param owner=Alex --param label=sprint_12 --save-artifact
```

- Template is loaded; `--param` is parsed and validated against the template’s `parameters`.
- Resolved params are stored in the workspace manifest as `template_params` (e.g. `{"owner": "Alex", "label": "sprint_12"}`).
- If the template has no `parameters`, passing `--param` causes an error. If parameters are defined, unknown keys or type errors cause validation to fail before execution.

## 7. Tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_templates.py -v
```

Result: **19 passed, 3 skipped** (skips: CLI help tests when PyYAML not installed).

Included: validation, versioning, export/import roundtrip, import invalid/collision, `resolve_template_params` (ok, unknown param, no params, defaults filled), parameter schema validation (valid, invalid type).

## 8. Remaining weaknesses (this pane only)

- **Run dir suffix**: `template_params` are in the manifest; optional use of a param (e.g. `label`) for run directory suffix is not implemented in `workspace_save`; can be added later if desired.
- **Content substitution**: No substitution of params into artifact content (e.g. owner in body); only manifest and future run-dir use are in scope.
- **Export format**: Import currently writes to `.yaml` only; export can produce JSON or YAML. Consistency (e.g. writing `.json` when source was `.tmpl.json`) could be refined.
- **CLI export error handling**: Export command does not currently catch `FileNotFoundError` for missing template in all code paths; behavior is consistent but could be made more explicit.
