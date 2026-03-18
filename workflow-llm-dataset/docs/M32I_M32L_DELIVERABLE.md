# M32I–M32L Deliverable: Guided Action Cards + One-Click Safe Handoffs

## 1. Files modified

- `src/workflow_dataset/cli.py` — Added `action_cards_group` and commands: `list`, `show`, `accept`, `dismiss`, `preview`, `execute`, `refresh`.
- `src/workflow_dataset/mission_control/state.py` — Added `action_cards_summary` (total_cards, pending/accepted/executed/blocked counts, awaiting_approval_count, highest_value_card, recent_outcomes, next_action).
- `src/workflow_dataset/mission_control/report.py` — Added **[Action cards]** section using `action_cards_summary`.

## 2. Files created

- `src/workflow_dataset/action_cards/__init__.py` — Package exports.
- `src/workflow_dataset/action_cards/models.py` — ActionCard, ActionPreview, CardState, HandoffTarget, TrustRequirement.
- `src/workflow_dataset/action_cards/store.py` — load_all_cards, save_cards, load_card, save_card, update_card_state, list_cards, get_cards_dir.
- `src/workflow_dataset/action_cards/builder.py` — suggestion_to_cards (personal, graph routines, style, copilot).
- `src/workflow_dataset/action_cards/preview.py` — build_preview(card) → ActionPreview.
- `src/workflow_dataset/action_cards/handoff.py` — execute_handoff(card_id, repo_root) → outcome dict.
- `tests/test_action_cards.py` — Card create/save/load, list by state, build_preview, execute_handoff (prefill), blocked/dismissed/not-found, update_card_state, outcome reporting.
- `docs/M32I_M32L_ACTION_CARDS.md` — Overview, model, flow, CLI, mission control, safety.
- `docs/M32I_M32L_ACTION_CARDS_BEFORE_CODING.md` — (pre-existing) Before-coding analysis.
- `docs/M32I_M32L_DELIVERABLE.md` — This file.

## 3. Exact CLI usage

```bash
# List all cards (optional filter by state)
workflow-dataset action-cards list
workflow-dataset action-cards list --state pending --limit 20
workflow-dataset action-cards list --json

# Show one card
workflow-dataset action-cards show --id card_abc123
workflow-dataset action-cards show --id card_abc123 --json

# Accept / dismiss (no execution)
workflow-dataset action-cards accept --id card_abc123
workflow-dataset action-cards dismiss --id card_abc123

# Preview what the card would do
workflow-dataset action-cards preview --id card_abc123
workflow-dataset action-cards preview --id card_abc123 --json

# Execute one-click handoff
workflow-dataset action-cards execute --id card_abc123
workflow-dataset action-cards execute --id card_abc123 --json

# Refresh: build new cards from suggestions/routines/copilot and save
workflow-dataset action-cards refresh
workflow-dataset action-cards refresh --json

# Override repo root
workflow-dataset action-cards list --repo-root /path/to/repo
```

## 4. Sample action card (JSON)

```json
{
  "card_id": "card_personal_focus_abc",
  "title": "Focus project proj_1",
  "description": "Set current project from suggestion",
  "source_type": "personal_suggestion",
  "source_ref": "sug_xyz",
  "handoff_target": "prefill_command",
  "handoff_params": {
    "command": "projects set-current --id proj_1",
    "hint": "projects"
  },
  "trust_requirement": "none",
  "reversible": true,
  "expected_artifact": "",
  "state": "pending",
  "created_utc": "2025-03-16T12:00:00Z",
  "updated_utc": "2025-03-16T12:00:00Z",
  "executed_at": "",
  "outcome_summary": "",
  "blocked_reason": ""
}
```

## 5. Sample action preview

```json
{
  "card_id": "card_personal_focus_abc",
  "summary": "Focus project proj_1",
  "what_would_happen": "Would prefill or run: projects set-current --id proj_1. Params: projects",
  "trust_note": "",
  "command_hint": "projects set-current --id proj_1",
  "approval_required": false,
  "simulate_first": true
}
```

## 6. Sample handoff/execution output

**Success (prefill_command):**

```json
{
  "ok": true,
  "card_id": "card_personal_focus_abc",
  "handoff_target": "prefill_command",
  "message": "Prefill command: projects set-current --id proj_1. Run it manually or use agent-loop.",
  "command_prefilled": "projects set-current --id proj_1"
}
```

**Blocked card:**

```json
{
  "ok": false,
  "error": "card_blocked",
  "card_id": "card_copilot_job_1",
  "blocked_reason": "Job has blocking issues; resolve in approval studio."
}
```

**Card not found:**

```json
{
  "ok": false,
  "error": "card_not_found",
  "card_id": "nonexistent_id"
}
```

## 7. Exact tests run

```bash
cd workflow-llm-dataset
python -m pytest tests/test_action_cards.py -v
```

Tests included:

- `test_card_create_and_roundtrip` — Create card, save, load; fields preserved.
- `test_list_cards_by_state` — list_cards with state filter.
- `test_build_preview_prefill_command` — build_preview for PREFILL_COMMAND.
- `test_build_preview_trust_note_approval_required` — trust_note when APPROVAL_REQUIRED.
- `test_execute_handoff_prefill_command` — execute PREFILL_COMMAND; card marked executed, outcome stored.
- `test_execute_handoff_blocked_card` — blocked card returns ok=False, blocked_reason.
- `test_execute_handoff_dismissed_card` — dismissed card returns ok=False.
- `test_execute_handoff_card_not_found` — missing card returns card_not_found.
- `test_update_card_state` — update_card_state updates state and outcome_summary.
- `test_get_cards_dir` — get_cards_dir path.
- `test_card_outcome_reporting` — After execute, outcome_summary and executed_at set.

## 8. Exact remaining gaps for later refinement

- **UI**: No UI for action cards yet; CLI and mission-control report only. A future pane could show cards and one-click execute.
- **Refresh strategy**: `action-cards refresh` merges new candidates; no deduplication by source_ref or “same suggestion” semantics.
- **CREATE_DRAFT handoff**: Relies on `materialize_from_suggestion` with a context_bundle that includes `suggestion_context.suggestions`; if context is built elsewhere, handoff may need to call a different entry point or build the bundle from card’s suggestion_id.
- **EXECUTOR_RUN handoff**: Currently returns a message that approval is required; does not enqueue to supervised_loop; can be extended to enqueue with mode=simulate or real after approval.
- **Prioritization**: “Highest value” card in mission control is simply the first pending/accepted; no scoring or ranking yet.
- **Reversibility**: Cards are reversible in model; no concrete “undo” implementation (e.g. revert prefill or cancel queued action) yet.
- **Idempotency**: Executing an already-executed card returns ok=True with already_executed; no duplicate queue entries for QUEUE_SIMULATED if executed twice (card state prevents second execution).
