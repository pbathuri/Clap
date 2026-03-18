# M33H.1 — Workflow Bundles + Stall Recovery Paths

Extension to the supervised real-time workflow runner (M33E–M33H): reusable workflow bundles, stall detection and recovery paths, stronger alternate-path recommendations, and clearer operator-facing escalation explanations.

## Workflow bundles

- **Location**: `data/local/live_workflow/bundles/` (one YAML or JSON file per bundle).
- **Model**: `WorkflowBundle` — `bundle_id`, `label`, `description`, `goal_template`, `routine_id`, `plan_ref`, `alternate_goals[]`, `recovery_suggestions[]`, `tags[]`.
- **CLI**: `workflow-dataset live-workflow bundles` (list), `workflow-dataset live-workflow now --bundle <id>` (start from bundle).
- **Step generation**: `generate_live_workflow_steps(bundle_id=...)` loads the bundle and uses `goal_template` / `routine_id`; populates `alternate_path_recommendations` from `alternate_goals`.

## Stall detection and recovery

- **Detection**: `detect_stall(run, last_activity_utc=..., idle_threshold_seconds=600)` uses `run.updated_utc` or `run.last_activity_utc`; if idle time ≥ threshold and state is ACTIVE, sets `stalled=True` and fills `suggested_recovery_paths` and `alternate_paths`.
- **Recovery paths**: Escalate one tier, open planner with current goal, and (if run has a bundle) bundle `recovery_suggestions`.
- **CLI**: `workflow-dataset live-workflow stall [--latest] [--idle-minutes 10]` — shows stalled flag, reason, recovery paths, alternate paths.
- **Mission control**: `live_workflow_state` includes `stall_detected`, `stall_reason`, `recovery_paths_count` when a run is present; report shows stall line when detected.

## Stronger alternate-path recommendations

- **Run fields**: `alternate_path_recommendations` (list of dicts: `label`, `goal_or_ref`, `reason`, `priority`) and `alternate_path_summary` (string).
- **From bundle**: When started from a bundle, alternate goals from the bundle are added as high-priority recommendations.
- **Fallback**: When no bundle, a single recommendation “Refine goal or try a different routine” is added.

## Escalation explanation

- **Model**: `EscalationExplanation` — `from_tier`, `to_tier`, `reason_code`, `operator_message`, `suggested_action`.
- **Reason codes**: `user_requested`, `stall_detected`, `blocked_step`, `repeated_hint_dismissed`.
- **CLI**: `workflow-dataset live-workflow explain-escalation --from <tier> --to <tier> --reason <code> [--step-label "..."]` — prints why escalation happened and what to do next.
- **API**: `explain_escalation(from_tier, to_tier, reason_code=..., step_label=...)` and `build_escalation_explanation(...)` in `live_workflow.escalation`.

## Run state

- **New state**: `WorkflowRunState.STALLED` (available for future use; stall detection currently only fills `StallDetectionResult`, not the run state).
- **New run fields**: `last_activity_utc`, `bundle_id`, `alternate_path_recommendations`.

## Next recommended step for the pane

- **Wire stall into run state (optional)**: When `detect_stall` returns `stalled=True`, optionally set `run.state = WorkflowRunState.STALLED` and persist, so mission control and UI can show “stalled” without recomputing.
- **Episode integration**: When the workflow-episode tracker is available, feed episode progress into `last_activity_utc` or step advancement so stall detection reflects real activity.
- **Action card from recovery path**: Allow “Create action card from this recovery path” so a `StallRecoveryPath` becomes an `ActionCard` with the same handoff.
