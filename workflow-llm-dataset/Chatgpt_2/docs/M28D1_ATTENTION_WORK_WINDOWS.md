# M28D.1 — Attention Budgets + Work Windows

First-draft support for attention budgets per project, work windows / time slices, operator-defined focus modes, and rules for when to recommend switching projects. Explicit and operator-readable.

## Config file

`data/local/portfolio/attention_config.json`

- **attention_budgets**: list of `{ project_id, minutes_per_day?, minutes_per_week?, reset_interval, note }`.
- **work_windows**: list of `{ window_id, name, duration_minutes, start_time_local?, days_of_week?, note }`.
- **focus_modes**: list of `{ mode_id, name, description?, default_project_id?, project_ids?, switch_rules, active }`.
- **active_focus_mode_id**: which focus mode is active (used for switch rules).
- **current_window_started_at_iso**: set by `portfolio start-window`; used to compute remaining minutes and “window ended”.

## Switch rules

- **on_window_end**: recommend switch when `current_window_started_at` + first work window duration has elapsed.
- **when_higher_priority_ready**: recommend switch when portfolio next recommends a different project.
- **on_budget_exhausted**: reserved (no time-spent tracking in first draft).
- **manual_only**: never auto-suggest switch.

## CLI

- `workflow-dataset portfolio attention` — show attention config (budgets, windows, focus modes).
- `workflow-dataset portfolio work-window [--project <id>]` — work window recommendation (duration, remaining, suggested next).
- `workflow-dataset portfolio should-switch [--project <id>]` — whether to switch (rule triggered, reason, suggested project).
- `workflow-dataset portfolio start-window` — start a work slice (sets current_window_started_at to now).

## Sample work-window recommendation (output)

```
  project: founder_case_alpha  window: Pomodoro slice  duration: 25 min
  remaining: 12 min
  suggested_next: analyst_research  — Portfolio next: analyst_research
```

## Sample should-switch recommendation (output)

```
  recommend_switch: True  rule: higher_priority_ready
  reason: Rank #1; advancing; unblocked
  suggested_project: analyst_research
```

## Next recommended step for the pane

- **Wire agent-loop to portfolio next**: When `agent-loop next` is run without `--project`, default to `portfolio next` recommended project so the loop advances the portfolio’s top suggestion.
- **Optional: Time-spent tracking**: Persist per-project time spent (e.g. from start-window + project_id) to drive `on_budget_exhausted` and budget caps in reports.
- **Optional: CLI to set active focus mode**: e.g. `workflow-dataset portfolio focus --mode round_robin`.
- **Mission control**: Add a one-line summary of work-window remaining and should-switch to the Portfolio section when attention config is present.
