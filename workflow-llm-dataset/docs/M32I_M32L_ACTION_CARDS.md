# M32I–M32L Guided Action Cards + One-Click Safe Handoffs

## Overview

The action-card layer turns assist suggestions into **explicit, previewable action cards** and supports **one-click safe handoffs** into planner, executor, workspace, and review flows. It does not perform hidden execution; all handoffs are explicit and respect approvals and trust boundaries.

## Model

- **ActionCard**: `card_id`, `title`, `description`, `source_type` (personal_suggestion | graph_routine | style_suggestion | copilot), `source_ref`, `handoff_target`, `handoff_params`, `trust_requirement`, `reversible`, `expected_artifact`, `state`, timestamps, `outcome_summary`, `blocked_reason`.
- **CardState**: `pending`, `accepted`, `dismissed`, `executed`, `blocked`.
- **HandoffTarget**: `open_view`, `prefill_command`, `queue_simulated`, `approval_studio`, `create_draft`, `compile_plan`, `executor_run`.
- **TrustRequirement**: `none`, `simulate_only`, `approval_required`, `trusted_path`.
- **ActionPreview**: Human-readable `summary`, `what_would_happen`, `trust_note`, `command_hint`, `approval_required`, `simulate_first`.

## Flow

1. **Suggestions → cards**: `suggestion_to_cards()` (in `builder`) builds cards from personal suggestions, graph routines, style suggestions, and copilot recommendations. Caller persists via store.
2. **Preview**: `build_preview(card)` returns an `ActionPreview` describing what would happen and trust/approval notes.
3. **Accept / Dismiss**: Operator can accept (enable execute) or dismiss a card via CLI or future UI.
4. **Execute handoff**: `execute_handoff(card_id, repo_root)` performs the handoff: prefill command, compile plan, queue simulated run, open approval studio, create draft, or open view. Card state is updated to `executed` and `outcome_summary` is set.
5. **Blocked cards**: Cards in state `blocked` or with blocking issues do not execute; handoff returns an error and optional `blocked_reason`.

## CLI

- `workflow-dataset action-cards list` — list cards (optional `--state pending|accepted|executed|dismissed|blocked`, `--limit`, `--json`).
- `workflow-dataset action-cards show --id <card_id>` — show one card.
- `workflow-dataset action-cards accept --id <card_id>` — accept card (enable execute; does not run).
- `workflow-dataset action-cards dismiss --id <card_id>` — dismiss card.
- `workflow-dataset action-cards preview --id <card_id>` — show what executing the card would do.
- `workflow-dataset action-cards execute --id <card_id>` — run the one-click handoff.
- `workflow-dataset action-cards refresh` — build new cards from suggestions/routines/copilot and save (merge with existing).

## Mission control

`get_mission_control_state()` includes `action_cards_summary`: `total_cards`, `pending_count`, `accepted_count`, `executed_count`, `blocked_count`, `awaiting_approval_count`, `highest_value_card`, `recent_outcomes`, `next_action`. The report prints an **[Action cards]** section with these counts and the highest-value card.

## Safety

- **No hidden execution**: Handoffs only do what the card declares (e.g. queue to approval, prefill command). Real execution happens only after operator approval via supervised_loop/approval flow.
- **Preview always available**: Every card can be previewed before execute.
- **Trust/approval preserved**: Handoffs that would run executor or desktop actions go through the existing approval queue or trust checks.
- **Reversible/dismissible**: Cards can be dismissed; accept means “enable execute”, not “run without confirmation”.
