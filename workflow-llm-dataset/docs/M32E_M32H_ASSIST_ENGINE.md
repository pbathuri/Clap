# M32E–M32H Just-in-Time Assist Engine

First-draft assist engine that generates timely suggestions from live context, persists them in a reviewable queue, and supports accept/snooze/dismiss without auto-execution.

## Features

- **Generation** from: progress board, goal/plan, daily digest, routines, inbox items.
- **Suggestion types**: `next_step`, `draft_summary`, `blocked_review`, `resume_routine`, `open_artifact`, `use_preference`, `remind`.
- **Queue**: sort by usefulness and confidence; suppress repetitive (recently dismissed type+reason); snooze/dismiss/accept.
- **Mission control**: top suggestion, queue depth, repeated dismissed patterns, highest-confidence next, focus-safe.

## CLI

| Command | Description |
|--------|-------------|
| `workflow-dataset assist now` | Generate suggestions from live context, merge into queue, show top results |
| `workflow-dataset assist queue` | List queue (default: pending). Options: `--status pending\|snoozed\|accepted\|dismissed`, `--limit N` |
| `workflow-dataset assist explain-suggestion --id sug_xxx` | Explain a suggestion: reason, context, evidence |
| `workflow-dataset assist accept --id sug_xxx` | Mark as accepted (record only; no auto-execute) |
| `workflow-dataset assist snooze --id sug_xxx --until 2025-03-17T12:00:00Z` | Snooze until UTC time |
| `workflow-dataset assist dismiss --id sug_xxx` | Dismiss (used for repeat suppression) |

Use `--repo /path` (or `-r`) to point at a repo root when not running from the repo.

## Sample suggestion (JSON-like)

```json
{
  "suggestion_id": "sug_abc123",
  "suggestion_type": "next_step",
  "title": "Next step from plan",
  "description": "Run or preview the next step.",
  "reason": {
    "title": "Plan has next step",
    "description": "Current plan has an unblocked step.",
    "evidence": ["Goal: ...", "Step: ..."]
  },
  "triggering_context": {
    "source": "goal_plan",
    "summary": "Current goal and latest plan",
    "signals": ["plan_steps", "goal_set"]
  },
  "confidence": 0.85,
  "usefulness_score": 0.8,
  "interruptiveness_score": 0.2,
  "required_operator_action": "Run or preview the next step.",
  "status": "pending"
}
```

## Sample queue output

```
[Assist queue] status=pending  count=3
  1. [sug_abc123] next_step: Next step from plan
     usefulness=0.80  confidence=0.85  interrupt=0.20
  2. [sug_def456] blocked_review: Review blocked or stalled work
     usefulness=0.85  confidence=0.80  interrupt=0.40
  3. [sug_ghi789] draft_summary: Propose draft or checklist from plan
     usefulness=0.60  confidence=0.70  interrupt=0.30
```

## Sample suggestion explanation

```
Next step from plan
Type: next_step  ID: sug_abc123
Reason: Plan has next step
Current plan has an unblocked step.
Evidence: Goal: ... | Step: ...
Context: goal_plan — Current goal and latest plan
Required action: Run or preview the next step.
```

## Storage

- Path: `data/local/assist_engine/queue.json`.
- All statuses (pending, snoozed, accepted, dismissed) in one file; max 100 items (oldest dropped).

## Safety and constraints

- **No auto-execute**: Accept only records outcome.
- **Trust**: Does not bypass approval/trust.
- **Local-only**: No telemetry.
- **Spam control**: Repetitive suggestions (same type + reason recently dismissed) are suppressed; queue size capped; low usefulness ranked lower.

## Tests

Run:

```bash
pytest tests/test_assist_engine.py -v
```

Covers: models, store save/load/update, generation (no crash), queue run_now/get_queue, explain, accept/dismiss/snooze, repeat suppression, no-context behavior.

## Remaining gaps (for later refinement)

- **Live context fusion**: Use `get_live_context_state` / `fuse_active_context` more deeply in generation (e.g. work mode, inferred project) for finer suggestions.
- **Teaching skills**: Feed recently accepted skills into “use this skill” suggestions.
- **Value packs / behavior overrides**: Suggest applying a pack or override when context matches.
- **Snooze defaults**: Default snooze duration (e.g. 1h) when user says “snooze” without `--until`.
- **Focus-safe filter**: CLI flag to show only low-interruptiveness, high-confidence suggestions.
- **Richer explanation**: Optional `--verbose` with full evidence and context dump.

---

## Final deliverable summary (M32E–M32H)

### Files created

| Path | Purpose |
|------|--------|
| `src/workflow_dataset/assist_engine/__init__.py` | Package exports |
| `src/workflow_dataset/assist_engine/models.py` | AssistSuggestion, SuggestionReason, TriggeringContext, status/type enums |
| `src/workflow_dataset/assist_engine/store.py` | save_suggestion, load_suggestion, list_suggestions, update_status, list_dismissed_patterns |
| `src/workflow_dataset/assist_engine/generation.py` | generate_assist_suggestions from board, goal/plan, digest, routines, inbox |
| `src/workflow_dataset/assist_engine/queue.py` | run_now, get_queue, accept/dismiss/snooze, _suppress_repetitive |
| `src/workflow_dataset/assist_engine/explain.py` | explain_suggestion(suggestion_id) |
| `docs/M32E_M32H_ASSIST_ENGINE_ANALYSIS.md` | Pre-coding analysis (what exists, gaps, file plan, safety, spam control) |
| `docs/M32E_M32H_ASSIST_ENGINE.md` | User-facing doc + CLI + samples + tests + gaps |
| `tests/test_assist_engine.py` | Tests: models, store, generation, queue, explain, accept/dismiss/snooze, repeat suppression, no-context |

### Files modified

| Path | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added assist commands: `now`, `queue`, `explain-suggestion --id`, `accept --id`, `snooze --id --until`, `dismiss --id` |
| `src/workflow_dataset/mission_control/state.py` | Added `assist_engine` block: top_suggestion, queue_depth, repeated_dismissed_patterns, highest_confidence_next, focus_safe |
| `src/workflow_dataset/mission_control/report.py` | Added [Assist] section to dashboard report |

### Exact CLI usage

```bash
workflow-dataset assist now
workflow-dataset assist queue [--status pending|snoozed|accepted|dismissed] [--limit N]
workflow-dataset assist explain-suggestion --id sug_xxx
workflow-dataset assist accept --id sug_xxx
workflow-dataset assist snooze --id sug_xxx --until 2025-03-17T12:00:00Z
workflow-dataset assist dismiss --id sug_xxx
```

Optional: `--repo /path` or `-r` for repo root.

### Tests run

```bash
pytest tests/test_assist_engine.py -v
```

Requires project env (e.g. `pip install -e .` or venv with pydantic). Covers: suggestion model, store save/load/update/dismissed_patterns, generation returns list, queue run_now/get_queue, explain by id, accept/dismiss/snooze, repeat suppression, no-context behavior.
