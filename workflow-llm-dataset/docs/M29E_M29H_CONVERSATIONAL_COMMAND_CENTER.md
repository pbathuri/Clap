# M29E–M29H — Conversational Command Center + Explainability Layer

## Purpose

A **safe conversational layer** over explicit system state and actions: accept natural-language operator requests, map them to explicit intents, preview intended actions, and explain current state in plain language. No execution from ask; no bypass of approvals or trust.

## Capabilities

1. **Natural-language entrypoint** — `workflow-dataset ask "<phrase>"`
2. **Explicit intents** — status, explanation, next-action, blocked-state, approval/review, project switch, plan preview, execution preview, policy, artifact lookup, what-changed
3. **Grounded answers** — every answer is derived from mission_control, project_case, progress, supervised_loop, lanes (no freeform hallucination)
4. **Action preview** — for action-like requests, show suggested command and trust/approval implications; no execution from ask
5. **Refusal when unclear** — low-confidence or unknown intents return a short refusal and suggested phrases/commands

## CLI

```bash
workflow-dataset ask "What should I work on next?"
workflow-dataset ask "Why is founder_case_alpha blocked?"
workflow-dataset ask "Show me what would happen if I approve the next queued action."
workflow-dataset ask "Summarize what changed in my active workspace today."
workflow-dataset ask "Status"
workflow-dataset ask "Why is this in the approval queue?"
workflow-dataset ask --json "What next?"
workflow-dataset ask --no-preview "What changed?"
```

## Intent types

| Intent | Example phrase |
|--------|----------------|
| next_action_query | What should I do next? |
| blocked_state_query | Why is X blocked? |
| what_changed | What changed since yesterday? |
| approval_review_query | Why is this in the approval queue? |
| execution_preview_request | What would happen if I approve? |
| plan_preview_request | Preview the plan |
| project_switch_request | Switch to founder_case_alpha |
| explanation_query | Why this project? |
| status_query | Status, overview |
| policy_question | Policy, trust rules |
| artifact_lookup | Workspace summary |
| unknown | (refusal + suggestions) |

## Safety

- **No execution** — ask only returns text and optional preview; all execution stays in CLI/approval flows.
- **Grounded answers** — answers are generated from real state (get_mission_control_state, project_case, progress, supervised_loop).
- **Preview before action** — action-like intents get a preview with suggested command and trust/approval note.
- **Refusal** — ambiguous or unsupported phrases get confidence 0 and a short refusal with suggestions.

## Files

- `conversational/intents.py` — Intent constants and `ParsedIntent`
- `conversational/interpreter.py` — `parse_natural_language()` (keyword/pattern first-draft)
- `conversational/explain.py` — `answer_what_next`, `answer_why_blocked`, `answer_what_changed`, etc.
- `conversational/preview.py` — `build_action_preview()`
- `conversational/ask.py` — `ask(phrase)` → answer, intent, preview, confidence

## Remaining gaps (for later)

- Richer NL understanding (synonyms, typo tolerance, optional LLM disambiguation with grounding).
- “What is this pack doing?” fully grounded in pack metadata.
- Caching of mission_control state per ask to avoid repeated aggregation.
- Integration with workspace shell / navigation state (Pane 1) when that surface is stable.
