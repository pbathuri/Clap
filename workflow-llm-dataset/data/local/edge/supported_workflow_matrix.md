# Supported Workflow Matrix

Generated: 2026-03-16T05:14:00.221442+00:00
Repo root: /Users/prady/Desktop/Clap/workflow-llm-dataset

| Workflow | Description | Manifest | Required files | Optional files |
|----------|-------------|----------|----------------|----------------|
| weekly_status | Single weekly status artifact. | manifest.json | manifest.json, weekly_status.md |  |
| status_action_bundle | Status brief + action register bundle. | manifest.json | manifest.json | status_brief.md, action_register.md |
| stakeholder_update_bundle | Stakeholder update + decision requests bundle. | manifest.json | manifest.json | stakeholder_update.md, decision_requests.md |
| meeting_brief_bundle | Meeting brief + action items bundle. | manifest.json | manifest.json | meeting_brief.md, action_items.md |
| ops_reporting_workspace | Multi-artifact ops reporting workspace (M21S/A2). | workspace_manifest.json | workspace_manifest.json, source_snapshot.md | weekly_status.md, status_brief.md, action_register.md, stakeholder_update.md, decision_requests.md |
