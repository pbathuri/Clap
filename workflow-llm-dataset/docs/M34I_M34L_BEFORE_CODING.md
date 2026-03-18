# M34I–M34L — Automation Inbox + Recurring Outcome Digests — Before Coding

## 1. What inbox / review / timeline surfaces already exist

| Surface | Location | What it does |
|--------|----------|----------------|
| **Intervention inbox** | `review_studio/inbox.py` | `build_inbox()` aggregates: approval queue, blocked runs (executor), replan recommendations, skill candidates, policy overrides, stalled projects, graph routine/pattern review. Uses `InterventionItem` (item_id, kind, status, summary, priority, entity_refs, source_ref, operator_notes). |
| **Review studio** | `review_studio/studio.py` | `get_item`, `inspect_item`, `accept_item`, `reject_item`, `defer_item` — delegate to supervised_loop/teaching where applicable; operator notes via `review_studio/store.py`. |
| **Activity timeline** | `review_studio/timeline.py` | `build_timeline()` from queue history, handoffs, executor runs, policy overrides, projects, skills, replan signals. `TimelineEvent` (event_id, kind, timestamp_utc, summary, entity_refs). |
| **Digests** | `review_studio/digests.py` | `DigestView` (what_changed, what_is_blocked, what_needs_approval, most_important_intervention). `build_morning_summary`, `build_end_of_day_summary`, `build_project_summary`, `build_rollout_support_summary` — all use timeline + inbox (no background_run/automation-specific content). |
| **Daily inbox** | `daily/inbox_report.py`, `daily/inbox.py`, `daily/digest_history.py` | `format_inbox_report`, `build_daily_digest`, `save_digest_snapshot`, `compare_digests` — daily work summary and compare. |
| **CLI** | `cli.py` | `inbox` (list, review, accept, reject, defer, explain, compare, snapshot); `inbox-studio` (list, review, accept, reject, defer); `digest` (morning, end-of-day, project, rollout-support). |
| **Background runner** | `background_run/` | `BackgroundRun`, `QueuedRecurringJob`, `RunSummary`; `list_runs`, `load_run`, `load_history`; `build_run_summary()` → active/blocked/retryable/needs_review_automation_ids. No inbox items or digests built from these. |
| **Automations** | `automations/` | Triggers, recurring workflow definitions, `evaluate_active_triggers`. Mission control already has `background_runner_state` and `automations_state` (queue, next, needs_review, active/suppressed/blocked triggers). |
| **Mission control** | `mission_control/state.py`, `report.py` | Aggregates product, evaluation, development, incubator, workflow_episodes, live_workflow, in_flow, assist_engine, background_runner_state, automations_state. Report prints background queue, needs_review, automations active/suppressed/blocked. No dedicated "automation inbox" or "recurring digest" section. |

---

## 2. What is missing for a true automation review layer

- **Automation-specific inbox items** — No first-class item kinds for: automation result, recurring digest summary, blocked automation, background result summary, failed/suppressed automation explanation, human follow-up recommendation. Existing `blocked_run` is executor-focused; background_run blocked/suppressed/failed are not turned into intervention items.
- **Collection from background runs** — No code that maps `BackgroundRun` (completed / blocked / failed / suppressed) and `load_history()` into inbox items or digest sections. No "what happened between sessions" built from background_run + automations.
- **Recurring automation digests** — No digest type that is automation-specific: e.g. morning automation digest, project automation digest, approval-follow-up digest, blocked-automation digest, built from background_run and trigger evaluation.
- **Persistence of automation-inbox decisions** — Review studio stores operator notes by item_id; accept/reject/defer for approval/skill delegate to other systems. Automation items need: accept/archive/dismiss and optionally "escalate" (reopen to planner/workspace/review) with decisions persisted so the same run/result does not reappear as pending.
- **CLI** — No `automation-inbox` or `automation-digest` command group. No `automation-inbox list | show | accept | archive | dismiss | escalate` or `automation-digest latest | project | blocked`.
- **Mission control** — No dedicated slice for: unseen automation results count, most important blocked automation, latest recurring digest ref, "background work completed since last session", "next recommended human follow-up" for automation.

---

## 3. Exact file plan

| Phase | Action | Path |
|-------|--------|------|
| A | Create automation inbox models | **Create** `src/workflow_dataset/automation_inbox/models.py` — AutomationInboxItem, RecurringDigest, BlockedAutomationReviewItem, BackgroundResultSummary, FailedSuppressedExplanation, HumanFollowUpRecommendation (dataclasses, to_dict/from_dict). |
| B | Result collection + digest building | **Create** `src/workflow_dataset/automation_inbox/collect.py` — collect from background_run (list_runs, load_run, load_history), build AutomationInboxItem list; **Create** `src/workflow_dataset/automation_inbox/digests.py` — build_morning_automation_digest, build_project_automation_digest, build_blocked_automation_digest, build_approval_followup_digest (using collect + existing review_studio where useful). |
| B | Store for automation inbox + decisions | **Create** `src/workflow_dataset/automation_inbox/store.py` — get_automation_inbox_root, save_item (optional persistence of items for dedup), save_decision (accept/archive/dismiss/escalate with timestamp + note), list_decisions, load_operator_notes (or reuse review_studio notes by prefix). |
| C | Review / follow-up flows | **Create** `src/workflow_dataset/automation_inbox/flows.py` — inspect_automation_item, accept_item, archive_item, dismiss_item, escalate_item, attach_operator_note; link_commands for planner/workspace/review. |
| D | CLI | **Modify** `src/workflow_dataset/cli.py` — add `automation_inbox_group` (name=`automation-inbox`) with commands: list, show, accept, archive, dismiss, escalate, note; add `automation_digest_group` (name=`automation-digest`) with commands: latest, project, blocked, approval-followup. |
| D | Mission control | **Modify** `src/workflow_dataset/mission_control/state.py` — add section `automation_inbox` (or extend existing pattern): unseen_count, most_important_blocked_automation, latest_recurring_digest_ref, background_completed_since_last_session, next_recommended_follow_up. **Modify** `src/workflow_dataset/mission_control/report.py` — print automation inbox summary lines. |
| E | Tests | **Create** `tests/test_automation_inbox.py` — inbox item creation, digest generation, blocked/suppressed handling, accept/archive/escalate, empty state. |
| E | Docs | **Create** `docs/M34I_M34L_AUTOMATION_INBOX.md` — summary, sample item, sample digest, sample blocked flow, CLI usage, gaps. |

**New package:** `src/workflow_dataset/automation_inbox/` with `__init__.py` exporting public API.

---

## 4. Safety / risk note

- **No hidden execution** — All automation results are surfaced for review; no new background execution in this block. We only read from `background_run` and `automations` and present.
- **Decisions are local** — Accept/archive/dismiss/escalate stored under `data/local/automation_inbox/` (or similar); no cloud or shared state.
- **Overlap with intervention inbox** — Existing `blocked_run` comes from executor; automation inbox will have "blocked_automation" from background_run. We keep them separate namespaces (automation-inbox vs inbox) to avoid double-counting and confusion. Escalation can route into existing review_studio/inbox or planner/workspace by link commands.
- **Idempotent digests** — Digest building is read-only and repeatable; no side effects on background_run or automations.

---

## 5. What this block will NOT do

- Will **not** rebuild review_studio, timeline, or daily inbox from scratch.
- Will **not** add cloud notifications or push delivery.
- Will **not** run or schedule background jobs (that is Pane 2 / existing background_run).
- Will **not** optimize for polish (minimal UI, first-draft copy).
- Will **not** implement full "since last session" detection (e.g. last login timestamp); we use "recent" runs and history entries with a simple limit/window; "since last session" can be a label in mission control based on recent outcomes).
- Will **not** unify automation inbox with the single intervention inbox in this block — additive automation-inbox surface only; integration into one inbox can be a later refinement.

---

*Proceeding to implement Phases A–E per the file plan.*
