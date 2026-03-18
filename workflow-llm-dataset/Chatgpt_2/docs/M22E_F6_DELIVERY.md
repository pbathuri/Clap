# M22E-F6 — Template Runs in Cohort/Workspace Flows + Reporting Hooks: Delivery

## 1. Files modified

- `src/workflow_dataset/cli.py` — Added `template_version` to ws_manifest; call `record_workflow_artifact` for ops_reporting_workspace with `template_id`; added `templates usage` command.
- `src/workflow_dataset/release/reporting_workspaces.py` — `get_workspace_inventory` now includes `template_id` and `template_version` from manifest.
- `src/workflow_dataset/release/dashboard_data.py` — `recent_workspaces` entries now include `template_id` and `template_version`.
- `src/workflow_dataset/release/package_builder.py` — `package_manifest` now copies `template_id` and `template_version` from workspace manifest when present.
- `src/workflow_dataset/pilot/session_log.py` — Added `record_workflow_artifact(workflow_type, dir_path, pilot_dir, template_id=None)`.
- `src/workflow_dataset/pilot/aggregate.py` — `session_summaries` now include `template_id` from `s.extra.get("template_id")` when present.
- `tests/test_review_queue.py` — Added `test_get_workspace_inventory_includes_template_fields`.
- `tests/test_templates.py` — Added `test_template_usage_summary_empty`, `test_template_usage_summary_with_template_runs`.
- `tests/test_pilot.py` — Added `test_record_workflow_artifact_stores_template_id`.

## 2. Files created

- `src/workflow_dataset/templates/usage.py` — `template_usage_summary(workspaces_root, repo_root, limit)`.
- `docs/M22E_F6_READ_FIRST.md` — Reuse map, file plan, risk note.
- `docs/M22E_F6_DELIVERY.md` — This file.

## 3. Manifest / reporting changes

| Where | Change |
|-------|--------|
| Workspace manifest (ops_reporting_workspace) | Already had `template_id`, `template_params`; now also `template_version` when template is used. |
| `get_workspace_inventory()` | Returned dict now has top-level `template_id` and `template_version` (from manifest). |
| Dashboard `recent_workspaces` | Each item has `template_id` and `template_version` (from inv). |
| Package manifest (`package_manifest.json`) | When built from a workspace whose manifest has `template_id`/`template_version`, those are copied into the package manifest. |
| Pilot session record | `record_workflow_artifact(..., template_id=...)` stores path in `artifacts_produced` and `template_id` in `extra["template_id"]`. |
| Aggregate session summaries | Each session summary dict includes `template_id` when present in session `extra`. |

## 4. Sample manifest excerpt (workspace)

```json
{
  "workflow": "ops_reporting_workspace",
  "timestamp": "2026-03-16T14:00:00Z",
  "grounding": "task_context_only",
  "template_id": "ops_reporting_core",
  "template_version": "1.0",
  "template_params": { "owner": "Alex", "label": "sprint_12" },
  "artifact_list": ["source_snapshot.md", "weekly_status.md", "status_brief.md"],
  "input_sources_used": [],
  "retrieval_used": false
}
```

## 5. Sample cohort / report excerpt

- **Dashboard recent_workspaces item:**  
  `"template_id": "ops_reporting_core"`, `"template_version": "1.0"` (when run was template-driven).

- **Aggregate session summary (per session):**  
  `"template_id": "ops_reporting_core"` when that session recorded an artifact with `record_workflow_artifact(..., template_id="ops_reporting_core")`.

- **Template usage output (`workflow-dataset templates usage`):**
  ```
  Template usage
    Total runs scanned: 12
    Template-driven runs: 5

  Most-used templates
    ops_reporting_core: 4 run(s)
    my_custom: 1 run(s)

  Recent template-driven runs (up to 10)
    2026-03-16T14:00:00Z  ops_reporting_core  2026-03-16_abc123  /path/to/workspaces/ops_reporting_workspace/2026-03-16_abc123
  ```

## 6. Tests run

```bash
# F6-specific (2 pass; pilot test may need pyyaml in env)
python3 -m pytest tests/test_templates.py::test_template_usage_summary_empty tests/test_templates.py::test_template_usage_summary_with_template_runs -v

# Inventory template fields (direct check, no pytest)
python3 -c "
from workflow_dataset.release.reporting_workspaces import get_workspace_inventory
...
assert inv.get('template_id') == 'ops_reporting_core'
"  # OK
```

- `test_get_workspace_inventory_includes_template_fields` — in `test_review_queue.py` (imports cli; requires `yaml`).
- `test_record_workflow_artifact_stores_template_id` — in `test_pilot.py` (imports pilot package; requires `yaml`).

With `pyyaml` installed, run:

```bash
python3 -m pytest tests/test_review_queue.py::test_get_workspace_inventory_includes_template_fields tests/test_templates.py::test_template_usage_summary_empty tests/test_templates.py::test_template_usage_summary_with_template_runs tests/test_pilot.py::test_record_workflow_artifact_stores_template_id -v
```

## 7. Remaining weaknesses (this pane only)

- **workspace_save**: `save_ops_reporting_workspace` is referenced by CLI and tests but the module was not found in the repo; manifest fields we add are passed through when that function exists elsewhere.
- **UI display**: Dashboard view code was not changed to render `template_id` in the workspace list; data is in payload, display can be added later.
- **Cohort report body**: Aggregate session summaries include `template_id`; cohort report markdown could explicitly list “Template: X” when present if desired.
- **Templates usage scope**: Only workspaces are scanned; pilot sessions are not aggregated in `template_usage_summary` (could add optional session scan for “runs that used a template” from session extra).
