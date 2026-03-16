# M22E-F6 — Template Runs in Cohort/Workspace Flows + Reporting Hooks: READ FIRST

## 1. Current state

- **Workspace manifest** (ops_reporting_workspace): Built in `cli.py` release_demo and passed to `save_ops_reporting_workspace`. Already includes `template_id`, `template_params`. Written as `workspace_manifest.json` in each run dir.
- **reporting_workspaces**: `get_workspace_inventory(workspace_path)` loads manifest and returns `workflow`, `artifacts`, `timestamp`, `grounding`, `manifest`, `mtime`. Full manifest is in `inv["manifest"]` but template fields are not first-class on inv.
- **dashboard_data**: `get_dashboard_data()` uses `list_reporting_workspaces`; each item has `workspace_path`, `workflow`, `timestamp`, `grounding`, `artifact_count`, etc. No template_id in recent_workspaces display.
- **package_builder**: Builds `package_manifest.json` from workspace; has `workflow`, `grounding`, `source_workspace`. Does not copy template_id/template_version from workspace manifest.
- **Pilot**: `PilotSessionRecord` has `extra: dict`; `session_log` has no `record_workflow_artifact` (referenced by cli but not defined in session_log). Sessions list/summaries do not surface template.

## 2. Reuse

- `get_workspace_inventory`, `list_reporting_workspaces`, `get_dashboard_data`, `build_package`, `load_session`/`save_session`, `PilotSessionRecord.to_dict`/`from_dict` (extra preserved).

## 3. What F6 adds

1. **Manifest**: Add `template_version` to ws_manifest when template_def present (id + params already there).
2. **Inventory**: In `get_workspace_inventory`, add `template_id`, `template_version` from manifest to returned inv so listings/reports can show them without parsing manifest.
3. **Dashboard**: In `get_dashboard_data`, add `template_id` (and optionally `template_version`) to each recent_workspaces entry from inv.
4. **Package**: In `build_package`, copy `template_id`, `template_version` from workspace manifest into package_manifest when present.
5. **Pilot**: Add `record_workflow_artifact(workflow_type, dir_path, pilot_dir, template_id=None)` in session_log; store artifact path in session and template_id in extra. Surface template in session summaries/cohort when present.
6. **Usage**: `workflow-dataset templates usage` — scan workspaces (and optionally sessions), aggregate by template_id, print most-used and recent template-driven runs.

## 4. What not to change

- Workflow execution or safety model. No new apply/cloud paths. Existing manifest keys and validation unchanged except additive template fields.

## 5. File plan

| Module | File(s) | Action |
|--------|---------|--------|
| A | docs/M22E_F6_READ_FIRST.md | This file. |
| B | cli.py | Add template_version to ws_manifest. |
| B | release/reporting_workspaces.py | get_workspace_inventory: add template_id, template_version from manifest to inv. |
| B | release/dashboard_data.py | recent_workspaces: add template_id, template_version from inv. |
| B | release/package_builder.py | package_manifest: add template_id, template_version from inv["manifest"]. |
| C | pilot/session_models.py | No change; extra already holds arbitrary keys. |
| C | pilot/session_log.py | Add record_workflow_artifact(workflow_type, dir_path, pilot_dir, template_id=None). |
| C | cli.py | Call record_workflow_artifact for ops_reporting_workspace with template_id; pass template_id where supported. |
| C | pilot/aggregate.py | session_summaries: include template_id from s.extra.get("template_id") when present. |
| D | templates/usage.py (new) or registry | template_usage_summary(workspaces_root, limit) -> counts + recent runs. |
| D | cli.py | templates usage command. |
| E | tests/test_templates.py or test_release.py | Tests for inventory template fields, usage summary. |
| E | docs/M22E_F6_DELIVERY.md | Samples and commands. |

## 6. Risk note

- All changes are additive and local. Template fields are optional; old manifests without them remain valid. record_workflow_artifact is new; existing callers that don’t pass template_id get backward behavior.
