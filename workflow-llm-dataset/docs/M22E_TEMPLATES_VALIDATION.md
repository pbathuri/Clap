# M22E — Workflow Composer + Template Studio — Validation

## Summary

- **Local-first:** Templates are YAML/JSON files under `data/local/templates/`. No cloud; no auto-apply.
- **Explicit composition:** A template defines `workflow_id` and ordered `artifacts`; release demo runs that workflow and saves only those artifacts in that order.
- **Stays in validated workflows:** Template `workflow_id` must be one of the current ops/reporting family; artifacts are validated against that workflow.

## Files Modified / Added

| Action | Path |
|--------|------|
| Added | `src/workflow_dataset/templates/__init__.py` |
| Added | `src/workflow_dataset/templates/registry.py` — load_template, list_templates, get_template, template_artifact_order_and_filenames |
| Added | `data/local/templates/ops_reporting_core.yaml` |
| Added | `data/local/templates/weekly_plus_stakeholder.yaml` |
| Modified | `src/workflow_dataset/cli.py` — templates list/show; release demo --template, template-based artifact filter/order, manifest template_id |
| Added | `tests/test_templates.py` |
| Added | `docs/M22E_TEMPLATES_VALIDATION.md` |

## Template / Composer Usage

```bash
# List templates
workflow-dataset templates list
workflow-dataset templates list --repo-root /path

# Show template definition
workflow-dataset templates show --id ops_reporting_core
workflow-dataset templates show -i weekly_plus_stakeholder

# Run demo with template (sets workflow and artifact set/order when saving)
workflow-dataset release demo --template ops_reporting_core --save-artifact
workflow-dataset release demo -t weekly_plus_stakeholder --intake sprint_notes --save-artifact
```

## Sample Template Definition

**data/local/templates/ops_reporting_core.yaml:**

```yaml
id: ops_reporting_core
name: Ops reporting core
description: Status brief, action register, and decision requests (subset of ops_reporting_workspace)
workflow_id: ops_reporting_workspace
artifacts:
  - status_brief
  - action_register
  - decision_requests
```

**Composer example (weekly + stakeholder):**

```yaml
id: weekly_plus_stakeholder
name: Weekly status and stakeholder update
description: Weekly status plus stakeholder-facing update and decision requests
workflow_id: ops_reporting_workspace
artifacts:
  - weekly_status
  - stakeholder_update
  - decision_requests
```

## Sample Template-Driven Workspace

After:

```bash
workflow-dataset release demo --template ops_reporting_core --save-artifact
```

the workspace under `data/local/workspaces/ops_reporting_workspace/<ts_id>/` contains:

- **Artifacts (template order):** `status_brief.md`, `action_register.md`, `decision_requests.md` (only these three, in that order)
- **source_snapshot.md** (first, as usual)
- **workspace_manifest.json** including:
  - `"template_id": "ops_reporting_core"`
  - `"workflow": "ops_reporting_workspace"`
  - `"artifact_list": ["source_snapshot.md", "status_brief.md", "action_register.md", "decision_requests.md"]`

Without `--template`, the same workflow would save all six artifacts (weekly_status, status_brief, action_register, stakeholder_update, decision_requests) in the default order.

## Tests Run

```bash
cd workflow-llm-dataset
PYTHONPATH=src python3 -m pytest tests/test_templates.py -v
# 9 passed
```

## Constraints Preserved

- Templates do not auto-apply code or files; they only control which artifacts are generated and in what order when the operator runs `release demo --template ... --save-artifact`.
- Scope is the current ops/reporting family (workflow_id and artifacts validated in registry).
- Composition is explicit: template id and artifact list are stored in the manifest.

---

## Recommendation for Next Workflow-Suite Batch

1. **Wording/style hints:** Use optional `wording_hints` in templates to inject style or tone (e.g. "concise", "stakeholder-safe") into prompts or into a future prompt-builder layer.
2. **Template from workspace:** Add `workflow-dataset templates create-from-workspace --workspace <path> --id <new_id>` to derive a template from an existing workspace (workflow + artifact list from manifest).
3. **More workflows:** When new workflows are added, extend `VALID_WORKFLOW_IDS` and `WORKFLOW_ARTIFACTS` so new templates can reference them.
4. **Dashboard:** Show "Templates" in the command center with list and a shortcut to run demo with a selected template.
