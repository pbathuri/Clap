# M33A–M33D Workflow Episode Tracker + Cross-App Context Bridge

First-draft workflow-episode layer: detect in-progress multi-step workflows, link activity across file/app/browser/terminal, maintain live episode state, infer stage and handoff gaps. Local-only and explainable.

## Purpose

- **Detect** that the user is in the middle of a multi-step workflow.
- **Connect** activity across files, (when available) apps/browser/terminal, and project/session.
- **Maintain** a live workflow episode state (current episode, recent list, transitions).
- **Identify** likely workflow stage, next step, and missing handoff (missing approval, possible missing artifact).
- **Support** real-time assistance without losing project/session grounding.
- **Explain** inference with evidence; no hidden workflow inference.

## Models (Phase A)

- **WorkflowEpisode**: episode_id, started_at_utc, updated_at_utc, linked_activities, inferred_project, current_task_hypothesis, stage, stage_evidence, next_step_candidates, handoff_gaps, overall_confidence, evidence_summary, is_active, closed_at_utc, close_reason.
- **WorkflowStage**: unknown, intake, drafting, review, approval_decision, execution_followup, handoff_wrapup.
- **LinkedActivity**: event_id, source, timestamp_utc, activity_type, path, label, evidence.
- **InferredProjectAssociation**, **CurrentTaskHypothesis**, **HandoffGap** (kind: missing_artifact, missing_approval, likely_context_switch, stale_episode), **NextStepCandidate**, **EpisodeTransitionEvent**, **EpisodeCloseReason**.

## Bridge (Phase B)

- **build_active_episode(repo_root, event_log_dir, root_paths, max_events, min_activities)**: Load recent observation events from event log, optional live context for project hint; group into one episode with linked_activities and inferred_project; return episode or None if no coherence.

## Stage / handoff (Phase C)

- **infer_stage(episode)**: From activity_type and path extensions → intake, drafting, review, execution_followup, or unknown.
- **infer_handoff_gaps(episode, repo_root)**: From supervised_loop approval queue → missing_approval when pending items exist.
- **infer_next_step_candidates(episode)**: From stage and gaps → suggested next step (e.g. open review, check approval queue).

## CLI (Phase D)

- `workflow-dataset workflow-episodes now` — Build current episode from recent events, infer stage and gaps, persist and show summary.
- `workflow-dataset workflow-episodes recent [--limit N]` — List recent episodes.
- `workflow-dataset workflow-episodes explain [--latest] [--id <episode_id>]` — Explain episode (evidence, project, confidence).
- `workflow-dataset workflow-episodes stage [--latest] [--id <episode_id>]` — Show stage and handoff-gaps explanation.

## Mission control

- **workflow_episodes**: current_episode_id, current_stage, activities_count, project_label, likely_next_step, handoff_gaps_count, handoff_gaps_summary, recent_transitions_count, next_action.
- Report section: `[Workflow episodes] episode=… stage=… next_step=… handoff_gaps=…`

## Privacy / safety

- No new data collection; bridge uses only existing observation events (consent-bounded) and live context.
- No raw content; linked activities use event metadata only.
- Explainable: episode, stage, and handoff gaps carry evidence; `explain` and `stage` commands show why.
- Local-only: state under data/local/workflow_episodes.
