# M29I–M29L Activity Timeline + Review Studio + Intervention Inbox — Pre-Coding Analysis

## 1. What review/inbox/timeline-like surfaces already exist

- **Approval queue (supervised_loop)**: `list_pending_sorted()`, `get_item()`, `cmd_queue`; status pending/approved/rejected/deferred; approve/reject/defer via `agent-loop approve|reject|defer`; queue stored in JSON; no unified “inbox” across domains.
- **Daily inbox (daily/inbox.py)**: `build_daily_digest()` — work state, what_changed, inbox_items (jobs/routines with reason/trust/blockers), blocked_items, reminders, approvals_needing_refresh, trust_regressions, recent_successful_runs, top_next_recommended, corrections; `format_inbox_report()`; CLI `workflow-dataset inbox`; digest is a snapshot, not a persistent intervention list.
- **Review queue (release)**: `review queue-status`, staging board (stage-package, stage-artifact, staging-board, remove-item); workspace/package review state; not “intervention” items, more release staging.
- **Mission control**: `get_mission_control_state()` aggregates product_state, evaluation_state, development_state, incubator_state, goal_plan, project_case, progress_replan, executor, supervised_loop, worker_lanes, human_policy, daily_inbox, portfolio_router; `format_mission_control_report()`; `recommend_next_action()`; no single “intervention inbox” or “activity timeline.”
- **Progress board**: `build_progress_board()` — stalled_projects, replan_needed, next_intervention_candidate; `report_needing_intervention()`; intervention playbooks; no unified inbox item type.
- **Portfolio**: top_intervention, needs_intervention_count; reports; no timeline.
- **Teaching/skills**: `list_candidate_skills(status=draft)`, accept_skill, reject_skill; skill review is separate from approval queue.
- **Executor**: `list_runs()`, run state (blocked, completed); resume-from-blocked; no shared “blocked run” inbox.
- **Human policy**: overrides list, board; no “policy exception” inbox item.
- **Agent audit log (agent/audit_log.py)**: ActionLogRecord (proposed/approved/rejected/executed/failed); append_log; device-local; not aggregated into a unified timeline.
- **Trial events (feedback/trial_events.py)**: record_trial_event, load_trial_events; release/task events; not system-wide timeline.
- **Corrections**: CorrectionEvent, add_correction; source_type, operator_action; not in a single review list.
- **Outcome history (outcomes/store)**: outcome_history entries; not timeline events.
- **Workspace timeline (release/workspace_rerun_diff)**: workspace_timeline() — runs with timestamp, run_id, artifact count; workflow-scoped only.

So: **existing** = approval queue, daily digest, review queue/staging, mission control aggregate, progress intervention candidate, portfolio top intervention, skill candidates, executor runs, policy board, audit log, trial events, corrections, outcome history, workspace timeline. **Missing** = one unified activity timeline (all event types, ordered), one intervention inbox (all review-worthy item kinds with accept/reject/defer), and a single review studio (inspect, why it matters, link to project/session/plan/run/lane/pack, operator notes).

---

## 2. What is missing for a real intervention studio

- **Unified timeline**: Single ordered stream of events across project, plan, approval queue, executor, lanes, skills, policy, artifacts; with event kind, timestamp, entity refs, human-readable summary; filterable by project/lane/kind.
- **Unified intervention inbox**: One list of “needs operator attention” items: approval queue pending, blocked runs, lane results awaiting acceptance, replan recommendations, skill draft candidates, policy exceptions/overrides to review, stalled-project interventions, important artifacts to review; each with stable id, kind, summary, priority, created_at, linked refs.
- **Review studio flows**: Inspect item → see why it matters → accept/reject/defer/escalate → link to project/session/plan/run/lane/pack → record operator notes; reuse existing approve/reject/defer where they exist, add “inbox item” wrapper and navigation.
- **What changed over time**: Timeline “diff” or “since” view (e.g. since last visit) so operator sees what happened in human-readable form.
- **Quick intervention**: From inbox or timeline, one command to accept/reject/defer with optional note; and “next recommended intervention” that mission control can surface.

---

## 3. Exact file plan

| Area | Action | Path |
|------|--------|------|
| Timeline model | Create | `src/workflow_dataset/review_studio/models.py` — TimelineEvent (event_id, kind, timestamp_utc, summary, entity_refs, project_id, pack_id, lane_id, run_id, session_id, plan_ref, artifact_ref, details), EVENT_KINDS (project_*, plan_*, action_queued/approved/rejected/deferred, executor_*, lane_*, skill_*, pack_*, policy_override_*, artifact_*) |
| Inbox model | Create | same file — InterventionItem (item_id, kind, status, summary, created_at, priority, entity_refs, source_ref, operator_notes, decided_at, decision_note) |
| Timeline build | Create | `src/workflow_dataset/review_studio/timeline.py` — build_timeline(repo_root, project_id?, limit, since_iso?) → list[TimelineEvent]; collect from project_case, supervised_loop queue/handoffs, executor list_runs, progress replan_signals, teaching list_skills, human_policy overrides, outcomes history, corrections, audit log where available |
| Inbox build | Create | `src/workflow_dataset/review_studio/inbox.py` — build_inbox(repo_root, status?, limit?) → list[InterventionItem]; collect approval queue pending, blocked runs, lane results (if any), replan recommendations, skill drafts, policy overrides (active), stalled next_intervention_candidate; persist optional inbox snapshot for “oldest unresolved” |
| Review studio | Create | `src/workflow_dataset/review_studio/studio.py` — get_item(item_id, repo_root), inspect_item(item_id), accept_item(item_id, note), reject_item(item_id, note), defer_item(item_id, note, revisit_after), link_entity_refs(item) → project/session/plan/run/lane/pack; delegate to agent-loop approve/reject/defer, teaching accept/reject, executor resume-from-blocked, etc. |
| Store | Create | `src/workflow_dataset/review_studio/store.py` — optional inbox_snapshot.json for “last seen” / oldest unresolved; operator_notes per item_id in notes store |
| CLI | Create | `src/workflow_dataset/review_studio/cli.py` — cmd_timeline_latest, cmd_timeline_project, cmd_inbox_list, cmd_inbox_review, cmd_inbox_accept, cmd_inbox_reject, cmd_inbox_defer |
| Main CLI | Modify | `src/workflow_dataset/cli.py` — add timeline_group, inbox_group (or review_studio_group with timeline + inbox subcommands) |
| Mission control | Modify | `src/workflow_dataset/mission_control/state.py` — add review_studio block: recent_timeline_count, inbox_count, urgent_count, oldest_unresolved_id, next_recommended_intervention_id |
| Mission control report | Modify | `src/workflow_dataset/mission_control/report.py` — add [Review studio] section: timeline summary, inbox count, oldest, next intervention |
| Tests | Create | `tests/test_review_studio.py` — timeline build, inbox build, review accept/reject/defer, empty state |
| Docs | Create | `docs/M29I_M29L_ACTIVITY_TIMELINE_REVIEW_STUDIO.md` |

---

## 4. Safety/risk note

- **Read-first aggregation**: Timeline and inbox are built by reading existing stores (queue, runs, progress, skills, policy, project_case); no new hidden writes to approval/executor/teaching; review actions delegate to existing flows (approve/reject/defer, accept_skill, resume-from-blocked).
- **No cloud**: All local; no telemetry or SaaS.
- **Explicit intervention**: Operator explicitly runs inbox list/review/accept/reject/defer; no auto-approval or auto-defer.
- **Notes**: Operator notes stored locally; optional; no PII requirement.

---

## 5. What this block will NOT do

- **No replacement** of approval queue, daily inbox, mission control, or progress board; additive layer that aggregates and adds unified timeline + intervention inbox + review flows.
- **No hidden action processing**: All actions (accept/reject/defer) go through existing APIs or explicit CLI.
- **No cloud monitoring** or external dependencies.
- **No vanity event log**: Timeline events are meaningful system events (project, plan, action, run, lane, skill, policy, artifact); not low-level UI events.
- **No full audit trail**: Timeline is first-draft “recent activity”; full audit remains in domain stores (queue, runs, corrections, etc.).
