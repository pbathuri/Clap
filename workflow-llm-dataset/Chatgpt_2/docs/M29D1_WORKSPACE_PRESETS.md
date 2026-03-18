# M29D.1 — Workspace Presets + Role-Specific Layouts

## Overview

First-draft workspace presets define role-specific home composition, default quick actions, priority widgets, and recommended first view. Presets extend the M29 workspace shell without rebuilding it.

## Presets

| Preset ID (--preset) | Label | Recommended first view |
|----------------------|--------|-------------------------|
| `founder-operator`    | Founder / Operator | portfolio |
| `analyst`            | Analyst | session |
| `developer`          | Developer | session |
| `document-heavy`     | Document-heavy | artifacts |

## Sample Workspace Preset (founder_operator)

```python
WorkspacePreset(
    preset_id="founder_operator",
    label="Founder / Operator",
    description="Portfolio-first: approvals, next project, mission control.",
    home_section_order=(
        "where_you_are",
        "approvals",
        "top_priority_next",
        "blocked",
        "recent",
        "trust_health",
        "areas",
        "quick",
    ),
    default_quick_actions=(
        {"label": "Mission control", "command": "workflow-dataset mission-control"},
        {"label": "Portfolio next", "command": "workflow-dataset portfolio next"},
        {"label": "Approval queue", "command": "workflow-dataset agent-loop queue"},
        {"label": "Workspace context", "command": "workflow-dataset workspace context"},
    ),
    priority_widgets=("approvals", "top_priority_next"),
    recommended_first_view="portfolio",
)
```

## Sample Role-Specific Home Output (founder-operator)

```
=== Workspace Home ===

(Preset: Founder / Operator)
  Recommended first view: portfolio

[Where you are]
  Project: —  
  Session: —  pack: —
  Goal: —

[Approvals]
  No pending approvals.

[Top priority / Next]
  Next project: —
  Reason: —
  Next action: build  — Pending patch proposals need operator review.

[Blocked]
  No blocked items.

[Recent]
  —
  Artifacts: 0

[Trust / Health]
  Trust: — ; Env: OK

[Areas]
  home: Home  — workflow-dataset workspace home
  ...

[Quick]

  Mission control: workflow-dataset mission-control
  Portfolio next: workflow-dataset portfolio next
  Approval queue: workflow-dataset agent-loop queue
  Workspace context: workflow-dataset workspace context
```

## CLI

- `workflow-dataset workspace home` — default layout
- `workflow-dataset workspace home --preset founder-operator` — founder/operator layout
- `workflow-dataset workspace home -p analyst` — analyst layout
- `workflow-dataset workspace presets list` — list all presets with id, label, description, first view

## Tests Run

```bash
pytest tests/test_workspace_m29.py -v
```

Covers: preset get/list, preset model roundtrip, format_workspace_home with preset (label + quick actions), founder preset section order (Approvals before Top priority), cmd_presets_list.

## Files Modified / Created

| Action | Path |
|--------|------|
| Modified | `src/workflow_dataset/workspace/models.py` — WorkspacePreset, HOME_SECTION_* |
| Created | `src/workflow_dataset/workspace/presets.py` |
| Modified | `src/workflow_dataset/workspace/home.py` — preset_id, section order, quick actions |
| Modified | `src/workflow_dataset/workspace/cli.py` — cmd_home(preset_id), cmd_presets_list |
| Modified | `src/workflow_dataset/cli.py` — workspace home --preset, workspace presets list |
| Modified | `src/workflow_dataset/workspace/__init__.py` — export presets |
| Modified | `tests/test_workspace_m29.py` — M29D.1 preset tests |
| Created | `docs/M29D1_WORKSPACE_PRESETS.md` |

## Next Recommended Step for the Pane

- **Persist selected preset**: Allow a default preset to be stored (e.g. `data/local/workspace/preset_id.txt` or env `WORKFLOW_WORKSPACE_PRESET`) so `workflow-dataset workspace home` without `--preset` uses it when set.
- **Open with first view**: Add `workflow-dataset workspace open --preset founder-operator` that opens the preset’s `recommended_first_view` and prints suggested commands for that view.
- **Priority widget emphasis**: In formatted output, optionally mark priority_widgets sections (e.g. with a `*` or header note) so “priority” is visible in the CLI.
