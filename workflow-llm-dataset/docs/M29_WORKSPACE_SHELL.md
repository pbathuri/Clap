# M29 — Unified Workspace Shell + Navigation State

## Overview

First-draft local-first workspace shell that provides one unified home, navigation between portfolio / project / session / lane / pack / policy / approval / artifact views, and clear “where am I / what is active / what should happen next” without rebuilding mission_control or other systems.

## CLI / Workspace Usage

| Command | Description |
|--------|-------------|
| `workflow-dataset workspace home` | Unified workspace home: top project, session, approvals, blocked, recent, next action, areas. |
| `workflow-dataset workspace open --view <view>` | Open a view; prints navigation state and suggested commands (deep link). |
| `workflow-dataset workspace open --view project --project <id>` | Open project view for `<id>`; suggests e.g. `projects show --id <id>`, `projects report`, `agent-loop next --project <id>`. |
| `workflow-dataset workspace open --view session [--session <id>]` | Open session view; suggests `session board`, `session artifacts`. |
| `workflow-dataset workspace context` | Current workspace context as JSON: project, session, breadcrumbs, next action. |
| `workflow-dataset workspace next` | Next recommended action (portfolio next + mission_control next) as JSON. |

Views for `workspace open --view`: `home`, `portfolio`, `project`, `session`, `approvals`, `policy`, `lanes`, `packs`, `artifacts`, `outcomes`, `rollout`, `settings`.

## Sample Workspace Home Output

```
=== Workspace Home ===

[Where you are]
  Project: founder_case_alpha  Founder ops
  Session: sess_abc  pack: founder_ops
  Goal: Complete weekly review and prioritise next actions…

[Top priority / Next]
  Next project: founder_case_alpha
  Reason: Best composite score; no blocker.
  Next action: advance  — Run agent-loop next for current goal

[Approvals]
  2 pending approval(s). Run: workflow-dataset agent-loop queue

[Blocked]
  No blocked items.

[Recent]
  Last: approved run=run_xyz
  Artifacts: 3

[Trust / Health]
  Trust: ok ; Env: OK

[Areas]
  home: Home  — workflow-dataset workspace home
  portfolio: Portfolio  (2)  — workflow-dataset portfolio status
  projects: Projects  (2)  — workflow-dataset projects list
  ...

[Quick]  workflow-dataset workspace context  |  workflow-dataset workspace next  |  workflow-dataset mission-control
```

## Sample Workspace Context Output

```json
{
  "active_project_id": "founder_case_alpha",
  "active_project_title": "Founder ops",
  "active_session_id": "sess_abc",
  "active_goal_text": "Complete weekly review and prioritise next actions",
  "queued_approvals_count": 2,
  "blocked_items_count": 0,
  "navigation": {
    "current_view": "home",
    "current_project_id": "founder_case_alpha",
    "current_session_id": "sess_abc",
    "breadcrumbs": ["Home"],
    "quick_actions": [
      {"label": "Project report", "command": "workflow-dataset projects report --id founder_case_alpha"},
      {"label": "Mission control", "command": "workflow-dataset mission-control"}
    ]
  },
  "next_action": "advance",
  "next_detail": "Run agent-loop next for current goal"
}
```

## Sample Navigation State / Deep-Link Output

`workflow-dataset workspace open --view project --project founder_case_alpha`:

- **view**: `project`
- **breadcrumbs**: `["Home", "Portfolio", "founder_case_alpha"]`
- **suggested_commands** (examples):
  - `workflow-dataset projects show --id founder_case_alpha`
  - `workflow-dataset projects report --id founder_case_alpha`
  - `workflow-dataset agent-loop next --project founder_case_alpha`

## Files Modified / Created

| Action | Path |
|--------|------|
| New | `src/workflow_dataset/workspace/__init__.py` |
| New | `src/workflow_dataset/workspace/models.py` |
| New | `src/workflow_dataset/workspace/state.py` |
| New | `src/workflow_dataset/workspace/home.py` |
| New | `src/workflow_dataset/workspace/navigation.py` |
| New | `src/workflow_dataset/workspace/cli.py` |
| Edit | `src/workflow_dataset/cli.py` — added `workspace_group` and commands `home`, `open`, `context`, `next` |
| New | `tests/test_workspace_m29.py` |
| New | `docs/M29_WORKSPACE_SHELL.md` |

## Tests Run

From repo root (workflow-llm-dataset):

```bash
pytest tests/test_workspace_m29.py -v
```

Covered:

- Workspace view model and navigation state (roundtrip, constants).
- Navigation state transitions (home → portfolio → project breadcrumbs).
- Home/overview generation (snapshot, format_workspace_home).
- Contextual linking (resolve_view_target, deep_link_commands).
- Empty-state / no-project / no-session (build_active_work_context, cmd_context, cmd_next).

## Remaining Gaps for Later Refinement

- **Persisted “current view”**: Navigation view is derived at call time; no persisted `current_view.json` for CLI consistency across invocations (optional later).
- **Rich UI**: Only CLI/text output; no TUI or web workspace UI.
- **Deep link execution**: Commands are suggested, not executed; operator runs them.
- **Lane/pack drill-down**: `open --view lanes` / `open --view packs` suggest list commands; no per-lane or per-pack “open” deep link yet.
- **Rollout/settings**: Placeholder suggestions only; can be wired to rollout/health commands in a later pass.
