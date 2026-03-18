# M36D.1 — Workday Presets + Operating Modes by Role

First-draft role-based workday presets: founder/operator, analyst, developer, document-heavy, supervision-heavy. Defines default day states, default transitions, queue/review emphasis, operator-mode usage.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/workday/store.py` | Added `get_active_workday_preset_id()`, `set_active_workday_preset_id()`; `ACTIVE_PRESET_FILE = active_preset.txt`. |
| `src/workflow_dataset/workday/surface.py` | Load active preset; set `preset_id`, `role_operating_hint` on surface; after startup recommend `preset.default_transition_after_startup`; when focus_work + preset operator_mode preferred, recommend operator_mode before wrap_up. |
| `src/workflow_dataset/workday/__init__.py` | Exported presets and store get/set. |
| `src/workflow_dataset/cli.py` | Added `day preset list`, `day preset show --id`, `day preset set --id`. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/workday/presets.py` | WorkdayPreset, BUILTIN_WORKDAY_PRESETS (founder_operator, analyst, developer, document_heavy, supervision_heavy), get_workday_preset, list_workday_presets. |
| `tests/test_workday_presets.py` | Tests for presets, active preset persistence, surface preset and recommendation. |
| `docs/M36D1_WORKDAY_PRESETS_AND_ROLES.md` | This document. |

---

## 3. Sample workday preset

**Preset: `supervision_heavy` (Supervision-heavy operator)**

```json
{
  "preset_id": "supervision_heavy",
  "label": "Supervision-heavy operator",
  "description": "Review and approvals first: start, clear queue and reviews, then focus or operator mode.",
  "default_day_states": ["startup", "review_and_approvals", "focus_work", "operator_mode", "wrap_up", "shutdown"],
  "default_transition_after_startup": "review_and_approvals",
  "queue_review_emphasis": "high",
  "operator_mode_usage": "preferred",
  "quick_actions": [
    {"label": "Agent loop queue", "command": "workflow-dataset agent-loop queue"},
    {"label": "Inbox studio", "command": "workflow-dataset inbox-studio list"},
    {"label": "Automation inbox", "command": "workflow-dataset automation-inbox list"},
    {"label": "Trust validate-config", "command": "workflow-dataset trust validate-config"}
  ],
  "role_operating_hint": "Clear approvals and review first; then focus or operator mode."
}
```

---

## 4. Sample role-based operating surface output

With `workflow-dataset day preset set --id founder_operator` and state `startup`:

```
=== Daily operating surface ===
  State: startup  (entered: 2025-03-16T08:00:00Z)
  Day: 2025-03-16  started: 2025-03-16T08:00:00Z
  Preset: founder_operator
  Hint: Portfolio and approvals first; operator mode for delegated runs.

[Context]
  Project: founder_case_alpha  Founder ops case
  Focus: —
  Top queue: —
  Approvals: 2 pending approval(s)
  Automation: —
  Trust: —

[Transitions]
  Allowed next: focus_work, review_and_approvals, operator_mode, wrap_up, shutdown
  Recommended: review_and_approvals
  Reason: (Founder / Operator) workflow-dataset day mode --set review_and_approvals
```

Without a preset, the same state would recommend `focus_work`. With `analyst` preset, after startup the recommended transition would be `focus_work`.

---

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_workday_presets.py -v
```

Test names:

- test_list_workday_presets
- test_get_workday_preset
- test_founder_operator_preset_defaults
- test_supervision_heavy_preset_defaults
- test_active_preset_persistence
- test_surface_includes_preset_when_set
- test_surface_startup_recommends_preset_transition
- test_workday_preset_to_dict

*(Note: test_surface_includes_preset_when_set and test_surface_startup_recommends_preset_transition call build_daily_operating_surface and may be slower due to aggregation.)*

---

## 6. Next recommended step for the pane

- **Align with workspace presets**: Map workspace preset (e.g. founder-operator) to workday preset (founder_operator) so that `workspace home --preset founder-operator` can optionally set or suggest the same workday preset for a consistent role experience.
- **Quick actions in surface**: Show preset quick_actions in `day status` output (e.g. a “[Quick actions]” section with the preset’s commands) so the operator can one-shot the role’s preferred commands.
- **Preset in mission control**: Add active workday preset to mission_control state/report (e.g. “workday_preset: founder_operator”) so the dashboard shows current role context.
- **Time- or context-based suggestion**: Optionally suggest switching preset (e.g. “Consider supervision_heavy when you have many pending approvals”) without auto-switching.
