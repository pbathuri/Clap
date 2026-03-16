# M22E-F2 — Template Versioning + Template Validation Reports — READ FIRST

Inspection and plan before implementation. No code until this is complete.

---

## 1. Current state of the template system

### 1.1 Template registry and schema (M22E base)

- **Location:** `src/workflow_dataset/templates/registry.py`
- **Data:** Templates stored as YAML/JSON under `data/local/templates/` (e.g. `ops_reporting_core.yaml`, `weekly_plus_stakeholder.yaml`).
- **Loaded fields:** `id`, `name`, `description`, `workflow_id`, `artifacts` (list of artifact keys), optional `wording_hints`. No `version`, `deprecated`, or `compatibility_note`.
- **Constants:** `VALID_WORKFLOW_IDS`, `WORKFLOW_ARTIFACTS` (allowed artifact keys per workflow), `ARTIFACT_TO_FILENAME` (key → filename).
- **API:** `load_template(id, repo_root)`, `get_template(id, repo_root)`, `list_templates(repo_root)`, `template_artifact_order_and_filenames(template)`.
- **Behavior:** `load_template` normalizes `workflow_id` (default `ops_reporting_workspace`, fallback to it if invalid) and filters `artifacts` to allowed set for that workflow. Raises `FileNotFoundError` if file missing.

### 1.2 CLI surface

- **`workflow-dataset templates list`** — Lists templates (id, name, workflow_id, artifacts, description). No status column.
- **`workflow-dataset templates show --id <id>`** — Prints template definition; no validation or report.
- **`workflow-dataset release demo --template <id> [--save-artifact] ...`** — Loads template, sets `workflow` from `template_def["workflow_id"]`; for `ops_reporting_workspace` save, uses `template_artifact_order_and_filenames` to build `artifacts_dict` and write workspace.

### 1.3 Workflow and export contracts (reuse)

- **Workflows:** `reporting_workspaces.REPORTING_WORKFLOWS` and registry `VALID_WORKFLOW_IDS` both list: weekly_status, status_action_bundle, stakeholder_update_bundle, meeting_brief_bundle, ops_reporting_workspace.
- **Export contracts:** `workspace_export_contract.EXPORT_CONTRACTS` defines per-workflow: `manifest_file`, `required_manifest_keys`, `required_files`, `optional_files`, `required_at_least_one_of`; `get_export_contract(workflow)`, `validate_workspace_export(workspace_path)`.
- **No template-specific tests** under `tests/` for templates (no test_workflow_templates or template tests in test_release).

### 1.4 Summary

Templates are **present and used**: list, show, and release demo --template work. There is **no version metadata**, **no validate/report commands**, **no compatibility status**, and **no migration hints**.

---

## 2. Exact reuse map (for F2)

| Piece | Where | Reuse for F2 |
|-------|--------|----------------|
| Workflow id set | `templates.registry.VALID_WORKFLOW_IDS` | Validation: required workflow reference must be in this set. |
| Artifact sets per workflow | `templates.registry.WORKFLOW_ARTIFACTS`, `ARTIFACT_TO_FILENAME` | Validation: referenced artifacts must be in allowed set; ordering uses same map. |
| Export contract per workflow | `workspace_export_contract.get_export_contract`, `EXPORT_CONTRACTS` | Validation report: template’s workflow’s required/optional files vs template’s artifacts; compatibility note. |
| Workspace export validation | `workspace_export_contract.validate_workspace_export` | Not applied to template file itself; used for saved workspace. Template validation checks **contract compatibility** (template artifacts ⊆ contract’s required+optional). |
| Template load/list | `templates.registry.load_template`, `list_templates` | Validate/report load template by id; list --show-status adds status per template. |
| Save behavior | CLI `release_demo` + `template_artifact_order_and_filenames` | Validation: “save behavior valid” = template’s workflow has a save path and artifact list is consistent with that workflow. |

---

## 3. Exact gap (what F2 adds)

| Gap | F2 addition |
|-----|--------------|
| No version metadata | Add to template schema: `version` (e.g. "1.0"), optional `compatibility_note`, optional `deprecated` (bool). Keep backward compatible: missing version = treat as unversioned but still loadable. |
| No template validation | `templates validate --id <id>`: run validation checks; exit 0 if valid (or valid_with_warning), non-zero if deprecated/invalid. |
| No validation report | `templates report --id <id>`: generate a clear report (required workflow exists, artifacts valid, ordering legal, save behavior valid, compatibility with export contract). |
| No compatibility status | Statuses: **valid**, **valid_with_warning**, **deprecated**, **invalid**. Computed from validation result + deprecated flag. |
| No migration hints | Optional `migration_hints` in report (and/or in template YAML): e.g. "replace artifact X with Y", "use workflow Z instead of A". Advisory only; no auto-rewrite. |
| list does not show status | `templates list --show-status`: add a status column (valid / valid_with_warning / deprecated / invalid). |

---

## 4. File plan

| Item | Action | Path / content |
|------|--------|----------------|
| **Template schema (versioning)** | Extend | `templates/registry.py` or keep schema in one place: accept and pass through `version`, `compatibility_note`, `deprecated` in loaded dict. Defaults: version=None, deprecated=False, compatibility_note=None. |
| **Validation + report** | New | `templates/validation.py`: `validate_template(template_dict \| id, repo_root?) -> dict` (errors, warnings, status, checks); `template_validation_report(template_dict \| id, repo_root?) -> str` or structured dict for CLI to print. Checks: (1) workflow_id in VALID_WORKFLOW_IDS, (2) every artifact in WORKFLOW_ARTIFACTS[workflow_id], (3) artifact order legal (no constraint beyond “subset of allowed”), (4) save behavior: workflow has save path (all current do), (5) export contract: template artifacts ⊆ contract required_files + optional_files (or required_at_least_one_of). Migration hints: optional list from template or derived (e.g. if deprecated, hint to use X). |
| **Status + migration** | In validation | Status = invalid if errors; else deprecated if template deprecated=True; else valid_with_warning if warnings; else valid. Migration hints: from template key `migration_hints` (list of strings) and optionally one auto-hint when deprecated. |
| **CLI** | Modify | `cli.py`: add `templates validate --id <id>`, `templates report --id <id>`, extend `templates list` with `--show-status`. |
| **Tests** | New | `tests/test_templates.py` or extend `test_release.py`: test validate (valid template, invalid workflow, invalid artifact, deprecated), report output shape, list --show-status. |
| **Docs** | New/update | `docs/M22E_F2_TEMPLATE_VERSIONING_READ_FIRST.md` (this file). After implementation: add “M22E-F2 delivery” section or short doc with CLI usage, sample report, sample deprecated/invalid output. |

**New file:** `src/workflow_dataset/templates/validation.py`  
**Modified:** `src/workflow_dataset/templates/registry.py` (schema defaults for version, deprecated, compatibility_note), `src/workflow_dataset/cli.py` (validate, report, list --show-status), `src/workflow_dataset/templates/__init__.py` (export validate/report if desired).  
**Optional:** Add `version`, `compatibility_note`, `deprecated`, `migration_hints` to existing YAML templates for examples.

---

## 5. Constraints (recap)

- Do not break existing template execution (`release demo --template` unchanged behavior).
- No auto-rewrite of templates; migration hints are advisory only.
- Do not broaden beyond ops/reporting family; use existing VALID_WORKFLOW_IDS and export contracts only.
- Keep validation explicit and inspectable (report human-readable).
- Preserve backward compatibility: templates without version/deprecated still load and run; validation treats missing version as unversioned.
