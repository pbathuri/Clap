# M47D.1 — Role-Tuned Entry Paths + Faster On-Ramps (Deliverable)

## 1. Files modified

- **src/workflow_dataset/vertical_excellence/models.py** — Added `RoleTunedEntryPath`, `OnRampPreset` dataclasses.
- **src/workflow_dataset/vertical_excellence/recommend_next.py** — Extended `recommend_next_for_vertical(repo_root, user_recency=None, role_id=None)` with new/returning flows and role-tuned start.
- **src/workflow_dataset/vertical_excellence/__init__.py** — Exported role entry paths and on-ramp presets.
- **src/workflow_dataset/cli.py** — Added `vertical-excellence entry-path --role`, `vertical-excellence on-ramp list`, `vertical-excellence on-ramp show <preset_id>`, and `recommend-next --new-user` / `--returning-user` / `--role`.
- **tests/test_vertical_excellence.py** — Added tests for role-tuned entry path, on-ramp presets, new/returning recommend-next.

## 2. Files created

- **src/workflow_dataset/vertical_excellence/role_entry_paths.py** — `get_role_tuned_entry_path(vertical_id, role_id, repo_root)`, `get_role_tuned_entry_path_for_chosen_vertical(role_id, repo_root)`; roles: operator, reviewer, analyst.
- **src/workflow_dataset/vertical_excellence/on_ramp_presets.py** — `list_on_ramp_presets()`, `get_on_ramp_preset(preset_id)`, `build_path_with_preset(vertical_id, preset_id, repo_root)`; presets: minimal (3 steps), standard (5), full (6).
- **docs/M47D1_ROLE_TUNED_ONRAMP_DELIVERABLE.md** — This file.

## 3. Sample role-tuned entry path

```
[bold]Reviewer entry — queue and approvals first[/bold]  vertical=founder_operator_core  role=reviewer
  entry: workflow-dataset onboard status
  1. Onboard approvals  # workflow-dataset onboard status
  2. Show inbox  # workflow-dataset inbox
  first_value_outcome: First review cycle; inbox and approval status visible.
  best_next_after_entry: workflow-dataset queue
```

(Operator and analyst variants differ by label, entry_point, step subset, and best_next_after_entry.)

## 4. Sample faster on-ramp preset

```
[bold]Minimal — 3 steps to first value[/bold]  Fastest on-ramp: profile bootstrap, onboard status, one simulate.
  entry: workflow-dataset profile bootstrap  steps: [1, 3, 6]  for: new_user
  1. Bootstrap profile  # workflow-dataset profile bootstrap
  3. Onboard approvals  # workflow-dataset onboard status
  6. Run one safe simulate-only routine  # ...
```

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_vertical_excellence.py -v
```

New/updated tests: `test_get_role_tuned_entry_path_operator`, `test_get_role_tuned_entry_path_reviewer`, `test_get_role_tuned_entry_path_analyst`, `test_get_role_tuned_entry_path_for_chosen_vertical`, `test_list_on_ramp_presets`, `test_get_on_ramp_preset_minimal`, `test_build_path_with_preset`, `test_recommend_next_new_user`, `test_recommend_next_returning_user`.

## 6. Next recommended step for the pane

- **Wire role into mission control / report:** Add optional `role_id` and `user_recency` to the vertical excellence mission-control slice and show “recommended for: new user (operator)” or “returning: day status” in the report.
- **Persist “new vs returning” signal:** Use a lightweight signal (e.g. first-time vs returning in session or continuity) so CLI can default `--new-user` / `--returning-user` when not passed.
- **Expand role set:** Align with vertical_packs (e.g. developer, document_heavy) and add role-specific entry paths for those packs.
- **On-ramp in path-report:** Include “suggested on-ramp: minimal” in the first-value path report when stage is not_started.
