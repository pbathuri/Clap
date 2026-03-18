# M34I–M34L — Automation Inbox + Recurring Outcome Digests

First-draft automation review layer: collect background run outputs, surface in a dedicated automation inbox, summarize with recurring digests, route blocked/failed into review flows, and expose in mission control.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `automation_inbox_group` (automation-inbox list, show, accept, archive, dismiss, escalate, note) and `automation_digest_group` (automation-digest latest, project, blocked, approval-followup). |
| `src/workflow_dataset/mission_control/state.py` | Added `automation_inbox` section: unseen_automation_results_count, most_important_blocked_automation_id, latest_recurring_digest_id, latest_digest_generated_at, background_completed_since_session_label, next_recommended_follow_up. |
| `src/workflow_dataset/mission_control/report.py` | Added [Automation inbox] block: unseen count, blocked_id, latest_digest, next follow-up. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/automation_inbox/__init__.py` | Package exports. |
| `src/workflow_dataset/automation_inbox/models.py` | AutomationInboxItem, RecurringDigest, BlockedAutomationReviewItem, BackgroundResultSummary, FailedSuppressedExplanation, HumanFollowUpRecommendation. |
| `src/workflow_dataset/automation_inbox/store.py` | get_automation_inbox_root, save_decision, list_decisions, get_latest_decision, save_operator_note, load_operator_notes, save_digest_snapshot, load_digest_snapshot. |
| `src/workflow_dataset/automation_inbox/collect.py` | collect_from_background_runs, build_automation_inbox (from background_run). |
| `src/workflow_dataset/automation_inbox/digests.py` | build_morning_automation_digest, build_project_automation_digest, build_blocked_automation_digest, build_approval_followup_digest, format_digest. |
| `src/workflow_dataset/automation_inbox/flows.py` | get_item, inspect_item, accept_item, archive_item, dismiss_item, escalate_item, attach_operator_note. |
| `tests/test_automation_inbox.py` | Model roundtrip, decisions, notes, empty inbox/digest, accept/archive/dismiss/escalate error for missing item, inspect missing. |
| `docs/M34I_M34L_BEFORE_CODING.md` | Before-coding: existing surfaces, gaps, file plan, safety, what we don’t do. |
| `docs/M34I_M34L_AUTOMATION_INBOX.md` | This deliverable. |

---

## 3. Exact CLI usage

```bash
# Automation inbox
workflow-dataset automation-inbox list [--repo PATH] [--status pending] [--limit 50]
workflow-dataset automation-inbox show --id auto_<id> [--repo PATH]
workflow-dataset automation-inbox accept --id <id> [--note "..." ] [--repo PATH]
workflow-dataset automation-inbox archive --id <id> [--note "..."] [--repo PATH]
workflow-dataset automation-inbox dismiss --id <id> [--note "..."] [--repo PATH]
workflow-dataset automation-inbox escalate --id <id> [--note "..."] [--repo PATH]
workflow-dataset automation-inbox note --id <id> --note "..." [--repo PATH]

# Recurring digests
workflow-dataset automation-digest latest [--repo PATH]
workflow-dataset automation-digest project --id <project_id> [--repo PATH]
workflow-dataset automation-digest blocked [--repo PATH]
workflow-dataset automation-digest approval-followup [--repo PATH]
```

---

## 4. Sample automation inbox item

```json
{
  "item_id": "auto_a1b2c3d4e5f6",
  "kind": "blocked_automation",
  "status": "pending",
  "summary": "Blocked: run_abc — no summary",
  "created_at": "2025-03-16T12:00:00",
  "priority": "high",
  "run_id": "run_abc",
  "automation_id": "aut_weekly",
  "plan_ref": "routine_weekly",
  "outcome_summary": "",
  "failure_code": "blocked",
  "entity_refs": {"run_id": "run_abc", "automation_id": "aut_weekly"},
  "source_ref": "run_abc"
}
```

Inbox items are **derived** from `background_run` (list_runs / load_run); they are not stored as separate records except for **decisions** (accept/archive/dismiss/escalate) and **operator_notes** under `data/local/automation_inbox/`.

---

## 5. Sample recurring digest

**Morning automation digest** (output of `workflow-dataset automation-digest latest`):

```
# Morning automation digest
Generated: 2025-03-16T14:30:00

## Completed runs
  run_001: Step 1 done; artifact written.
  (or:   (no completed runs in window))

## Blocked or failed
  run_002: Blocked: run_002 — policy_suppressed
  (or:   (none))

## Approval follow-ups
  (none)

## Most important follow-up
  Review blocked/failed: workflow-dataset automation-inbox show --id auto_xyz
  (or: No automation follow-up needed.)
```

---

## 6. Sample blocked automation review flow

1. **List** — `workflow-dataset automation-inbox list` shows pending items (e.g. `auto_xyz` blocked_automation).
2. **Inspect** — `workflow-dataset automation-inbox show --id auto_xyz` shows why it matters and link commands (escalate, background run).
3. **Act** — Operator runs:
   - `workflow-dataset automation-inbox escalate --id auto_xyz --note "Reopen in planner"` (records decision, suggests next commands), or
   - `workflow-dataset automation-inbox accept --id auto_xyz` (acknowledged), or
   - `workflow-dataset automation-inbox dismiss --id auto_xyz` (no action).
4. **Note** — `workflow-dataset automation-inbox note --id auto_xyz --note "Will retry after config fix"` attaches an operator note.
5. Once a decision is recorded, the item no longer appears in `automation-inbox list` when `--status pending` (default).

---

## 7. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_automation_inbox.py -v --tb=short
```

**Result:** 10 passed (model roundtrip, decisions, notes, empty inbox, empty morning/blocked digest, accept/archive/dismiss/escalate on missing item, inspect missing item, get_automation_inbox_root).

---

## 8. Remaining gaps for later refinement

- **“Since last session”** — No explicit last-session timestamp; “recent” is limit-based. A later refinement can store last_seen_utc and label “background work completed since last session” from that.
- **Single unified inbox** — Automation inbox is separate from `inbox` / `inbox-studio`; merging into one view (with filters by kind) can be a later step.
- **Digest persistence** — `automation-digest latest` builds on demand; optional “save as snapshot” for compare (e.g. compare with previous digest) not wired in CLI yet (store has save_digest_snapshot / load_digest_snapshot).
- **Project scoping** — Project digest filters by project_id where items have it; background_run does not yet set project_id on runs; can be added when runner/automations carry project context.
- **Escalate target** — Escalate records the decision and suggests link commands; it does not create an in-flow handoff or planner task automatically; that can be a follow-up integration.
- **Approval digest** — build_approval_followup_digest pulls from review_studio inbox (approval_queue); no automation-specific approval state yet.
