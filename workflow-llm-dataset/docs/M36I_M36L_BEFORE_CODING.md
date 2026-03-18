# M36I–M36L Continuity Engine + Morning/Shutdown/Resume — Before Coding

## 1. What continuity/digest/resume-like surfaces already exist

| Area | What exists |
|------|-------------|
| **workday/** | **WorkdayState** (NOT_STARTED, STARTUP, FOCUS_WORK, REVIEW_AND_APPROVALS, OPERATOR_MODE, WRAP_UP, SHUTDOWN, RESUME_PENDING). **WorkdayStateRecord**, **DaySummarySnapshot** (day_id, states_visited, top_actions, final_state). **DailyOperatingSurface** (current state, active project, top_queue_item, pending_approvals, next_recommended_transition). State machine (valid transitions, blocked reasons). Store: load/save workday state, load/save day summary by day_id. |
| **automation_inbox/briefs** | **MorningBriefCard** (what_happened_while_away, top_next_action, handoff). **ResumeWorkContinuityCard** (resume_context, what_happened, suggested_next, handoff). **build_morning_brief()**, **build_resume_continuity_card()**, **build_what_happened_summary()**, **get_recommended_handoff()**. |
| **daily/** | **DailyDigest** (what_changed, relevant_job_ids, inbox_items, blocked_items, top_next_recommended). **build_daily_digest()** from copilot, work_context, corrections. |
| **context/drift** | **ContextDrift** (newly_recommendable_jobs, newly_blocked_jobs, approvals_changed, summary). **compare_snapshots(older, newer)**. |
| **unified_queue/** | **QueueSummary**, **build_queue_summary()**; views by mode (focus, review, operator, wrap-up). **UnifiedQueueItem**, section_id, actionability_class. |
| **session/** | **Session**, **SessionBoard** (active_tasks, queued, blocked, completed, artifacts). **build_session_board()**. |
| **workflow_episodes/** | **WorkflowEpisode**, stage detection, handoff gaps, next-step candidates. |
| **mission_control** | **workday_state** (current_workday_mode, day_id, next_recommended_transition). automation_inbox digest/handoff used in state. |

So: workday state machine and day summaries exist; morning/resume cards and “what happened” exist in automation_inbox; daily digest has what_changed; context drift compares snapshots; queue and session/board exist. There is no **single continuity engine** that (1) defines “last active session” and “change since then”, (2) runs a **morning entry flow** (change + queue + automations + approvals + stalled projects + first mode/action), (3) runs a **shutdown flow** (completed, unresolved, carry-forward, tomorrow start, blocked), (4) runs a **resume flow** (interrupted work, project/session/episode reconnection, “what you were doing and what remains”), or (5) exposes **carry-forward items** and **unresolved blocker continuation** as first-class models with mission_control visibility.

---

## 2. What is missing for a true continuity engine

- **Continuity snapshot** — Single model that ties “as-of” time, “last session end”, and a summary of state at that point for comparison.
- **Change since last session** — Explicit “what changed since last active session” (queue delta, automation outcomes, approvals, project/outcome changes), using a stored last-session-end or last-shutdown time.
- **Morning entry flow** — One flow that surfaces: change since last session, top queue items, automation outcomes, urgent approvals/reviews, stalled projects, recommended first operating mode, recommended first action. (Daily digest and morning brief exist but are not wired into workday STARTUP as a single “morning” flow.)
- **Shutdown / wrap-up flow** — Explicit flow that: summarizes completed work, captures unresolved items, prepares carry-forward context, stages tomorrow’s likely starting point, notes blocked/high-risk items. (Workday has WRAP_UP/SHUTDOWN and DaySummarySnapshot but no “shutdown summary” with carry-forward and next-session recommendation.)
- **Resume flow** — Detect interrupted work, reconnect to project/session/workflow episode, surface artifacts and next steps, explain “what the system thinks you were doing and what remains”. (ResumeWorkContinuityCard exists but does not include interrupted-work chain or episode reconnection.)
- **Carry-forward item** and **unresolved blocker continuation** — First-class models for items to carry into the next session and blockers that continue.
- **Next-session recommendation** — Stored “tomorrow’s likely starting point” and “first action” from shutdown.
- **Mission control** — Visibility for: next best start-of-day action, strongest resume target, most important carry-forward item, unresolved blocker carried into today, end-of-day readiness.

---

## 3. Exact file plan

| Path | Purpose |
|------|--------|
| `src/workflow_dataset/continuity_engine/__init__.py` | Package exports. |
| `src/workflow_dataset/continuity_engine/models.py` | ContinuitySnapshot, ChangeSinceLastSession, MorningEntryBrief (or extended morning), ShutdownSummary, ResumeCard, InterruptedWorkChain, CarryForwardItem, UnresolvedBlockerContinuation, NextSessionRecommendation. |
| `src/workflow_dataset/continuity_engine/store.py` | Last session end time; last shutdown summary; carry-forward list; next-session recommendation. Data: `data/local/continuity_engine/`. |
| `src/workflow_dataset/continuity_engine/morning_flow.py` | build_morning_entry_flow() — aggregate workday, queue, automation, approvals, stalled projects, first mode/action. |
| `src/workflow_dataset/continuity_engine/shutdown_flow.py` | build_shutdown_summary(), build_carry_forward(), record_last_shutdown(). |
| `src/workflow_dataset/continuity_engine/resume_flow.py` | build_resume_flow(), get_strongest_resume_target(), detect_interrupted_work(). |
| `src/workflow_dataset/continuity_engine/changes.py` | build_changes_since_last_session(). |
| `src/workflow_dataset/cli.py` | continuity_group: morning, shutdown, resume, changes-since-last, carry-forward. |
| `src/workflow_dataset/mission_control/state.py` | continuity_engine_state: next_best_start_of_day_action, strongest_resume_target, most_important_carry_forward, unresolved_blocker_carried, end_of_day_readiness. |
| `src/workflow_dataset/mission_control/report.py` | [Continuity] section when state present. |
| `tests/test_continuity_engine.py` | Snapshot, morning flow, shutdown flow, resume target, carry-forward, empty state. |
| `docs/M36I_M36L_CONTINUITY_ENGINE.md` | Spec and usage. |

---

## 4. Safety/risk note

- **Local-only:** All state under `data/local/continuity_engine/`. No cloud or background summarization.
- **Grounded:** Morning/shutdown/resume and “changes since” are built from existing workday, queue, automation inbox, session, outcomes, project — no ungrounded prose.
- **Uncertainty visible:** Interrupted-work and resume target are best-effort; we do not hide uncertainty (e.g. “likely project X” with reason).
- **No hidden autonomy:** Continuity engine only reads and aggregates; it does not change workday state or execute actions unless the user invokes CLI (e.g. continuity shutdown to record).

---

## 5. What this block will NOT do

- **Static digest only:** We add morning/shutdown/resume *flows* that consume and produce structured continuity state, not just one-off morning text.
- **Hidden background summarization:** No always-on summarizer; generation is on-demand (CLI / mission_control).
- **Generic journaling:** Focus is daily operations OS continuity (yesterday/today/resume/carry-forward), not free-form journaling.
- **Rebuild queue/timeline/progress:** We call into existing unified_queue, workday, automation_inbox, session, outcomes; we do not replace them.
