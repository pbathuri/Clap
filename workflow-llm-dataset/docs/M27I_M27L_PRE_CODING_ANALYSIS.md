# M27I–M27L — Triggered Replanning + Impact / Progress Board — Pre-coding analysis

## 1. What triggers/progress/outcome state already exists

- **context/drift.py** — ContextDrift (newly_recommendable_jobs, newly_blocked_jobs, approvals_changed, summary); compare_snapshots(older, newer). No explicit "replan" signal.
- **context/triggers.py** — TriggerResult (job_or_routine_id, trigger_type, triggered, reason, blocker); evaluate_trigger_for_job. Job/routine triggers only; no plan-level trigger.
- **planner/store.py** — save/load current_goal, save/load latest_plan (single plan). No plan history or prior plan for diff.
- **planner/schema.py** — Plan (steps, edges, checkpoints, blocked_conditions, expected_artifacts), PlanStep, BlockedCondition. No replan metadata.
- **outcomes/** — SessionOutcome, TaskOutcome, outcome history (entries with session_id, disposition, blocked_count, blocked_causes, source_refs). patterns: repeated_block_patterns, repeated_success_patterns. signals: generate_improvement_signals (recurring_blocker, job_fails_repeatedly, macro_or_job_highly_useful, first_value_flow_weak).
- **mission_control** — goal_plan: active_goal, latest_plan_id, plan_step_count, blocked_step_count, next_checkpoint_index, expected_artifacts. No replan-needed or progress board.

## 2. What is missing for real triggered replanning and impact visibility

- **Replan signals** — Explicit signal types (new_blocker, capability_changed, milestone_slipped, repeated_failed_action, new_skill_accepted, artifact_updated, context_drift_affecting_goal) and a store/generator that produces them from outcomes + planner + context + teaching.
- **Replan recommendation** — Recommend replan (yes/no + reason); compare prior plan vs current/candidate plan; explain why replan suggested; show changed steps/checkpoints/blockers. Requires storing a "prior plan" when recommending replan.
- **Impact/progress model** — Goals completed, actions executed, blockers unresolved, artifacts produced, repeated success patterns, stalled vs advancing, session-to-session movement. No first-class progress entity today.
- **Progress board** — Single view: active projects, project health, stalled vs advancing, recent replans, recurring blockers, positive impact signals, next intervention candidate.
- **CLI** — progress board, progress project --id, replan recommend/diff/accept. No replan or progress commands yet.
- **Mission control** — replan_needed_projects, stalled_projects, advancing_projects, recent_impact_signals, top_intervention_candidate.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `progress/__init__.py` |
| Create | `progress/models.py` — ReplanSignal, ProgressSignal, project_id semantics (default or goal-derived). |
| Create | `progress/store.py` — progress dir, save/load prior plan, save/load replan signals, list projects. |
| Create | `progress/signals.py` — generate_replan_signals (from outcomes, planner, context drift, teaching skills). |
| Create | `progress/recommendation.py` — recommend_replan(project_id), compare_plans(prior, new), explain_replan, format_plan_diff. |
| Create | `progress/board.py` — build_progress_board(), format_progress_board(); stalled/advancing from outcomes + plan blocked. |
| Modify | `cli.py` — progress_group: board, project --id; replan_group: recommend, diff, accept. |
| Modify | `mission_control/state.py` — progress_replan section. |
| Modify | `mission_control/report.py` — [Progress / Replan] section. |
| Create | `tests/test_progress_replan.py` |
| Create | `docs/M27I_M27L_PROGRESS_REPLAN.md` |

## 4. Safety/risk note

- No auto-replan or auto-execute: recommend_replan and replan accept are operator-facing; accept means "record that operator acknowledged" or "store current as new baseline", not automatic plan replacement without confirmation.
- Evidence-based only: signals come from existing outcomes, planner state, context drift, teaching; no hidden analytics or cloud.
- Prior plan storage is local (data/local/progress); operator can inspect and delete.

## 5. What this block will NOT do

- No hidden autonomous replanning; no auto-execution of new plans without explicit operator flow.
- No cloud analytics or vanity dashboards only; all data local.
- No rebuild of context, outcomes, planner, or mission control; additive only.
- No first-class project/case registry from Pane 1 required; project_id can be "default" or goal-derived.
