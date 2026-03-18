# M33A–M33D Workflow Episode Tracker + Cross-App Context Bridge — Before Coding

## 1. What live-context and observation pieces already exist

### Observation (observe/*)
- **ObservationEvent**: event_id, source (file | app | browser | terminal | calendar | teaching), timestamp_utc, device_id, tier, payload. Normalized keys: activity_type, project_hint, session_hint, redaction_marker, provenance.
- **Event log**: events_YYYYMMDD.jsonl under a log dir; `load_all_events(log_dir, source_filter, max_events)` loads newest-first.
- **File collector**: implemented (metadata only: path, filename, extension, size, mtime, is_dir; no content). Other sources (app, browser, terminal, calendar, teaching) are stubs.
- **Runtime**: `run_observation()` respects observation_enabled, allowed_sources, file_root_paths, boundaries; writes events to log.
- **Boundaries**: check_source_enabled, get_source_health, consent/boundary enforcement per source.

### Live context (live_context/*)
- **ActiveWorkContext**: context_id, timestamp_utc, focus_target, inferred_project, inferred_task_family, work_mode, activity_mode, focus_state, overall_confidence, evidence_summary, source_contributions, is_stale, last_signal_utc, session_hint, project_hint.
- **Fusion**: `fuse_active_context(events, root_paths, graph_projects, graph_routines, session_hint, project_hint)` — project from file events (path under root), rank by count; task family from graph routines; work_mode from distribution; activity_mode from file extensions (writing/reviewing/planning/coding/admin); focus_state (single_file, project_browse, scattered).
- **Session detector**: `detect_transitions(current, previous)` → SessionTransitionEvent (session_start, project_switch, deep_work_continuation, interruption, return_to_work).
- **State**: get_live_context_state(repo_root), save_live_context_state(context), get_recent_transitions(), append_transition(); persisted under data/local/live_context (current.json, transitions.jsonl).

### Personal / session / project
- **Personal graph**: work graph nodes, ingest_file_events, graph_reports (list_recent_routines, list_strong_patterns), graph_store (list_suggestions).
- **Session** (session/*): Session model — session_id, value_pack_id, active_tasks, current_artifacts, state (open/closed/archived).
- **Project case** (project_case/*): Project, Goal, store (get_projects_dir, load_project, list_projects, current project).

### Planner / executor / review / trust
- **Planner**: compile_goal_to_plan, store (load_current_goal, load_latest_plan).
- **Executor**: runs, checkpoints, approval flow.
- **Review studio**: intervention inbox (approval_queue, blocked_run, replan, skills, policy); timeline from handoffs, executor runs; digests (what_needs_approval, what_is_blocked).
- **Supervised loop**: handoffs store (load_handoffs), approval queue.
- **Trust / approvals**: approval registry, path/app/scope allowlists.

---

## 2. What is missing for real workflow-episode tracking

- **First-class workflow episode**: A bounded “in-progress workflow” entity with identity, time window, linked activities across sources, inferred stage, and evidence. Live context is a point-in-time snapshot; we need an episode that can span multiple context snapshots and multiple apps/files.
- **Cross-app context bridge**: Logic that takes recent events from file + (when available) app/browser/terminal/notes and groups them into one or more candidate episodes with evidence (why these items belong together: same project, same time window, same session, routine prior).
- **Workflow stage taxonomy**: Explicit stages (e.g. intake/gathering, drafting, review, approval/decision, execution/follow-up, handoff/wrap-up) with first-draft inference from activity mix and artifacts.
- **Handoff gap / next-step / missing-artifact detection**: Inference of “likely missing artifact”, “likely missing approval”, “likely next app/tool/context switch” from episode state + review_studio/supervised_loop/planner state.
- **Episode lifecycle**: Episode start/transition/close events; persistence of current episode and recent closed episodes for explain and reports.
- **Stale / no-episode behavior**: When there is no coherent multi-step workflow (e.g. idle or single isolated action), explicit “no active episode” or “episode closed” with reason.

---

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|---------|
| Create | `src/workflow_dataset/workflow_episodes/__init__.py` | Package exports. |
| Create | `src/workflow_dataset/workflow_episodes/models.py` | WorkflowEpisode, WorkflowStage (enum), LinkedActivity, InferredProjectAssociation, CurrentTaskHypothesis, HandoffGap, NextStepCandidate, EpisodeTransitionEvent, EpisodeCloseReason; confidence/evidence fields. |
| Create | `src/workflow_dataset/workflow_episodes/bridge.py` | Cross-app bridge: load recent events (observe.load_all_events), optional live context (live_context.get_live_context_state), optional session/project/graph; produce active_workflow_episode (or None), candidate_episode_associations, evidence (why items belong together). |
| Create | `src/workflow_dataset/workflow_episodes/stage_detection.py` | Infer stage from linked activities + live context; infer next_step_candidates; infer handoff_gaps (missing_artifact, missing_approval, likely_context_switch). |
| Create | `src/workflow_dataset/workflow_episodes/store.py` | Persist current episode, recent episodes list, episode transitions; get_current_episode(), save_current_episode(), list_recent_episodes(), append_episode_transition(). |
| Create | `src/workflow_dataset/workflow_episodes/explain.py` | build_episode_explanation(episode), build_stage_explanation(episode), build_handoff_gaps_explanation(episode). |
| Extend | `src/workflow_dataset/cli.py` | Add workflow_episodes group: now, recent, explain --latest, stage --latest. |
| Extend | `src/workflow_dataset/mission_control/state.py` | Add workflow_episodes slice: current_episode_id, current_stage, likely_next_step, handoff_gaps_summary, recent_episode_transitions. |
| Extend | `src/workflow_dataset/mission_control/report.py` | Add [Workflow episodes] section from state. |
| Create | `tests/test_workflow_episodes.py` | Episode model creation, bridge with mock events, stage detection, handoff-gap detection, stale/no-episode. |
| Create | `docs/M33A_M33D_WORKFLOW_EPISODES.md` | Overview, model, bridge, stage, CLI, mission control, privacy. |
| Create | `docs/M33A_M33D_DELIVERABLE.md` | Files modified/created, CLI usage, sample episode, sample stage/handoff output, tests run, gaps. |

---

## 4. Safety/risk note

- **Bounded input**: Bridge uses only existing observation events (consent-bounded), live context, session/project/graph; no new raw capture. No screen scraping or uncontrolled app surveillance.
- **Explainable**: Episode, stage, and handoff-gap outputs carry evidence/reason strings; no hidden inference.
- **Local-only**: All state under data/local/workflow_episodes; no cloud activity stitching.
- **No bypass of trust/approval**: Handoff-gap “missing approval” is advisory (from review_studio/supervised_loop); we do not auto-approve or execute.

---

## 5. Privacy/consent boundaries

- **No new collection**: Workflow episodes consume only data already produced under existing observation and graph consent (same as M32 live context).
- **No raw content**: Linked activities reference event metadata (path, source, timestamp, activity_type) and optional bounded labels; no file body or clipboard.
- **Inspectable**: User can run `workflow-episodes explain --latest` and see why an episode was inferred and what evidence supports stage/handoff gaps.
- **Retention**: Episode and transition persistence follows same local-first policy as live_context; no exfiltration.

---

## 6. What this block will NOT do

- Will **not** capture uncontrolled raw content (no screen scraping, no arbitrary surveillance).
- Will **not** implement real app/browser/terminal collectors (those remain stubs; bridge will work with file + whatever events exist).
- Will **not** cloud-stitch or sync episodes across devices.
- Will **not** hide inference: stage and handoff gaps are explicit and explainable.
- Will **not** auto-approve or execute; “missing approval” is a suggested next step only.
- Will **not** rebuild observe, personal, session, or live_context; we consume their outputs.

---

*Proceeding to implementation (Phases A–E) only after this document is agreed. No code before this analysis is complete.*
