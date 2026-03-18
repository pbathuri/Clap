# M36I–M36L Continuity Engine

First-draft continuity layer that closes the loop between yesterday, today, active work, and next resume. Not a static digest only: a daily continuity engine for the personal operations OS.

## What it does

1. **Summarize what changed** since the last active session (queue, automation outcomes, urgent approvals).
2. **Morning entry flow** — change since last, top queue, automations, approvals, stalled projects, recommended first mode/action.
3. **Shutdown / wrap-up flow** — completed work, unresolved items, carry-forward, tomorrow’s likely start, blocked/high-risk.
4. **Resume flow** — detect interrupted work, reconnect to project/session/episode, surface next steps and suggested first action.
5. **Carry-forward** — items to carry into the next session (from shutdown).
6. **Mission Control** — visibility for next start-of-day action, strongest resume target, most important carry-forward, unresolved blocker, end-of-day readiness.

## CLI usage

From repo root:

```bash
# Morning entry (run at start of day)
workflow-dataset continuity morning [--repo PATH] [--json]

# Shutdown / wrap-up (run at end of day)
workflow-dataset continuity shutdown [--repo PATH] [--json]

# Resume interrupted work
workflow-dataset continuity resume [--repo PATH] [--json]

# What changed since last session
workflow-dataset continuity changes-since-last [--repo PATH] [--json]

# List carry-forward items (from last shutdown)
workflow-dataset continuity carry-forward [--repo PATH] [--json]
```

`--repo` defaults to current repo root. `--json` prints the structured output as JSON.

## Data location

- `data/local/continuity_engine/`
  - `last_session.json` — last session end timestamp (optional; fallback: last shutdown time).
  - `last_shutdown.json` — last shutdown summary.
  - `carry_forward.json` — carry-forward items from last shutdown.
  - `next_session.json` — next-session recommendation from last shutdown.

## Sample morning brief (structure)

```json
{
  "brief_id": "brief_...",
  "generated_at_utc": "2025-03-17T10:00:00...",
  "change_since_last": {
    "last_session_end_utc": "2025-03-16T18:00:00Z",
    "queue_items_added": 3,
    "automation_outcomes": ["automation_result: run_abc — ok"],
    "approvals_urgent": ["ref-123"],
    "summary_lines": ["Queue: 5 pending item(s) now.", "Urgent approvals: 1"],
    "has_changes": true
  },
  "top_queue_items": [...],
  "automation_outcomes_summary": ["Completed: run_abc — ok"],
  "urgent_approvals": ["ref-123"],
  "stalled_projects": [],
  "recommended_first_mode": "startup",
  "recommended_first_action": "Review inbox",
  "recommended_first_command": "workflow-dataset inbox list",
  "handoff_label": "Review approval queue",
  "handoff_command": "workflow-dataset inbox list"
}
```

## Sample shutdown summary (structure)

```json
{
  "summary_id": "shutdown_...",
  "generated_at_utc": "2025-03-16T18:05:00...",
  "day_id": "2025-03-16",
  "completed_work": ["Workday states: focus, wrap_up", "Day 2025-03-16 — final state: wrap_up"],
  "unresolved_items": [{"item_id": "...", "label": "Review PR X", "source": "approval_queue"}],
  "carry_forward_items": [{"kind": "unresolved", "label": "Review PR X", "ref": "...", "command": "workflow-dataset queue view"}],
  "tomorrow_likely_start": "Project: proj_abc",
  "tomorrow_first_action": "workflow-dataset workspace open",
  "blocked_or_high_risk": [],
  "end_of_day_readiness": "has_unresolved"
}
```

## Sample resume card (structure)

```json
{
  "card_id": "card_...",
  "generated_at_utc": "2025-03-17T10:05:00...",
  "interrupted_work": {
    "chain_id": "chain_...",
    "inferred_what_doing": "Last session was shutdown; resuming today.",
    "next_step_summary": "workflow-dataset continuity morning",
    "confidence": "medium"
  },
  "resume_target_label": "Start morning flow",
  "resume_target_command": "workflow-dataset continuity morning",
  "what_system_thinks_doing": "Last session was shutdown; resuming today.",
  "what_remains": ["workflow-dataset continuity morning"],
  "suggested_first_action": "workflow-dataset continuity morning"
}
```

## Mission Control

When mission control state is built, it includes a **Continuity** block (from `continuity_engine_state`):

- `next_best_start_of_day_action` — recommended first action text.
- `strongest_resume_target_label` / `strongest_resume_target_command` — best resume target (handoff or morning).
- `most_important_carry_forward` — top carry-forward item label (or none).
- `unresolved_blocker_carried` — unresolved blocker carried into today (if any).
- `end_of_day_readiness` — ready / has_unresolved / has_blocked (from last shutdown).

## Tests

- **Fast (default):** `pytest tests/test_continuity_engine.py -m "not slow"`  
  - `test_changes_since_last_session_empty`  
  - `test_morning_flow_generation`  
  - `test_save_last_session_end`

- **Including slow:** `pytest tests/test_continuity_engine.py`  
  - Adds: `test_shutdown_flow_generation`, `test_resume_flow_generation`, `test_strongest_resume_target`, `test_carry_forward_after_shutdown`, `test_empty_state_no_prior_session`  
  - Some of these may be slow when run with an empty `tmp_path` due to deep dependency chains (queue, workday, automation inbox, workspace). Run with repo root for full integration.

## Remaining gaps (for later refinement)

- **Explicit last session end:** `save_last_session_end()` is only called by callers; shutdown flow could call it so “changes since last session” has a clear baseline.
- **Prose polish:** Morning/shutdown/resume text is first-draft; no LLM polish yet.
- **Interrupted-work confidence:** Resume flow does not hide uncertainty; confidence (low/medium/high) could drive UI copy.
- **Empty-state copy:** When no prior session, messaging could be tuned for “first use” vs “no recent session.”
- **Carry-forward prioritization:** Currently first N unresolved items; could use priority/blocked flags for ordering.
- **Mission Control report:** Continuity section is present in state and in the report; no further UX yet.
