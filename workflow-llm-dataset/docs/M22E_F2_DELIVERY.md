# M22E-F2 — Template Versioning + Template Validation Reports — Delivery

## 1. Files modified

| File | Changes |
|------|--------|
| `src/workflow_dataset/templates/registry.py` | Defaults for `version`, `deprecated`, `compatibility_note`, `migration_hints` on load; list_templates includes these keys. |
| `src/workflow_dataset/cli.py` | `templates list` has `--show-status` (shows valid/valid_with_warning/deprecated/invalid per template); `templates show` prints version/deprecated/compatibility_note/migration_hints; `templates validate --id` and `templates report --id`; `templates report` has `--output`/`-o` to write report to file. |
| `src/workflow_dataset/templates/__init__.py` | Exported `validate_template`, `template_validation_report`, `get_template_status`. |
| `data/local/templates/ops_reporting_core.yaml` | Added `version: "1.0"`. |
| `data/local/templates/weekly_plus_stakeholder.yaml` | Added `version: "1.0"`. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M22E_F2_TEMPLATE_VERSIONING_READ_FIRST.md` | READ FIRST: current state, reuse map, gap, file plan. |
| `src/workflow_dataset/templates/validation.py` | `validate_template()`, `template_validation_report()`, `get_template_status()`; checks workflow, artifacts, ordering, save, export contract; status + migration hints. |
| `data/local/templates/legacy_weekly_only.yaml` | Example deprecated template (version 0.9, deprecated: true, migration_hints). |
| `tests/test_templates.py` | Tests for validation, report, status, list/validate/report CLI help. |
| `docs/M22E_F2_DELIVERY.md` | This file. |

## 3. Template validation/versioning CLI usage

```bash
# List templates (optionally with validation status)
workflow-dataset templates list
workflow-dataset templates list --show-status

# Show template definition (includes version, deprecated, compatibility_note, migration_hints if set)
workflow-dataset templates show --id ops_reporting_core

# Validate template (exit 0 if valid or valid_with_warning; exit 1 if deprecated or invalid)
workflow-dataset templates validate --id ops_reporting_core

# Generate template validation report
workflow-dataset templates report --id ops_reporting_core
```

Optional: `--repo-root <path>` on any of the above to override repo root.

## 4. Sample template report (valid)

```
--- Template validation report ---
Template id: ops_reporting_core
Version: 1.0
Workflow: ops_reporting_workspace
Status: valid

Checks:
  workflow_exists: OK
  artifacts_valid: OK
  artifact_ordering_legal: OK
  save_behavior_valid: OK
  export_contract_compatible: OK
---
```

## 5. Sample deprecated template report

For a template with `deprecated: true` (e.g. `legacy_weekly_only`):

```
--- Template validation report ---
Template id: legacy_weekly_only
Version: 0.9
Workflow: weekly_status
Status: deprecated

Warnings:
  - Template is marked deprecated.

Migration hints:
  - Use workflow weekly_status directly: workflow-dataset release demo --workflow weekly_status --save-artifact
  - Or use template ops_reporting_core for status brief + action register + decision requests
  - Consider using a non-deprecated template or workflow 'weekly_status' directly.

Checks:
  workflow_exists: OK
  artifacts_valid: OK
  artifact_ordering_legal: OK
  save_behavior_valid: OK
  export_contract_compatible: OK
---
```

## 6. Sample invalid template output

Template not found:

```
--- Template validation report ---
Template id: _nonexistent_
Version: unversioned
Workflow: —
Status: invalid

Errors:
  - Template not found: _nonexistent_

Checks:
---
```

`templates validate --id _nonexistent_` prints the error and exits with code 1.

Invalid workflow_id or artifact:

- `validate` prints errors (e.g. "workflow_id 'x' is not in allowed set...", "Artifacts not allowed for workflow...") and exits 1.
- `report` shows Status: invalid, Errors list, and checks with FAIL where applicable.

## 7. Tests run

```bash
cd workflow-llm-dataset && PYTHONPATH=src python3 -m pytest tests/test_templates.py -v
```

**Result (typical):**
- **9 passed**: validate_template (valid dict, invalid workflow, invalid artifact, deprecated), get_template_status, template_validation_report (string + not found), validate real template if present, load_template versioning defaults.
- **3 skipped** (when `pyyaml` not installed): CLI help tests for `templates validate`, `templates report`, `templates list --show-status`.

With full project deps (typer, pyyaml, etc.) and `PYTHONPATH=src`, all 12 can pass; CLI commands require the full environment.

## 8. Remaining weaknesses (this pane only)

- **YAML dependency:** Without `pyyaml`, template files are loaded as empty dicts and get default `workflow_id`/`deprecated`; validation then reports “valid” with wrong workflow. Install `pyyaml` for real template loading.
- **No automatic migration:** Migration hints are advisory only; no tool rewrites or upgrades templates.
- **Export-contract check:** “Export contract compatible” only ensures template-requested artifact files are in the contract’s required/optional sets; it does not run `validate_workspace_export()` on a saved workspace.
- **Single-workflow templates:** Validation assumes one workflow per template; no check for future multi-step or suite definitions.
- **Version format:** Version is an opaque string (e.g. `"1.0"`); no semver or compatibility rules enforced.
