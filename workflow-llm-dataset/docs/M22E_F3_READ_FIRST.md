# M22E-F3 — Template Import/Export + Typed Parameters: READ FIRST

## 1. Current state

- **Registry** (`templates/registry.py`): `load_template(id)`, `list_templates()`, `template_artifact_order_and_filenames(template)`. Templates on disk: `data/local/templates/<id>.yaml` or `.json`. Schema: id, name, description, workflow_id, artifacts, wording_hints, version, deprecated, compatibility_note, migration_hints (F2).
- **Validation** (`templates/validation.py`): `validate_template(template_id_or_dict)`, `template_validation_report()`, `get_template_status()`. Checks: workflow exists, artifacts valid, ordering, save behavior, export contract.
- **CLI**: `templates list` (--show-status), `templates show --id`, `templates validate --id`, `templates report --id`; `release demo --template <id> --save-artifact` loads template and uses workflow_id + artifact order when saving ops_reporting_workspace.
- **No export/import**, no **parameters** schema, no **--param** on release demo.

## 2. Reuse

- `load_template`, `validate_template`, `list_templates`, `template_artifact_order_and_filenames` — reuse as-is.
- Validation before import: call `validate_template(imported_dict)` and fail import if invalid.
- Registry `_templates_path`, `_safe_id`, `VALID_WORKFLOW_IDS`, `WORKFLOW_ARTIFACTS`, `ARTIFACT_TO_FILENAME` — reuse for export payload and import target path.
- Release demo: extend to accept `--param key=value`; validate params against template’s `parameters` when template is used.

## 3. What F3 adds

1. **Export** — Serialize a registered template to a local file (e.g. `.tmpl.json`). Include: id, version, description, workflow_id, artifacts, versioning fields, compatibility metadata, and `parameters` if present. CLI: `templates export --id X --out path`.
2. **Import** — Load from file, validate, then write to `data/local/templates/<id>.yaml` (or .json). Collision: reject unless `--overwrite` or `--as-id <new_id>`. CLI: `templates import --file path [--overwrite] [--as-id Y]`.
3. **Typed parameters** — Template schema may include `parameters: [{name, type, required, default, description}]`. Types: string, integer, boolean, choice (with choices list). Normalize in `load_template`; validate at runtime.
4. **Parameter substitution** — Use resolved params for: optional run dir suffix (e.g. from `label` or `run_prefix`), and store `template_params` in workspace manifest. No arbitrary code or hidden templating.
5. **Runtime --param** — `release demo --template X --param owner=Alex --param label=sprint_12 --save-artifact`. Parse `--param k=v`, validate against template parameters, then pass to save/manifest.

## 4. What not to change

- Existing template YAML/JSON schema beyond adding optional `parameters`.
- Validation checks (workflow, artifacts, export contract) or status values.
- Behavior of `release demo` when `--template` is not set.
- Other CLI groups or unrelated commands.

## 5. File plan

| Module | File(s) | Action |
|--------|---------|--------|
| A | docs/M22E_F3_READ_FIRST.md | This file. |
| B | templates/registry.py | Add `export_template(template_id, out_path, repo_root)` → write .tmpl.json. |
| B | cli.py | Add `templates export --id X --out path`. |
| C | templates/registry.py or templates/io.py | Add `import_template_from_file(path, overwrite, as_id, repo_root)` → validate then write to templates dir. |
| C | cli.py | Add `templates import --file path [--overwrite] [--as-id Y]`. |
| D | templates/registry.py | In `load_template`, normalize `parameters` list (name, type, required, default, description); add `validate_template_parameters(template, params_dict)`. |
| D | templates/parameters.py (new) | `validate_template_parameters(template, params)`, `parse_param_string("k=v")`, types: string, integer, boolean, choice. |
| E | cli.py | release demo: add `param: list[str] = Option([], "--param")`; parse to dict; if template loaded, validate and pass to manifest / optional dir suffix. |
| E | release/artifact_schema or workspace_save | Accept optional `template_params` in manifest; optional run dir suffix from param (e.g. label). |
| F | tests/test_templates.py | Tests for export, import (valid/invalid/overwrite), parameter validation, release demo --param (help or minimal run). |
| F | docs/M22E_F3_*.md | Sample exported file, import result, parameterized run. |

## 6. Risk note

- **Import overwrite**: Explicit flag only; default reject on id collision.
- **Parameters**: Allowlist of types; no eval or user code. Substitution only in manifest and optional naming; no injection into artifact content except via explicit future fields (e.g. owner in manifest).
- **release demo**: Adding `--param` is additive; existing invocations unchanged. If template has no `parameters`, any --param can be ignored or stored as extra metadata only.
