# M47A–M47D Vertical Excellence — Deliverable

## 1. Files modified

- **workflow-llm-dataset/src/workflow_dataset/cli.py**  
  Added `vertical_excellence_group` and commands: `first-value`, `path-report`, `friction-points`, `recommend-next`.
- **workflow-llm-dataset/src/workflow_dataset/mission_control/state.py**  
  Added `vertical_excellence_state` from `vertical_excellence_slice(repo_root)`.
- **workflow-llm-dataset/src/workflow_dataset/mission_control/report.py**  
  Added "[Vertical excellence]" section: vertical, first_value_stage, strongest_friction, blocked_cases, next action, path_improvement.

## 2. Files created

- **workflow-llm-dataset/docs/M47A_M47D_BEFORE_CODING_ANALYSIS.md** — Before-coding analysis (path, friction, file plan, safety, principles, out-of-scope).
- **workflow-llm-dataset/src/workflow_dataset/vertical_excellence/__init__.py** — Package exports.
- **workflow-llm-dataset/src/workflow_dataset/vertical_excellence/models.py** — FirstValuePathStage, RepeatValuePathStage, CriticalUserJourney, FrictionPoint, AmbiguityPoint, MissingNextStepSignal, ExcellenceTarget.
- **workflow-llm-dataset/src/workflow_dataset/vertical_excellence/path_resolver.py** — get_chosen_vertical_id, build_first_value_path_for_vertical, build_repeat_value_path_for_vertical.
- **workflow-llm-dataset/src/workflow_dataset/vertical_excellence/compression.py** — assess_first_value_stage, list_friction_points, list_ambiguity_points, list_blocked_first_value_cases.
- **workflow-llm-dataset/src/workflow_dataset/vertical_excellence/recommend_next.py** — recommend_next_for_vertical (NextRecommendation).
- **workflow-llm-dataset/src/workflow_dataset/vertical_excellence/reports.py** — format_first_value_path_report, format_friction_point_report, format_recommend_next.
- **workflow-llm-dataset/src/workflow_dataset/vertical_excellence/mission_control.py** — vertical_excellence_slice.
- **workflow-llm-dataset/tests/test_vertical_excellence.py** — Tests for path resolver, stage, friction, ambiguity, blocked cases, recommend-next, slice, reports, no-active-vertical.
- **workflow-llm-dataset/docs/M47A_M47D_VERTICAL_EXCELLENCE_DELIVERABLE.md** — This file.

## 3. Exact CLI usage

```bash
# Current first-value stage and next step
workflow-dataset vertical-excellence first-value
workflow-dataset vertical-excellence first-value --repo /path/to/repo
workflow-dataset vertical-excellence first-value --json

# First-value path report (entry, steps, stage)
workflow-dataset vertical-excellence path-report
workflow-dataset vertical-excellence path-report --repo /path/to/repo

# Friction points and blocked first-value cases
workflow-dataset vertical-excellence friction-points
workflow-dataset vertical-excellence friction-points --json

# Recommend next action for the chosen vertical
workflow-dataset vertical-excellence recommend-next
workflow-dataset vertical-excellence recommend-next --json
```

## 4. Sample first-value path report

```
[Vertical excellence] First-value path report
vertical_id=founder_operator_core
stage: not_started (step 0/6)
next_command_hint: workflow-dataset profile bootstrap

path_id=founder_operator_core_first_value_fallback
entry_point=workflow-dataset profile bootstrap
  step 1: Bootstrap profile  # workflow-dataset profile bootstrap
  step 2: Check runtime mesh  # workflow-dataset runtime backends
  step 3: Onboard approvals  # workflow-dataset onboard status
  step 4: Show recommended job pack  # workflow-dataset jobs list
  step 5: Show inbox  # workflow-dataset inbox
  step 6: Run one safe simulate-only routine  # ...
```

## 5. Sample friction-point report

```
[Vertical excellence] Friction points report
friction_count=5
blocked_first_value_cases=0

  failure_step_1  kind=blocked_recovery  step=1
    label: Bootstrap fails
    remediation: Run from repo root
    escalation: workflow-dataset profile bootstrap
  queue_to_action_handoff  kind=handoff_overhead  step=0
    label: Queue to action handoff
    remediation: Use vertical-speed action-route for top queue item to get single command.
```

## 6. Sample next-step recommendation output

```
[Vertical excellence] Recommend next
command: workflow-dataset value-packs first-run --id founder_operator_core
label: Start first-value path
rationale: Start here to reach first useful artifact in this vertical.
```

Or when blocked:

```
[Vertical excellence] Recommend next
command: workflow-dataset onboard status
label: Recover from blocked first-value
rationale: Run onboard approve with path_repo scope
```

## 7. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_vertical_excellence.py -v
```

Tests: test_get_chosen_vertical_id_default, test_build_first_value_path_for_vertical_fallback, test_build_repeat_value_path_for_vertical, test_assess_first_value_stage_not_started, test_list_friction_points, test_list_ambiguity_points, test_list_blocked_first_value_cases_no_vertical, test_recommend_next_for_vertical, test_vertical_excellence_slice, test_format_first_value_path_report, test_format_friction_point_report, test_format_recommend_next, test_no_active_project_uses_default_vertical.

## 8. Remaining gaps for later refinement

- **Progress sync:** vertical_packs progress (reached_milestone_ids, blocked_step_index) is not auto-updated when user runs commands; a future hook or post-step recorder could keep stage in sync.
- **Chosen vertical = production cut only:** When production cut is not set, we use active pack or default; optionally lock production cut when setting vertical excellence so the “chosen vertical” is always cut-backed.
- **First-value path per vertical:** Fallback path is generic (operator_quickstart); vertical-specific paths from vertical_packs.paths.build_path_for_pack are used when the pack has a golden bundle or first_run_flow; more packs can get dedicated first-value steps.
- **Recommend-next vs mission_control next_action:** mission_control next_action remains product/eval-focused; vertical_excellence recommend-next is first-value/blocked-focused; a single “next” surface could merge both with a “vertical first” vs “product next” toggle.
- **Blocked detection:** Blocked state today comes from vertical_packs progress (blocked_step_index); additional signals (e.g. approval blocked, runtime down) could be folded into list_blocked_first_value_cases.
- **Repeat-value path in reports:** Repeat-value path (high-frequency workflows) is built and exposed in the slice but not yet in a dedicated path-report subsection; could add `vertical-excellence repeat-value-report`.
