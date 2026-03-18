# M22E — Workflow Composer + Template Studio — READ FIRST (no code yet)

This document is the **inspection and plan** required before implementation. It covers: current repo state for this track, exact reuse map, exact gap, file plan, and collision-risk for shared files.

---

## 1. Current repo state for this track

### 1.1 Validated workflows (source of truth)

- **weekly_status** — Single artifact: `weekly_status.md` + `manifest.json` under `data/local/workspaces/weekly_status/{ts}_{id}/`.
- **status_action_bundle** — Two artifacts: `status_brief.md`, `action_register.md` + `manifest.json` under `data/local/workspaces/status_action_bundle/`.
- **stakeholder_update_bundle** — Two artifacts: `stakeholder_update.md`, `decision_requests.md` + `manifest.json` under `data/local/workspaces/stakeholder_update_bundle/`.
- **meeting_brief_bundle** — Two artifacts: `meeting_brief.md`, `action_items.md` + `manifest.json` under `data/local/workspaces/meeting_brief_bundle/`.
- **ops_reporting_workspace** — Multi-artifact: `workspace_manifest.json`, `source_snapshot.md`, plus optional `weekly_status.md`, `status_brief.md`, `action_register.md`, `stakeholder_update.md`, `decision_requests.md` under `data/local/workspaces/ops_reporting_workspace/{ts}_{id}/`.

All are driven by a single CLI entrypoint: `release demo --workflow <name> [--context-file ...] [--context-text ...] [--input-pack ...] [--retrieval] [--rerun-from ...] --save-artifact`.

### 1.2 Where workflow logic lives

- **`src/workflow_dataset/cli.py`** — `release_demo()` (around lines 3432–4025):
  - `workflow_type` is derived from `--workflow` (default `weekly_status`); allowed values: `status_action_bundle`, `stakeholder_update_bundle`, `meeting_brief_bundle`, `ops_reporting_workspace`; else falls back to `weekly_status`.
  - For each workflow type there is a **hardcoded block**: `prompts` (list of prompt strings), `prompt_kinds` (list of kinds for instructions), and a **save block** (nested under `if save_artifact and workflow_type == "..."`) that builds dir path, writes .md files, builds manifest, calls `record_workflow_artifact`. For `ops_reporting_workspace`, the save block imports `save_ops_reporting_workspace` from `release.workspace_save` and calls it with an artifacts dict and manifest.
  - No shared “workflow definition” structure; workflow surface area is **ad hoc** (if/elif chain).

### 1.3 Release module (current files)

| File | Purpose |
|------|--------|
| `reporting_workspaces.py` | `REPORTING_WORKFLOWS` tuple; `get_workspace_inventory()`, `list_reporting_workspaces()`; loads `workspace_manifest.json` or `manifest.json`. |
| `workspace_export_contract.py` | `WORKSPACE_EXPORT_SCHEMA_VERSION`, `EXPORT_CONTRACTS` per workflow (manifest_file, required_manifest_keys, required_files, optional_files, required_at_least_one_of); `get_export_contract()`, `validate_workspace_export()`. |
| `workspace_rerun_diff.py` | `infer_rerun_args(manifest)`, `diff_workspaces()`, `workspace_timeline()`. |
| `package_builder.py` | `build_package(workspace_path, ...)` — copies approved artifacts to `data/local/packages/{ts}_{id}/`; uses `get_workspace_inventory`, `get_approved_artifacts`, `load_review_state`. |
| `review_state.py` | Per-workspace review state (approved/needs_revision/excluded); `load_review_state`, `save_review_state`, `set_artifact_state`, `get_approved_artifacts`. |
| `dashboard_data.py` | Read-only dashboard aggregation (workspaces, packages, pilot, cohort); uses `list_reporting_workspaces`, `get_workspace_inventory`, `load_review_state`. |

**Note:** In this branch, `workspace_save.py`, `input_packs.py`, and `artifact_schema.py` are **not present** (glob search returned 0). The CLI and tests reference them; if they exist elsewhere or get re-added, they should be reused as in the implementation summary. For M22E we only **invoke** existing workflow entrypoints (e.g. pass `--workflow` or equivalent); we do not depend on those three files for the **template** layer itself.

### 1.4 Pilot

- `pilot_group` exists in CLI (`app.add_typer(pilot_group, name="pilot")`). Pilot commands (verify, start-session, end-session, capture-feedback, aggregate, etc.) and `record_workflow_artifact` are the validated pilot/cohort surface. Template runs should continue to use the same artifact recording when saving (so sessions/cohort stay workflow-aware).

### 1.5 Materialize

- No `materialize` package under `src/workflow_dataset/` in the listed structure; only `release`, `devlab`, `eval`, `intake`, `ui`, `mission_control`, etc. Materialize is **out of scope** for M22E unless we discover a materialize path used by release/demo.

### 1.6 Other registries

- **intake** (`intake/registry.py`): Label-based registration of **input path sets** and snapshots under `data/local/intake/`; `registry.json` with `sets`; `add_intake`, `get_intake`. This is **input** registration, not workflow composition. We do not extend it for templates; we add a separate template store.
- **packs** (`packs_group` in CLI): Capability/role packs (install, activate, pin, conflicts). Used for **runtime role** (e.g. ops), not for defining which artifacts a workflow generates. We do **not** extend packs for M22E.
- **devlab**: Own registry for candidate repos; not workflow composition.

### 1.7 Data layout

- Workspaces: `data/local/workspaces/<workflow_name>/{ts}_{id}/` with workflow-specific manifest and .md files.
- Packages: `data/local/packages/{ts}_{id}/` (from `review build-package`).
- Pilot: `data/local/pilot` (sessions, feedback, readiness).
- Review state: `data/local/review/<workflow>/<run_id>.json`.

---

## 2. Exact reuse map

| Piece | Where | Reuse for M22E |
|-------|--------|-----------------|
| Workflow list / contracts | `reporting_workspaces.REPORTING_WORKFLOWS`, `workspace_export_contract.EXPORT_CONTRACTS` | Template “target workflow family” and artifact names must stay within these workflows; use export contract for “required/optional files” when defining template artifact sets. |
| Run one workflow | `cli.release_demo` with `--workflow <name>` | Template **run** = invoke existing entrypoint (e.g. subprocess or internal call) with workflow set from template; no reimplementation of prompts/save. |
| Save to sandbox | Per-workflow save blocks in `release_demo`; `workspace_save.save_ops_reporting_workspace` for ops_reporting_workspace (when present) | Template-based save = same flows; template only **selects** which workflow(s) to run and optionally **names/orders** outputs; save paths remain `data/local/workspaces/<workflow>/` or one composed dir if we add a “template run” workspace root. |
| Workspace discovery | `list_reporting_workspaces`, `get_workspace_inventory` | List/show template-run workspaces unchanged. |
| Export validation | `validate_workspace_export` | After a template run, optionally validate the saved workspace against the workflow’s export contract. |
| Pilot artifact recording | `record_workflow_artifact(workflow_id, dir_path, pilot_dir)` | Keep calling for template-driven runs so cohort/session stays consistent. |
| Intake registry pattern | `intake/registry.py`: load/save JSON under a root dir, list/get by id | **Pattern only**: template registry = local JSON (or one file per template) under e.g. `data/local/workflow_templates/`; list templates, get template by id, validate schema. Do not mix intake data with template data. |

---

## 3. Exact gap

- **No declarative workflow template.** Today, “which artifacts a workflow generates” and “in what order” are fixed in code (if/elif and save blocks). There is no local, inspectable definition that says “this template produces weekly_status + stakeholder_update” or “this template is ops_reporting_core with these artifact names/order.”
- **No template registry.** No list/show/validate/run for “templates”; only `--workflow` for a fixed set of workflow ids.
- **No composer layer.** Operators cannot define a reusable “suite” (e.g. status_plus_actions = status_brief + action_register + decision_requests) without it being a new hardcoded workflow in cli.py.
- **Artifact ordering/naming** are implicit in each workflow’s save block; not driven by a template (e.g. optional naming hints or ordering list).

Filling the gap means: **add a narrow template layer** that (1) defines templates (id, description, target workflow family, artifacts to generate, ordering, optional naming/style hints, save default), (2) provides list/show/validate/run against **current** workflow entrypoints, (3) saves template-run outputs into a **coherent** sandbox (reusing existing save flows), and (4) keeps existing `release demo --workflow X` behavior unchanged.

---

## 4. File plan

| Module | Action | Path / content |
|--------|--------|----------------|
| **A — Reuse map / design** | Doc only | Already in this file (§2). Optional: short `docs/M22E_TEMPLATE_DESIGN.md` with template JSON/YAML schema draft. |
| **B — Template schema / parser / validator** | New | `src/workflow_dataset/release/workflow_templates.py` (or `release/templates/` if preferred): template schema (id, description, target_workflow_family, input_expectations, artifacts_to_generate, artifact_ordering, optional naming_hints, wording_hints, save_artifact_default); load from JSON or YAML; `validate_template(template_dict) -> {valid, errors}`. Repo uses YAML elsewhere (configs); use **YAML** for template files to stay consistent with configs, and JSON for in-memory/registry index if needed. |
| **C — Template registry and list/show** | New | Same module or `release/template_registry.py`: registry root `data/local/workflow_templates/`; `list_templates(repo_root) -> list[dict]`, `get_template(template_id, repo_root) -> dict | None`, `validate_template_file(path)`. Templates stored as files e.g. `data/local/workflow_templates/ops_reporting_core.yaml`; optional `registry.json` index for list (or scan dir). |
| **D — Template runner** | New | `release/template_runner.py`: `run_template(template_id, repo_root, *, context_file, context_text, input_pack, retrieval, save_artifact)` that (1) loads template, (2) validates, (3) maps template to **one** current workflow id (template defines “target workflow” or “workflow_suite” that maps to a single release_demo workflow), (4) invokes the existing release demo flow with that workflow and options. No recursive composition: one template → one workflow run. If we later support “multi-step” (e.g. run workflow A then B), that is a separate, explicit step list in the template and runner runs them in order, each calling the same entrypoint; **no** dynamic chains. |
| **E — Sandbox save integration** | Reuse | Template runner passes through `--save-artifact` and existing save blocks write to `data/local/workspaces/<workflow>/`. Optionally: when template has a “workspace_label” or “run_label”, create a subdir or a single composed workspace dir (e.g. `data/local/workspaces/template_runs/<template_id>/{ts}_{id}/`) that contains the same artifact set — **only** if we can do that without duplicating save logic (e.g. copy/move from workflow-specific dirs into one dir, or call a shared writer). Prefer reusing current per-workflow save paths so export contracts and review keep working. |
| **F — CLI** | Modify | `cli.py`: new commands under **release** or a new **composer** Typer (prefer **release** to avoid extra top-level group): `release template list`, `release template show <id>`, `release template validate <id>`, `release template run <id> [--context-file ...] [--context-text ...] [--input-pack ...] [--retrieval] [--save-artifact]`. No removal or change of `release demo --workflow ...`. |
| **F — Tests** | New | `tests/test_release.py` or `tests/test_workflow_templates.py`: test template load/validate, list/get, run_template invokes release_demo with correct workflow and saves to sandbox; test that `release demo --workflow weekly_status` still works. |
| **F — Docs** | New | `docs/M22E_WORKFLOW_COMPOSER_DELIVERY.md` (after implementation): files changed, CLI usage, sample template, sample workspace tree, tests run, remaining weaknesses. |

**Summary of new files**

- `src/workflow_dataset/release/workflow_templates.py` — schema, load, validate (and optionally `template_registry.py` if split).
- `src/workflow_dataset/release/template_runner.py` — run_template using current workflow entrypoint.
- `data/local/workflow_templates/` — directory for YAML templates (e.g. `ops_reporting_core.yaml`, `stakeholder_bundle.yaml`).
- Optional: `data/local/workflow_templates/registry.json` — index for list (or derive list from dir scan).

**Modified files**

- `src/workflow_dataset/cli.py` — add `release template list|show|validate|run` (or `release composer ...`). No change to `release_demo` signature or behavior for direct `--workflow` usage.

---

## 5. Collision-risk note for shared files (e.g. `cli.py`)

- **cli.py**
  - **Risk:** Large file; many groups and commands; any new command must be added in one place and can conflict with existing option names or argument positions.
  - **Mitigation:** Add only **new** commands under `release_group`: `release template list`, `release template show <id>`, `release template validate <id>`, `release template run <id>` with options that mirror `release demo` (context-file, context-text, input-pack, retrieval, save-artifact). Do **not** change `release_demo`’s signature or the existing `--workflow` handling. Use a **subgroup** (e.g. `template_group = typer.Typer()` then `release_group.add_typer(template_group, name="template")`) so that `release template ...` is clearly namespaced and does not collide with `release demo`, `release verify`, etc.
  - **Naming:** Avoid `release run` (could be confused with `release run` for trials). Using `release template run` is clear.

- **release/reporting_workspaces.py**
  - **Risk:** Adding a new “workflow” id that is template-based could require listing template-run workspaces. Current code iterates over `REPORTING_WORKFLOWS` and then run dirs. If we store template runs under e.g. `data/local/workspaces/template_runs/` or under a single workflow id like `template_ops_reporting_core`, we might add that to `REPORTING_WORKFLOWS` or handle it in `list_reporting_workspaces` so they appear in review/dashboard. Low risk if we keep saving under existing workflow ids (e.g. template “ops_reporting_core” → run `release demo --workflow ops_reporting_workspace`); then no change to reporting_workspaces needed.

- **release/workspace_export_contract.py**
  - **Risk:** Adding new “workflow” keys to `EXPORT_CONTRACTS` for every template would bloat. Prefer: templates reference **existing** workflow ids; export contract stays as-is; template-run output is validated with the same contract as that workflow.

- **tests/test_release.py**
  - **Risk:** Many tests already; new tests for template list/show/validate/run must not break existing release or review tests. Add isolated tests (template load, validate, run_template mocks or small integration) and keep existing test names and behavior.

---

## 6. Implementation order (recap)

- **Module A** — Workflow reuse map and template design (this doc + optional M22E_TEMPLATE_DESIGN.md).
- **Module B** — Template schema/parser/validator in `release/workflow_templates.py`.
- **Module C** — Template registry: list/show/validate from `data/local/workflow_templates/`.
- **Module D** — Template runner: run template → call existing release demo flow with chosen workflow.
- **Module E** — Sandbox save: reuse current flows; optional single composed dir only if feasible without duplication.
- **Module F** — CLI (release template *), tests, docs.

No coding until this READ FIRST is complete. Implementation can start from Module B after approval of this plan.
