# M27I–M27L — Triggered Replanning + Impact / Progress Board

First-draft progress and replanning layer: notice change, recommend replan, compare plans, show progress and impact. Local, evidence-based; no auto-replan.

---

## 1. Files modified

- **cli.py** — Added `progress_group` (board, project) and `replan_group` (recommend, diff, accept).
- **mission_control/state.py** — Added **progress_replan** section: replan_needed_projects, stalled_projects, advancing_projects, recent_replan_signals_count, recurring_blockers_count, positive_impact_count, next_intervention_candidate.
- **mission_control/report.py** — Added **[Progress / Replan]** section.

## 2. Files created

- **docs/M27I_M27L_PRE_CODING_ANALYSIS.md** — Existing triggers/progress, gaps, file plan, safety, out-of-scope.
- **progress/__init__.py** — Public API.
- **progress/models.py** — ReplanSignal, REPLAN_SIGNAL_TYPES, ProgressSignal.
- **progress/store.py** — get_progress_dir, save/load_prior_plan, save/load_replan_signals, list_projects (data/local/progress/).
- **progress/signals.py** — generate_replan_signals (from plan blocked, outcomes patterns, context drift, teaching skills).
- **progress/recommendation.py** — recommend_replan, compare_plans, explain_replan, format_plan_diff.
- **progress/board.py** — build_progress_board, format_progress_board.
- **tests/test_progress_replan.py** — Signals, store, compare_plans, explain, format_diff, board.
- **docs/M27I_M27L_PROGRESS_REPLAN.md** — This doc.

## 3. Exact CLI usage

```bash
# Progress board
workflow-dataset progress board
workflow-dataset progress board --output board.txt

# Project progress
workflow-dataset progress project --id default
workflow-dataset progress project --id founder_case_alpha

# Replan recommend (saves signals for board)
workflow-dataset replan recommend
workflow-dataset replan recommend --project founder_case_alpha

# Plan diff (prior vs current)
workflow-dataset replan diff --project default

# Accept: store current plan as prior baseline
workflow-dataset replan accept --project default
```

Mission control: `workflow-dataset mission-control` shows [Progress / Replan] replan_needed=, stalled=, advancing=, blockers=, impact=, next_intervention=.

## 4. Sample replan signal

```json
{
  "signal_type": "new_blocker_detected",
  "project_id": "default",
  "reason": "Plan has blocked condition",
  "ref": "approval_scope",
  "evidence": ["step_index=1"],
  "created_at": "2026-03-16T12:00:00Z"
}
```

Other types: `repeated_failed_action`, `capability_changed`, `new_skill_accepted`.

## 5. Sample plan diff output

```
=== Plan diff ===

Steps: prior=3  new=4
Blocked: prior=0  new=1

Steps added: Generate report
Blocked conditions changed: yes
Checkpoints changed: yes
```

## 6. Sample progress board output

```
=== Impact / Progress board ===

[Active projects] default
[Project health] default=blocked

[Stalled] (none)
[Advancing] (none)
[Replan needed] default

[Recurring blockers] 2
[Positive impact signals] 1

[Next intervention] default

[Recent replan signals]
  - new_blocker_detected: Plan has blocked condition
  - repeated_failed_action: Recurring block: approval_missing
```

## 7. Exact tests run

```bash
python3 -m pytest tests/test_progress_replan.py -v
```

Covers: ReplanSignal roundtrip, save/load prior plan, save/load replan signals, list_projects, compare_plans, explain_replan, format_plan_diff, build_progress_board, format_progress_board, recommend_replan.

## 8. Exact remaining gaps for later refinement

- **Project registry** — No first-class project/case from Pane 1; project_id is "default" or from prior_plans dir. Add project registry and link to sessions/goals when present.
- **Milestone semantics** — "milestone_slipped" signal type exists but not yet derived from dates or explicit milestones.
- **Artifact-updated signal** — "artifact_updated" not yet generated from artifact or file events.
- **Replan accept semantics** — Accept stores current as prior; no automatic recompile or executor hook. Operator must recompile if they want a new plan.
- **Stalled threshold** — Stalled = 2+ sessions with disposition fix/pause and blocked_count > 0; may need configurable threshold.
- **Next action integration** — Mission control next_action does not yet factor in next_intervention_candidate from progress_replan.
