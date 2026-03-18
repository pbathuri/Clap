# M48D.1 — Governance Presets + Scope Templates (Deliverable)

## 1. Files modified

- **src/workflow_dataset/governance/models.py** — Added `GovernancePreset`, `ScopeTemplate` dataclasses.
- **src/workflow_dataset/governance/__init__.py** — Exported presets, scope_templates, reports.
- **src/workflow_dataset/governance/mission_control.py** — Slice now includes `active_governance_preset_id`, `preset_implications`, `active_scope_template_id`.
- **src/workflow_dataset/mission_control/report.py** — [Governance] section now prints preset, scope_template, and first two implication lines.
- **src/workflow_dataset/cli.py** — Added `governance preset show|list|set`, `governance scope-templates list|show`.
- **tests/test_governance.py** — Added tests for presets, scope templates, report, slice.

## 2. Files created

- **src/workflow_dataset/governance/presets.py** — `GovernancePreset` built-ins (solo_operator, supervised_team, production_maintainer); `list_presets`, `get_preset`, `get_active_preset`, `set_active_preset`; persistence in `data/local/governance/active_preset.json`.
- **src/workflow_dataset/governance/scope_templates.py** — `ScopeTemplate` built-ins (solo_vertical, team_vertical_project, production_single_vertical); `list_scope_templates`, `get_scope_template`.
- **src/workflow_dataset/governance/reports.py** — `format_governance_preset_report(repo_root)` for operator-facing active preset and implications.
- **docs/M48D1_GOVERNANCE_PRESETS_DELIVERABLE.md** — This file.

## 3. Sample governance preset

**supervised_team:**

```json
{
  "preset_id": "supervised_team",
  "label": "Supervised team",
  "description": "Operator + reviewer/approver; separation of duties for real run and sensitive gates.",
  "primary_role_id": "operator",
  "trust_preset_id": "supervised_operator",
  "scope_template_id": "team_vertical_project",
  "implications": [
    "Operator executes; reviewer/approver signs off on real run and sensitive gates.",
    "Initiator cannot self-approve in sensitive domains; use review studio for approvals.",
    "Escalate to support_reviewer or maintainer when blocked."
  ],
  "allowed_role_ids": ["operator", "reviewer", "approver", "observer", "support_reviewer"]
}
```

## 4. Sample scope template

**production_single_vertical:**

```json
{
  "template_id": "production_single_vertical",
  "label": "Production single vertical",
  "description": "Locked production cut; single vertical, review domains and operator routines scoped.",
  "scope_levels": ["vertical", "review_domain", "operator_mode_routine"],
  "default_scope_hint": "vertical",
  "deployment_pattern": "production_single_vertical"
}
```

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_governance.py -v
```

New/updated tests: `test_list_governance_presets`, `test_get_governance_preset`, `test_get_active_preset_default`, `test_set_and_get_active_preset`, `test_list_scope_templates`, `test_get_scope_template`, `test_format_governance_preset_report`, `test_governance_slice_includes_preset`.

## 6. Next recommended step for the pane

- **Wire preset into bindings:** When computing `get_effective_binding`, optionally prefer the active governance preset’s `trust_preset_id` (e.g. production_maintainer → release_safe) so the preset directly caps authority without requiring production_cut to be set.
- **Scope template application:** Add `governance scope-templates apply --id <template_id>` that sets default_scope_hint or writes a small scope config used by `resolve_scope` when scope_hint is empty.
- **Operator report in mission_control:** Ensure the “[Governance]” report section is visible in the default mission-control summary (already added); consider a dedicated `workflow-dataset governance report` that prints the full operator-facing preset report.
- **Preset ↔ production_cut alignment:** When production_cut is locked, suggest a matching governance preset (e.g. production_maintainer) if the current preset is solo_operator, and surface in mission_control.
