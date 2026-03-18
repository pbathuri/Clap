# M29E–M29H — Conversational Command Center — Pre-coding analysis

## 1. What command/query surfaces already exist

- **CLI**: `mission-control`, `portfolio list|status|rank|next|explain|stalled|blocked|attention|work-window|should-switch|start-window`, `progress board|project|recovery|playbooks`, `replan recommend|diff|accept`, `lanes list|create|status|simulate|results|review|approve|reject|accept|trust-report|bundles`, `planner compile|preview`, `executor run|status|resume`, `projects create|set-current`, agent-loop approve, etc. All structured; no natural-language entry.
- **Mission control**: `get_mission_control_state()` aggregates product, evaluation, development, incubator, goal_plan, project_case, progress_replan, executor, supervised_loop, worker_lanes; `format_mission_control_report()` produces a text report; `recommend_next_action(state)` returns action + rationale + detail. Read-only; no conversational mapping.
- **Portfolio**: `cmd_explain(project)`, `cmd_stalled`, `cmd_blocked`, `cmd_next`, `cmd_work_window`, `cmd_should_switch` — explain and recommendations are structured, not NL-driven.
- **Project/case**: `recommended_next_goal(project_id)`, goal stack, linked plans/runs/artifacts.
- **Supervised loop**: `build_cycle_summary()` — pending/approved queue, next proposed action, blocked reason.
- **Progress**: `build_progress_board()`, `recommend_replan()`, replan signals, stalled/advancing.
- **Planner**: `load_current_goal()`, `load_latest_plan()`; compile/preview via CLI.
- **No existing**: natural-language “ask” endpoint, intent model, or grounded Q&A over this state.

## 2. What is missing for a real conversational control plane

- **Explicit intent model** for status, explanation, next-action, blocked-state, approval/review, project switch, plan preview, execution preview, policy question, artifact lookup.
- **NL → intent mapping**: parse operator phrase into intent + scope (e.g. project id, “next”, “blocked”) with confidence and preview; refusal when unclear.
- **Explainability layer**: answers to “what next?”, “why blocked?”, “why this project?”, “what changed?”, “what is this pack doing?”, “why in approval queue?” grounded in mission_control/project_case/progress/supervised_loop/lanes state.
- **Action preview**: for action-like intents, show concrete command/action, trust/approval/risk, require confirmation or handoff.
- **Single entrypoint**: e.g. `workflow-dataset ask "..."` that runs intent parsing → answer or preview → optional confirm.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `conversational/__init__.py` |
| Create | `conversational/intents.py` — Intent types (status, explanation, next_action, blocked_state, approval_review, project_switch, plan_preview, execution_preview, policy_question, artifact_lookup), ParsedIntent (intent_type, scope, confidence, ambiguity_note, suggested_command). |
| Create | `conversational/interpreter.py` — parse_natural_language(phrase, repo_root) → ParsedIntent; keyword/pattern first-draft; confidence; refusal/fallback when unclear. |
| Create | `conversational/explain.py` — answer_what_next(state), answer_why_blocked(project_id, state), answer_why_this_project(project_id, state), answer_what_changed(state), answer_approval_queue(state), answer_pack_doing(pack_ref, state); all grounded in state. |
| Create | `conversational/preview.py` — build_action_preview(parsed_intent, state) → preview text + suggested command + trust/approval note. |
| Create | `conversational/ask.py` — ask(phrase, repo_root) → response text + optional preview + confidence. |
| Modify | `cli.py` — add `ask` command: `workflow-dataset ask "..."`. |
| Create | `tests/test_conversational.py` |
| Create | `docs/M29E_M29H_CONVERSATIONAL_COMMAND_CENTER.md` |

## 4. Safety/risk note

- No execution from ask: only query, explain, and preview. Execution remains via explicit CLI or approval flow.
- All answers grounded in existing state (mission_control, project_case, progress, supervised_loop, lanes); no freeform generative bypass.
- Action preview shows exact suggested command and trust/approval implications; operator confirms elsewhere.
- Refusal/fallback when intent is ambiguous; no guessing dangerous actions.

## 5. What this block will NOT do

- No autonomous execution from natural language.
- No bypass of approval or trust gates.
- No replacement of CLI or mission-control; additive conversational layer only.
- No unconstrained chat or hidden state; every answer traceable to product state.
