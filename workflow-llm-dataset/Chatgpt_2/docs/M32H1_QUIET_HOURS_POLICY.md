# M32H.1 — Quiet Hours + Interruptibility Policy

First-draft support for quiet hours, focus-safe suppression, and interruptibility by work mode, project, and trust level. Held-back suggestions get a clear explanation (visible via `assist explain-suggestion --id <id>`).

## Config location

`data/local/assist_engine/policy.yaml`  
Copy from `configs/assist_policy.yaml.example` to enable.

## Sample quiet-hours config

```yaml
quiet_hours:
  - start_utc: "22:00"
    end_utc: "07:00"
    description: "Night quiet (no assist suggestions)"

focus_safe:
  enabled: true
  max_interruptiveness: 0.3
  min_confidence: 0.7

interruptibility_rules:
  - work_mode: focused
    project_id: main_app
    trust_level: "*"
    allow_suggestions: false
    hold_back_reason_template: "Quiet focus mode for project {project_id}"
```

## Sample held-back suggestion explanation

When a suggestion is held back, `workflow-dataset assist explain-suggestion --id sug_xxx` can return:

```json
{
  "suggestion_id": "sug_abc123",
  "title": "Review blocked or stalled work",
  "status": "held_back",
  "held_back": true,
  "held_back_explanation": "Night quiet (no assist suggestions) (UTC 22:00–07:00)"
}
```

Or for focus-safe:

```json
{
  "held_back": true,
  "held_back_explanation": "Focus-safe: suggestion interruptiveness 0.45 exceeds max 0.30"
}
```

Or for interruptibility:

```json
{
  "held_back": true,
  "held_back_explanation": "Quiet focus mode for project main_app"
}
```

## CLI

- `assist now --focus-safe` — run with focus-safe suppression on for this run.
- `assist queue --status held_back` — list suggestions that were held back by policy.
- `assist explain-suggestion --id sug_xxx` — includes `held_back_explanation` when status is `held_back`.
- `assist policy-status` — show loaded policy (quiet hours, focus-safe, rules).

## Tests

```bash
pytest tests/test_assist_engine_policy.py -v
```

## Next recommended step for this pane

- **Wire live context into policy context**: Use `get_live_context_state` (or equivalent) in the assist engine so that `work_mode` and `project_id` are populated from the active live-context detector (Pane 1) when running `assist now`. That way interruptibility rules keyed by `focused` or by project will apply without the operator passing flags.
- **Optional override**: Add a one-off override for “show suggestions anyway” (e.g. `assist now --override-policy`) for emergencies, with an audit note.
