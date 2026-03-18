# M27D.1 — Project Templates + Goal Archetypes

First-draft reusable project templates and goal archetypes. Defines default goal stack, common artifacts, likely blockers, and recommended pack/value-pack associations. Extends M27A–M27D without rebuilding the project/case layer.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/project_case/models.py` | Added `GoalArchetype` (goal_id, title, description, order, default_blocked_reason) and `ProjectTemplate` (template_id, title, description, default_goal_stack, common_artifacts, likely_blockers, recommended_pack_ids, recommended_value_pack_ids). |
| `src/workflow_dataset/project_case/report.py` | Added `format_template_list`, `format_goal_archetype` for CLI and goal-archetype output. |
| `src/workflow_dataset/project_case/__init__.py` | Exported GoalArchetype, ProjectTemplate, list_templates, get_template, create_project_from_template, format_template_list, format_goal_archetype. |
| `src/workflow_dataset/cli.py` | `projects create`: added `--from-template` to seed from a template; added `projects templates list` and `projects templates show --id <template_id>`. |
| `tests/test_project_case_m27.py` | Added tests: test_list_templates, test_get_template, test_create_project_from_template, test_goal_archetype_output. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/project_case/templates.py` | Built-in templates: founder_ops, analyst_research, document_review, developer_feature; list_templates(), get_template(id), create_project_from_template(project_id, template_id, ...). |
| `docs/M27D1_PROJECT_TEMPLATES_GOAL_ARCHETYPES.md` | This doc. |

---

## 3. Sample project template

**Founder ops project** (template_id: `founder_ops`):

```python
ProjectTemplate(
    template_id="founder_ops",
    title="Founder ops project",
    description="Light ops, reporting, stakeholder updates. Weekly cadence.",
    default_goal_stack=[
        GoalArchetype("ship_weekly_report", "Ship weekly report", "Produce and send weekly status.", 0),
        GoalArchetype("stakeholder_review", "Stakeholder review", "Review with stakeholders.", 1, "Waiting on approval"),
        GoalArchetype("close_loop", "Close the loop", "Capture outcomes and next actions.", 2),
    ],
    common_artifacts=["weekly_status.md", "stakeholder_notes", "outcomes.json"],
    likely_blockers=["approval_missing", "timeout", "user_abandoned"],
    recommended_pack_ids=["founder_ops_pack", "ops_reporting_pack"],
    recommended_value_pack_ids=["founder_ops", "reporting_workspace"],
)
```

Templates included: **founder_ops**, **analyst_research**, **document_review**, **developer_feature**.

---

## 4. Sample goal-archetype output

**Command:** `workflow-dataset projects templates show --id founder_ops`

```
=== Goal archetype: founder_ops ===

title: Founder ops project
description: Light ops, reporting, stakeholder updates. Weekly cadence.

Default goal stack:
  [0] ship_weekly_report  Ship weekly report
  [1] stakeholder_review  Stakeholder review  (default blocked: Waiting on approval)
  [2] close_loop  Close the loop

Common artifacts: weekly_status.md, stakeholder_notes, outcomes.json
Likely blockers: approval_missing, timeout, user_abandoned
Recommended packs: founder_ops_pack, ops_reporting_pack
Recommended value-packs: founder_ops, reporting_workspace
```

---

## 5. Exact tests run

```bash
pytest tests/test_project_case_m27.py -v --tb=short
```

**Result: 14 passed** (10 existing M27 + 4 M27D.1).

M27D.1-related tests:
- `test_list_templates` — list_templates returns at least 4 templates including founder_ops, analyst_research, document_review, developer_feature.
- `test_get_template` — get_template("founder_ops") returns template with title, default_goal_stack, recommended packs.
- `test_create_project_from_template` — create_project_from_template("from_founder", "founder_ops") creates project with goals (e.g. ship_weekly_report) and linked artifacts.
- `test_goal_archetype_output` — format_goal_archetype("analyst_research") contains template id, "Default goal stack", goal names, "Common artifacts", "Recommended".

---

## 6. Next recommended step for the pane

- **User-defined templates**: Allow loading templates from `data/local/project_case/templates/*.json` in addition to built-ins, so operators can add custom project templates without code changes.
- **Template validation**: Add a small validator for template JSON (required keys, goal_archetype shape) and optionally `projects templates validate --path <file>`.
- **Planner/value-pack wiring**: When creating a project from a template, optionally suggest or link the recommended value pack / session template (e.g. set value_pack_id on a new session tied to the project) so "founder ops project" can auto-suggest the reporting workspace.
- **Goal archetype docs**: Add one-line descriptions for each built-in template to the CLI help or a `projects templates list --verbose` so operators can choose without opening the template.
