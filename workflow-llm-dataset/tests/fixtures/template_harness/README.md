# Template harness golden fixtures (M22E-F5)

Each subdir is a minimal workspace that matches one template’s expected artifact inventory and manifest shape.

- **ops_reporting_core/** — Matches template `ops_reporting_core`: source_snapshot.md, status_brief.md, action_register.md, decision_requests.md; workspace_manifest.json with workflow, template_id, artifact_list.

Used by `tests/test_template_harness.py` and optionally `workflow-dataset templates test --id <id> --workspace <path>`.
