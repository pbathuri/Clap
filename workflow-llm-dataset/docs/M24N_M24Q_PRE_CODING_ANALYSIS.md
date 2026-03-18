# M24N–M24Q — Outcome Capture + Session Memory + Improvement Signals — Pre-coding analysis

## 1. What correction/memory/outcome state already exists

- **Corrections (M23M):** `CorrectionEvent` — correction_id, source_type (recommendation, routine, job_run, artifact_output, …), source_reference_id, operator_action (rejected, corrected, accepted_with_note, …), correction_category, original/corrected value, eligible_for_memory_update. Persisted in `data/local/corrections/events/`. `save_correction`, `get_correction`, `list_corrections`; `add_correction` in capture.
- **Feedback/trials (M19):** `TrialFeedbackEntry` — session_id, task_id, outcome_rating (completed|partial|failed), usefulness_rating 1–5, trust_rating. `TrialSessionSummary` — tasks_attempted/completed, top_praise/failure/requested. Stored in `data/local/trials/feedback` and `summaries`. `save_feedback_entry`, `save_session_summary`, `load_feedback_entries`, `load_session_summaries`.
- **Pilot (M21):** `PilotSessionRecord` — session_id, commands_run, artifacts_produced, blocking_issues, disposition. `PilotFeedbackRecord` — usefulness_score, trust_score, blocker_encountered, top_failure_reason. `session_log`: start_session, end_session, load_session, list_sessions. Persisted under `data/local/pilot/sessions/`.
- **Context (M23L):** WorkState snapshots — recent_successful_jobs, approval_blocked_jobs, etc. Save/load snapshot; no explicit “session outcome” model.
- **Acceptance (M24C):** Run results — run_id, scenario_id, outcome, ready_for_trial. `data/local/acceptance/runs/`.
- **Rollout (M24F):** State from acceptance — current_stage, blocked_items, next_required_action. `data/local/rollout/`.
- **Job packs:** `SpecializationMemory` per job — last_successful_run, recurring_failure_notes. No cross-session outcome aggregation.

## 2. What is missing for real session-level outcome capture

- **Unified session outcome model:** A single record type that ties session_id to what ran (jobs/routines/macros), what was useful vs blocked vs incomplete, operator-confirmed usefulness, and follow-up recommendations.
- **Task outcome and artifact outcome:** First-class records (task/artifact level) linked to a session, with outcome kind and cause.
- **Blocked cause taxonomy:** Stored with outcomes (e.g. approval_missing, job_not_found, timeout, user_abandoned) for pattern detection.
- **Session memory store:** Aggregated session summaries, outcome histories, repeated block patterns, repeated success patterns, and “most useful” jobs/macros/artifacts per pack.
- **Improvement signals:** Explicit generator for “job repeatedly fails for this pack”, “macro highly useful in this context”, “recurring blocker”, “first-value flow weak/strong”.
- **Bridge:** From session outcomes to corrections (suggest only), trust review (expose only), pack refinement suggestions, and next-run recommendations.
- **Outcomes CLI and mission control:** Commands (outcomes latest, session --id, patterns, recommend-improvements) and mission control section for latest outcomes, recurring blockers, high-value jobs, next improvement action.

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|---------|
| Create | `src/workflow_dataset/outcomes/models.py` | SessionOutcome, TaskOutcome, ArtifactOutcome, BlockedCause enum/struct, UsefulnessConfirmation, IncompleteWork, FollowUpRecommendation. |
| Create | `src/workflow_dataset/outcomes/store.py` | Persist under data/local/outcomes/ (sessions/, tasks/, artifacts/). save_session_outcome, get_session_outcome, list_session_outcomes, append_task_outcome. |
| Create | `src/workflow_dataset/outcomes/patterns.py` | repeated_block_patterns(), repeated_success_patterns(), most_useful_per_pack() from store. |
| Create | `src/workflow_dataset/outcomes/signals.py` | generate_improvement_signals() — job_fails_repeatedly, macro_highly_useful, recurring_blocker, first_value_flow_weak. |
| Create | `src/workflow_dataset/outcomes/bridge.py` | outcome_to_correction_suggestions(), pack_refinement_suggestions(), next_run_recommendations(). |
| Create | `src/workflow_dataset/outcomes/report.py` | format_session_outcome(), format_patterns(), format_recommend_improvements(). |
| Create | `src/workflow_dataset/outcomes/__init__.py` | Exports. |
| Modify | `src/workflow_dataset/cli.py` | outcomes group: latest, session --id, patterns, recommend-improvements. |
| Modify | `src/workflow_dataset/mission_control/state.py` | outcomes section: latest_session_outcomes, recurring_blockers, high_value_jobs_macros, next_recommended_improvement. |
| Modify | `src/workflow_dataset/mission_control/report.py` | Outcomes section in report. |
| Create | `docs/M24N_M24Q_OUTCOMES.md` | Outcome model, store, patterns, signals, bridge, CLI, constraints. |
| Create | `tests/test_outcomes.py` | Persistence, pattern detection, repeated blocker report, session summary, recommendation generation. |

## 4. Safety/risk note

- All outcome data is local under `data/local/outcomes/`. No hidden continual learning; no automatic trust or approval changes. Improvement signals and recommendations are explicit and advisory only; operator decides. Bridge to corrections only proposes; no auto-apply. Session outcome capture is opt-in or triggered by existing flows (e.g. job run, pilot end) — no background scraping.

## 5. What this block will NOT do

- No hidden continual learning; no automatic trust upgrades; no opaque model mutation. No rebuild of corrections/trust/acceptance/rollout. No auto-apply of corrections from outcomes. No cloud sync of outcomes. No stopping at thin report-only outputs — store and signals are real and actionable within the constraints above.
