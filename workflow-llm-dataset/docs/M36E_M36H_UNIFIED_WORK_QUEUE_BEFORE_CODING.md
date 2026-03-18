# M36E–M36H Unified Work Queue + Cross-System Action Router — Before Coding

## 1. What queue / inbox / review surfaces already exist

| Surface | Location | Item type | Sources / content | CLI / entry |
|--------|----------|-----------|-------------------|-------------|
| **Intervention inbox** | review_studio/inbox.py | InterventionItem (item_id, kind, status, summary, priority, entity_refs, source_ref) | Approval queue (supervised_loop), blocked runs (executor), replan (progress board), skill candidates (teaching), policy overrides (human_policy), stalled (live_workflow), graph routine/pattern review (personal) | `inbox list` (workspace area: intervention_inbox) |
| **Automation inbox** | automation_inbox/collect.py | AutomationInboxItem (item_id, kind, run_id, automation_id, priority, outcome_summary, failure_code) | Background runs: completed, blocked, failed, suppressed | `automation-inbox list`, `automation-inbox show` |
| **Approval queue** | supervised_loop/store.py, queue.py | ApprovalQueueItem (queue_id, action: QueuedAction, status) | Supervised loop queue (pending approval actions) | `agent-loop queue`, `agent-loop approve/reject/defer` |
| **Assist queue** | assist_engine/queue.py | AssistSuggestion (from list_suggestions + policy) | Generated suggestions; filtered by policy, snooze, repetitive suppress | get_queue(); assist CLI |
| **Action cards** | action_cards/store.py | ActionCard (card_id, title, handoff_target, state: PENDING/ACCEPTED/BLOCKED/…) | Cards from suggestions; list_cards(state=…) | action-cards list, refresh, execute |
| **Worker lanes** | lanes/store.py | WorkerLane (lane_id, status: open/running/blocked/completed) | Lanes with status completed = results awaiting review | `lanes list`; mission_control worker_lanes.results_awaiting_review |
| **Daily digest** | daily/inbox.py | DailyDigest (inbox_items, blocked_items, reminders_due, top_next_recommended) | Copilot, work_context, job_packs, reminders; one “top next” | daily digest build; mission_control daily_inbox |
| **Mission control “next action”** | mission_control/next_action.py | recommend_next_action(state) → action (build, benchmark, cohort_test, promote, hold, rollback, …) | Product/eval/devlab/incubator/observation — not personal ops queue | Used in mission control report |
| **Portfolio** | portfolio/scheduler.py, reports.py | get_next_recommended_project, report_best_next, report_blocked | Ranked projects; best next; blocked | `portfolio status`, `portfolio list` |
| **Project next action** | project_case/graph.py | get_project_summary → recommended_next_action | Per-project: next goal, replan, etc. | Mission control project_case |
| **In-flow drafts / checkpoints** | in_flow/store.py | DraftArtifact, ReviewCheckpoint | list_drafts(review_status=waiting_review), list_checkpoints(status=pending) | Mission control in_flow; no single “queue” CLI |
| **Recommended handoff** | automation_inbox/briefs.py | get_recommended_handoff() | Blocked automation > approval queue > inbox (one “next” handoff) | Used in mission control automation_inbox; handoff command |

So today: **multiple disjoint queues/inboxes** (intervention inbox, automation inbox, approval queue, assist queue, action cards, lanes results, daily top-next, portfolio next, project next, in-flow drafts). There is **no single normalized “unified work queue”** or **one accept/defer/route** flow that routes into the correct subsystem.

---

## 2. What is missing for a real unified work queue

- **Single normalized item type**  
  One model (e.g. UnifiedQueueItem) that can represent any of the above: with source_subsystem (approval_queue | automation_inbox | review_studio | lanes | action_cards | assist | project_next | portfolio_next | in_flow_draft | blocked_run | resume_continuity), actionability_class (needs_approval | needs_review | executable | deferred | blocked), and stable item_id + source_ref so we can route back.

- **Single collect step**  
  One function that pulls from: project next actions, approval queue, automation inbox, review_studio inbox (or merge its sources), worker lanes (completed awaiting review), action cards (pending/blocked), assist queue, blocked/failed runs, in-flow drafts waiting review / checkpoints pending, daily top-next, resume-work/continuity items. Each is normalized into UnifiedQueueItem with source_subsystem and entity_refs.

- **Prioritization / ranking**  
  A first-draft ranker that uses: current workday state (if present from Pane 1), active project and portfolio priority, trust/policy posture, blocked vs executable, user preferences (e.g. focus_mode, review_mode), recurring responsibility/operator mode, freshness and interruption cost. Output: ordered list and optional grouping (e.g. “blocked”, “approval”, “focus_ready”, “review_ready”, “operator_ready”).

- **Accept / defer / dismiss / escalate / route**  
  One set of actions that: (1) **accept** → route item into the appropriate subsystem (e.g. open approval, open automation-inbox show, open draft, start executor, etc.); (2) **defer** → record deferral with optional revisit_after and leave in queue with state deferred; (3) **dismiss** → mark as dismissed and remove from actionable queue; (4) **escalate** → mark for human takeover or move to review; (5) **route** → explicitly send to planner | executor | review | workspace | automation_follow_up | draft_composer. All must call existing subsystem APIs (no bypass of trust/approval).

- **Single CLI surface**  
  `queue list`, `queue top`, `queue explain --id <item_id>`, `queue accept --id <item_id>`, `queue defer --id <item_id>`, `queue dismiss --id <item_id>`, `queue route --id <item_id> [--target planner|executor|review|…]` so the operator has one place to see and act.

- **Mission control slice**  
  Add a **unified_queue** (or work_queue) slice: top section (e.g. first 5–10 items), next_best_item_id, blocked_but_important_item_id, count_ready_focus_mode, count_ready_review_mode, count_ready_operator_mode, and a one-line “recommended next” from the queue.

---

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|--------|
| **Create** | `src/workflow_dataset/unified_queue/models.py` | UnifiedQueueItem (item_id, source_subsystem, source_ref, actionability_class, urgency/priority, value_score, trust_score, routing_target, blocked_reason, state, group/section, label, summary, entity_refs, created_at). QueueSection or QueueGroup for grouping. RoutingTarget enum (planner, executor, review, workspace, automation_follow_up, draft_composer). |
| **Create** | `src/workflow_dataset/unified_queue/collect.py` | collect_from_* helpers per source (projects, approval, automation_inbox, review_studio, lanes, action_cards, assist, blocked_runs, in_flow, daily, operator_mode/resume). build_unified_queue(repo_root, limit, include_sections) → list[UnifiedQueueItem]. |
| **Create** | `src/workflow_dataset/unified_queue/prioritize.py` | rank_unified_queue(items, context) where context has workday_state, active_project_id, portfolio_next_id, trust_posture, focus_mode, review_mode, operator_mode. Return ordered list + optional section labels (blocked, approval, focus_ready, review_ready, operator_ready). |
| **Create** | `src/workflow_dataset/unified_queue/route.py` | accept_item(item_id, repo_root), defer_item(item_id, reason, revisit_after, repo_root), dismiss_item(item_id, repo_root), escalate_item(item_id, repo_root), route_item(item_id, target, repo_root). Each resolves item to source and calls the right subsystem (e.g. agent-loop approve, automation-inbox accept, inbox decide, lanes handoff, action-cards execute, open draft, etc.). |
| **Create** | `src/workflow_dataset/unified_queue/explain.py` | explain_item(item_id, repo_root) → why it’s in the queue, priority, routing_target, what accept/route would do. |
| **Create** | `src/workflow_dataset/unified_queue/store.py` | Optional: persist deferrals, dismissals (so they don’t reappear in queue until revisit_after or explicit refresh). data/local/unified_queue/deferrals.json, dismissals.json. |
| **Create** | `src/workflow_dataset/unified_queue/cli.py` | Commands: list, top, explain, accept, defer, dismiss, escalate, route. (Register under main app as `queue` group.) |
| **Create** | `src/workflow_dataset/unified_queue/__init__.py` | Public API. |
| **Modify** | `src/workflow_dataset/mission_control/state.py` | Add unified_queue_state: top_item_ids, next_best_item_id, blocked_important_item_id, count_focus_ready, count_review_ready, count_operator_ready, recommended_next_command. |
| **Modify** | `src/workflow_dataset/mission_control/report.py` | Add [Unified queue] section: top N, next best, blocked-important, counts by mode. |
| **Modify** | `src/workflow_dataset/cli.py` | Register `queue` group and commands. |
| **Create** | `tests/test_unified_queue.py` | Tests: normalization from each source, prioritization, defer/dismiss persistence, routing to correct subsystem (stub or integration). |
| **Create** | `docs/M36E_M36H_UNIFIED_WORK_QUEUE.md` | Deliverable: files, CLI, sample item, sample ranked output, routing explanation, tests, gaps. |

---

## 4. Safety / risk note

- **Do not bypass trust or review.** Routing and “accept” must invoke existing flows (e.g. agent-loop approve, automation-inbox accept/archive, review studio resolve). No new path that skips approval or policy checks.
- **Routing must be explicit and explainable.** explain_item must state which subsystem will be used and what command or API will be called. No hidden auto-routing.
- **Defer/dismiss state is local and reversible.** Persist deferrals/dismissals so the queue doesn’t re-surface the same item until revisit_after or operator clears; allow “show deferred” / “undismiss” if needed later.
- **Blocked items remain visible.** Blocked-but-important should be clearly labeled and not buried; prioritization can put them in a dedicated section.

---

## 5. Routing principles

- **Blocked items**  
  Surface with blocked_reason; routing_target may be “review” or “executor” (resume). Prioritization can put “blocked but important” in a dedicated section.

- **Workday / focus mode**  
  When a workday state or focus mode is available (Pane 1): prefer items that match current project or “focus_ready”; deprioritize high-interruption items unless urgent.

- **Review mode**  
  When operator is in “review” mode: boost approval_queue, in_flow drafts, automation_inbox items needing decision, lanes results awaiting review.

- **Operator mode**  
  When operator mode is active: boost automation follow-up, resume-work continuity, and delegated-responsibility next actions.

- **Trust posture**  
  If trust/policy says “simulate_only” or “approval_required”, items that would trigger real execution should be clearly marked and routing_target may require “review” first.

- **Freshness and interruption**  
  Older blocked items or stale “next” can be ranked higher for “clear the deck”; assist suggestions can be down-ranked if interruptiveness is high and not focus-safe.

---

## 6. What this block will NOT do

- **Replace every subsystem-specific view.** Inbox list, automation-inbox list, agent-loop queue, action-cards list, lanes list, etc. remain. The unified queue is an additional “one place to look and act” layer.
- **Hide routing logic.** explain --id and route --id must show exactly which subsystem and (where applicable) which command or API is used.
- **Bypass trust or review boundaries.** No new execution path that skips human_policy, approval registry, or existing gates.
- **Rebuild approvals, review studio, or automation inbox from scratch.** We only aggregate and normalize; accept/route calls into existing modules.
- **Implement Pane 1 daily operating state machine.** We consume workday state / focus mode / review mode if exposed (e.g. from workspace or a future day layer); we do not define the state machine here.
- **Add a full UI.** CLI and mission control text only.

---

*Do not code until this is complete. Proceed to Phase A (unified queue model) after review.*
