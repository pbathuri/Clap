# M39E–M39H — Curated Vertical Workflow Packs (Deliverable)

First-draft curated vertical workflow layer: opinionated packs, guided value paths, first-value milestones, CLI, mission control visibility.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `vertical-packs` Typer: list, show --id, apply --id, first-value --id, progress; added `vertical-paths` Typer with first-value --id. |
| `src/workflow_dataset/mission_control/state.py` | Added `vertical_packs_state`: active_curated_pack_id, current_first_value_path_id, next_vertical_milestone, blocked_vertical_onboarding_step, strongest_value_path_id, suggested_next_command. |
| `src/workflow_dataset/mission_control/report.py` | Report section for [Vertical packs]: active pack, path, next milestone, blocked step, suggested command. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/vertical_packs/models.py` | CuratedVerticalPack, CoreWorkflowPath, FirstValuePath, FirstValuePathStep, TrustReviewPosture, RecommendedWorkdayProfile, RecommendedQueueProfile, RequiredSurfaces, SuccessMilestone, CommonFailurePoint. |
| `src/workflow_dataset/vertical_packs/paths.py` | build_path_for_pack(); milestones and common_failure_points; uses value_packs golden_bundles and first_run_flow. |
| `src/workflow_dataset/vertical_packs/registry.py` | BUILTIN_CURATED_PACKS (founder_operator_core, analyst_core, developer_core, document_worker_core); get_curated_pack, list_curated_pack_ids, get_curated_pack_for_value_pack. |
| `src/workflow_dataset/vertical_packs/defaults.py` | apply_vertical_defaults(); get_recommended_commands_for_pack(); persist active pack, return recommended commands (no trust/approval change). |
| `src/workflow_dataset/vertical_packs/store.py` | data/local/vertical_packs/active.json, progress.json; get/set active pack, get/set path progress, set_milestone_reached. |
| `src/workflow_dataset/vertical_packs/progress.py` | get_next_vertical_milestone(), get_blocked_vertical_onboarding_step(), build_milestone_progress_output(). |
| `src/workflow_dataset/vertical_packs/__init__.py` | Re-exports models, registry, paths, defaults, store, progress. |
| `tests/test_vertical_packs.py` | test_curated_pack_model, test_guided_path_generation, test_vertical_defaults_apply, test_first_value_milestone_tracking, test_weak_incomplete_path_behavior. |
| `docs/samples/M39_curated_vertical_pack_sample.json` | Sample curated pack (founder_operator_core). |
| `docs/samples/M39_guided_value_path_sample.json` | Sample first-value path with steps, milestones, failure points. |
| `docs/samples/M39_milestone_progress_sample.json` | Sample progress: next milestone, reached, suggested command. |
| `docs/M39E_M39H_CURATED_VERTICAL_BEFORE_CODING.md` | Before-coding: assets, gaps, file plan, safety, curation principles, scope. |
| `docs/M39E_M39H_CURATED_VERTICAL_DELIVERABLE.md` | This deliverable. |

---

## 3. Exact CLI usage

```bash
# List curated vertical packs
workflow-dataset vertical-packs list
workflow-dataset vertical-packs list --json

# Show one pack (definition, paths, trust, surfaces)
workflow-dataset vertical-packs show --id founder_operator_core
workflow-dataset vertical-packs show --id founder_operator_core --json

# Apply pack (set active pack; show recommended commands; does not change trust/approval)
workflow-dataset vertical-packs apply --id founder_operator_core
workflow-dataset vertical-packs apply --id founder_operator_core --dry-run
workflow-dataset vertical-packs apply --id founder_operator_core --json

# First-value path for a pack
workflow-dataset vertical-packs first-value --id founder_operator_core
workflow-dataset vertical-packs first-value --id founder_operator_core --json
workflow-dataset vertical-paths first-value --id founder_operator_core

# Path progress (active pack, next milestone, blocked step, suggested command)
workflow-dataset vertical-packs progress
workflow-dataset vertical-packs progress --json
```

---

## 4. Sample curated vertical pack

See `docs/samples/M39_curated_vertical_pack_sample.json`. Summary:

- **pack_id**: founder_operator_core  
- **name**: Founder / Operator (core)  
- **value_pack_id**: founder_ops_plus  
- **workday_preset_id**: founder_operator  
- **default_experience_profile_id**: founder_calm  
- **trust_review_posture**: trust_preset_id supervised_operator, review_gates_default ["before_real"]  
- **core_workflow_path**: morning_ops, weekly_status_from_notes, weekly_status, morning_reporting  
- **first_value_path**: founder_ops_plus_first_value (entry, steps, milestones, common_failure_points)  
- **required_surfaces**: workspace_home, day_status, queue_summary, approvals_urgent, continuity_carry_forward  

---

## 5. Sample guided value path

See `docs/samples/M39_guided_value_path_sample.json`. Summary:

- **path_id**: founder_ops_plus_first_value  
- **entry_point**: workflow-dataset package first-run  
- **required_surface_ids**: workspace_home, queue_summary, approvals_urgent, continuity_carry_forward  
- **steps**: 1–5 (Install/bootstrap, Check runtime, Onboard approvals, First simulate run, First trusted-real candidate)  
- **milestones**: first_run_completed, runtime_check_done, onboard_approvals_done, first_simulate_done, first_real_done  
- **first_value_milestone_id**: first_simulate_done  
- **common_failure_points**: step 1 (install), step 3 (approval scope), step 4 (simulate), step 5 (real run) with symptoms and remediation_hint  

---

## 6. Sample milestone / progress output

See `docs/samples/M39_milestone_progress_sample.json`. Example:

```json
{
  "active_curated_pack_id": "founder_operator_core",
  "path_id": "founder_ops_plus_first_value",
  "next_milestone_id": "first_simulate_done",
  "next_milestone_label": "First simulate",
  "reached_milestone_ids": ["first_run_completed", "runtime_check_done", "onboard_approvals_done"],
  "blocked_step_index": 0,
  "strongest_value_path_id": "founder_ops_plus_first_value",
  "suggested_next_command": "workflow-dataset macro run --id morning_ops --mode simulate"
}
```

CLI: `workflow-dataset vertical-packs progress --json` (after `vertical-packs apply --id founder_operator_core` and optional progress updates).

---

## 7. Exact tests run

```bash
cd /Users/prady/Desktop/Clap/workflow-llm-dataset
python3 -m pytest tests/test_vertical_packs.py -v
```

**Result:** 5 passed (test_curated_pack_model, test_guided_path_generation, test_vertical_defaults_apply, test_first_value_milestone_tracking, test_weak_incomplete_path_behavior).

**Note:** Run CLI in an environment with project deps installed (e.g. `pip install -e .` then `workflow-dataset vertical-packs list`). Registry was updated to use `PROFILE_DOCUMENT_CALM` from default_experience.profiles (name was PROFILE_DOCUMENT_CALM, not PROFILE_DOCUMENT_HEAVY_CALM).

---

## 8. Exact remaining gaps for later refinement

- **Apply workday/experience/trust**: `apply` only sets active pack and prints recommended commands; it does not call workday preset, default_experience profile, or trust preset application. A later step can wire apply to existing `workflow-dataset day preset` / `workspace home --profile` / `trust preset` flows or add a single “apply all” with confirmation.
- **Progress from runs**: Milestones are not auto-marked from package first-run or value-packs first-run; progress is updated only via set_milestone_reached (or manual progress.json). Hook first-run and job/macro runs to set_milestone_reached when steps complete.
- **Blocked step detection**: blocked_step_index is stored but not inferred from queue/approval/executor state. Later: derive blocked step from “approval missing”, “run failed”, etc.
- **Custom curated packs**: Only built-in packs; no load from data/local/vertical_packs/packs.yaml (or similar).
- **Workspace home integration**: Default entry command is shown; workspace home could read active_curated_pack_id and suggest “first-value” or show next milestone.
- **Pane 1 scope-lock**: When vertical/scope-lock exists, link curated pack to scope (e.g. limit surfaces/jobs to vertical).
