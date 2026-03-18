# M27A–M27D — Project/Case Graph + Persistent Goal Stack

First-draft persistent project/case layer: project and case model, goal stack (ordered goals, active/deferred/complete/blocked), links to sessions/plans/runs/artifacts/skills, project report and mission-control visibility. Local-first, inspectable; no cloud or autonomous project changes.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `projects_group` and commands: `list`, `create`, `show`, `goals`, `add-goal`, `attach-session`, `attach-plan`, `attach-run`, `attach-artifact`, `report`, `set-current`, `archive`. |
| `src/workflow_dataset/mission_control/state.py` | Added `project_case` block: `active_project_id`, goal_stack_summary, project_blockers, latest_linked, recommended_next_project_action; populated when current project is set. |
| `src/workflow_dataset/mission_control/report.py` | Added [Project / case] section: active project, goals summary, blockers, recommended next. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/project_case/models.py` | Project, Goal, Subgoal, ProjectMilestone, ProjectState, LinkedSession, LinkedPlan, LinkedRun, LinkedArtifact, LinkedSkill, BlockedDependency, NextProjectAction. |
| `src/workflow_dataset/project_case/store.py` | get_projects_dir, get_project_dir, create_project, load_project, save_project, list_projects, set_current_project_id, get_current_project_id, archive_project; attach_session, attach_plan, attach_run, attach_artifact, attach_skill; get_linked_*. |
| `src/workflow_dataset/project_case/goal_stack.py` | list_goals, list_subgoals, add_goal, add_subgoal, set_goal_order, set_goal_status, set_subgoal_status, add_goal_dependency, get_blocked_goals, recommended_next_goal. |
| `src/workflow_dataset/project_case/graph.py` | build_project_state, get_project_summary (for report and mission control). |
| `src/workflow_dataset/project_case/report.py` | format_project_list, format_project_show, format_goal_stack, format_project_report. |
| `src/workflow_dataset/project_case/__init__.py` | Public exports. |
| `tests/test_project_case_m27.py` | Tests: create/load, list, archive, goal ordering, goal status/blocked, recommended next, attach session/run, report format, current project id, project summary. |
| `docs/M27A_M27D_PROJECT_CASE_ANALYSIS.md` | Before-coding: existing state, gaps, file plan, safety, what this block does not do. |
| `docs/M27A_M27D_PROJECT_CASE.md` | This doc. |

Storage: `data/local/project_case/` — `current_project_id.json`, `projects/<project_id>/project.json`, `goals.json`, `links.json`.

---

## 3. Exact CLI usage

```bash
workflow-dataset projects list [--repo-root PATH] [--state active|archived|closed]
workflow-dataset projects create --id <id> [--title T] [--description D] [--repo-root PATH]
workflow-dataset projects show --id <id> [--repo-root PATH]
workflow-dataset projects goals --id <id> [--repo-root PATH]
workflow-dataset projects add-goal --id <id> --goal-id <gid> [--title T] [--order N] [--repo-root PATH]
workflow-dataset projects attach-session --id <id> --session <session_id|latest> [--repo-root PATH]
workflow-dataset projects attach-plan --id <id> [--plan-id PID] [--plan-path PATH] [--repo-root PATH]
workflow-dataset projects attach-run --id <id> --run <run_id> [--repo-root PATH]
workflow-dataset projects attach-artifact --id <id> --artifact <path_or_label> [--repo-root PATH]
workflow-dataset projects report --id <id> [--repo-root PATH]
workflow-dataset projects set-current --id <id> [--repo-root PATH]
workflow-dataset projects archive --id <id> [--repo-root PATH]
```

---

## 4. Sample project record

**data/local/project_case/projects/founder_case_alpha/project.json**

```json
{
  "project_id": "founder_case_alpha",
  "title": "Founder case alpha",
  "description": "First persistent case for founder ops.",
  "state": "active",
  "created_at": "2025-03-16T12:00:00.000000Z",
  "updated_at": "2025-03-16T12:05:00.000000Z"
}
```

**data/local/project_case/projects/founder_case_alpha/goals.json** (excerpt)

```json
{
  "goals": [
    {
      "goal_id": "ship_weekly_report",
      "title": "Ship weekly report",
      "description": "",
      "status": "active",
      "order": 0,
      "blocked_reason": "",
      "created_at": "2025-03-16T12:01:00Z",
      "updated_at": "2025-03-16T12:01:00Z"
    },
    {
      "goal_id": "stakeholder_review",
      "title": "Stakeholder review",
      "status": "blocked",
      "order": 1,
      "blocked_reason": "Waiting on approval",
      "created_at": "2025-03-16T12:02:00Z",
      "updated_at": "2025-03-16T12:02:00Z"
    }
  ],
  "subgoals": [],
  "goal_dependencies": []
}
```

---

## 5. Sample goal stack output

```
=== Goal stack: founder_case_alpha ===

  [0] ship_weekly_report  Ship weekly report  status=active
  [1] stakeholder_review  Stakeholder review  status=blocked
      blocked: Waiting on approval
```

---

## 6. Sample project report

```
=== Project report: Founder case alpha ===

state: active
goals: 2  (active/blocked/deferred/complete in project_state)

Blocked goals:
  - stakeholder_review: Waiting on approval

Recommended next: work_goal — Ship weekly report (First active goal in stack)

Latest linked:
  session: sess_abc
  run: run_xyz
```

---

## 7. Exact tests run

```bash
pytest tests/test_project_case_m27.py -v --tb=short
```

**Result: 10 passed.**

- test_create_and_load_project  
- test_list_projects  
- test_archive_project  
- test_goal_stack_ordering  
- test_goal_status_active_blocked  
- test_recommended_next_goal  
- test_attach_session_and_run  
- test_project_report_format  
- test_current_project_id  
- test_project_summary_for_mission_control  

---

## 8. Exact remaining gaps for later refinement

- **Subgoal CLI**: add_subgoal, set_subgoal_status exist in goal_stack; no CLI commands for subgoals yet.
- **Goal dependency UX**: add_goal_dependency exists; no CLI to add or list dependency edges.
- **Planner/executor/session linking**: Project only stores references (session_id, run_id, etc.). No automatic “link latest plan/run to current project” on planner compile or executor run; can be added later as optional hooks.
- **Mission control next_action**: When no active project, next_action suggests create + set-current; could also suggest “projects list” for discoverability.
- **Bulk import / export**: No export/import of a project (e.g. JSON bundle) for backup or move.
- **Project state history**: Only current state is stored; no time-series of state changes for “project state over time” analytics.
