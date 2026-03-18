# M29H.1 — Suggested Queries + Guided Operator Dialogues

## Summary

- **Suggested next questions** — After each answer, the ask response includes `suggested_queries`: follow-up questions the operator can ask (e.g. after "What next?" → "Why is my current project blocked?", "What's in the approval queue?").
- **Guided operator dialogues** — For intents that map to a common flow (e.g. blocked → unblock flow, approval → approve-and-run flow), the response includes a `guided_dialogue` with steps (prompt + suggested command). No execution; operator follows steps manually.
- **Role-specific suggested commands** — When `--role operator` or `--role reviewer` is set, the response includes `role_commands`: short label + command (e.g. operator: mission-control, portfolio next, approve; reviewer: approval queue, lanes review, trust report).
- **Better follow-up when ambiguous** — When intent is unknown or low-confidence, suggested prompts are role-aware (reviewer sees approval/lanes prompts first; operator sees next/blocked/status).

## CLI

```bash
workflow-dataset ask "What should I do next?"
# → answer + Suggested next questions: • ask "Why is my current project blocked?" ...

workflow-dataset ask "Why is founder_case_alpha blocked?"
# → answer + Guided flow: Unblock a project (steps 1–4 with commands)

workflow-dataset ask "Status" --role operator
# → answer + Suggested commands (operator): Mission control, What to do next, ...

workflow-dataset ask "xyz unclear" --role reviewer
# → refusal + follow-up prompts tailored to reviewer (approval queue, lanes, ...)
```

## Guided flows

| Flow id | Title | Trigger intent |
|--------|--------|----------------|
| unblock_project | Unblock a project | blocked_state_query |
| approve_and_run | Approve and run next action | approval_review_query, execution_preview_request |
| switch_and_plan | Switch project and plan | project_switch_request |
| review_lanes | Review worker lane results | (optional: lanes-related intent) |

## Roles

- **operator** — mission-control, portfolio next, blocked, progress board, approve, switch project.
- **reviewer** — approval queue, lanes list/review/approve, trust report, mission-control.
- **default** — status, ask, blocked, progress (no role flag).

## Files

- `conversational/suggested_queries.py` — `get_suggested_queries(intent, scope, state)`, `get_follow_up_prompts_when_ambiguous(phrase, role)`.
- `conversational/dialogues.py` — `GuidedDialogue`, `DialogueStep`, `get_dialogue_definition(flow_id)`, `list_guided_dialogues()`, `get_dialogue_for_intent(intent_type, scope)`.
- `conversational/roles.py` — `get_role_suggested_commands(role)`, `get_roles()`.
- `ask.py` — Extended return: `suggested_queries`, `guided_dialogue` (when intent maps), `role_commands` (when role set). Ambiguous answers use role-aware follow-ups.
