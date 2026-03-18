# M32I–M32L Guided Action Cards + One-Click Safe Handoffs — Before Coding

## 1. What action-preview / execution-handoff pieces already exist

- **supervised_loop**: `QueuedAction` (action_id, label, action_type, plan_ref, plan_source, mode, why, risk_level); `ApprovalQueueItem` (queue_id, action, status pending|approved|rejected|deferred); `ExecutionHandoff` (handoff_id, queue_id, action_type, run_id, status, outcome_summary, artifact_paths); `execute_approved(queue_id)` → runs executor/planner and records handoff. Queue: `enqueue_proposal`, `list_pending`, approve/reject/defer. Store: cycle, approval_queue.json, handoffs.json.
- **conversational/preview**: `build_action_preview(parsed_intent, state)` — text preview for INTENT_EXECUTION_PREVIEW_REQUEST, INTENT_PLAN_PREVIEW_REQUEST, INTENT_APPROVAL_REVIEW_QUERY, INTENT_PROJECT_SWITCH_REQUEST; suggests command and notes “no execution from ask”.
- **planner**: `compile_goal_to_plan(goal, mode)`; `format_plan_preview(plan)`; Plan with steps, checkpoints, expected_artifacts.
- **executor**: `run_with_checkpoints(plan_source, plan_ref, mode, …)`; `resume_run`; mode simulate|real.
- **desktop_adapters**: `run_simulate(adapter_id, action_id, params)` — dry-run preview; `run_execute` — real execution; ApprovalRegistry (approved_paths, approved_apps, approved_action_scopes).
- **trust**: `build_trust_cockpit`, `safe_to_expand`, release gates.
- **personal**: Suggestions in graph_store (suggestion_id, type, title, description, confidence, status); style_suggestion_engine (StyleAwareSuggestion); graph_review_inbox (routine/pattern accept/reject/edit).
- **review_studio**: `build_inbox()` — intervention items (approval_queue, blocked_run, replan, skill_candidate, policy, stalled, graph_routine_confirmation, graph_pattern_review).
- **mission_control/next_action**: `recommend_next_action(state)` — high-level build|benchmark|cohort_test|promote|hold|rollback|replay_task|observe_setup.
- **materialize**: `materialize_from_suggestion(context_bundle, workspace_root, suggestion_id, …)` — suggestion → sandbox artifact.
- **copilot**: `build_plan_for_job`, recommendations, plan/run.

## 2. What is missing for a real guided action-card layer

- **Explicit action card model**: A first-class “action card” that has: source suggestion ref, title/description, action preview (what would happen), trust/approval requirement, handoff target (planner | executor | workspace | review_studio | open_view | prefill_command), reversible flag, expected artifact/output, card state (pending | accepted | dismissed | executed | blocked).
- **Suggestion-to-card pipeline**: Transform accepted suggestions (from personal/suggestions, graph_review accepted routines, style suggestions, or copilot recommendations) into action cards with a concrete handoff_type and params (e.g. plan_ref, command, view_id, suggestion_id).
- **Card store**: Persist cards (create, list, get, update state) so they survive across sessions and can be shown in CLI/mission control.
- **Preview generation**: For each card, produce a consistent “action preview” (human-readable what-would-happen, approval note, simulate-vs-real).
- **One-click safe handoff execution**: A single entry point that, given a card id: opens a target view, or prefills a command/goal, or enqueues a simulated run to the approval queue, or navigates to review/approval studio, or creates a draft artifact in sandbox, or compiles a plan — without hidden execution; all previewable first.
- **Blocked/approval handling**: Cards that require approval show “blocked” or “awaiting_approval” and link to the approval queue or review surface; no bypass of trust/approval.
- **CLI**: `action-cards list`, `action-cards show --id X`, `action-cards accept`, `action-cards dismiss`, `action-cards preview --id X`, `action-cards execute --id X`.
- **Mission control**: Block for action cards: highest-value card, blocked count, recent executed, awaiting approval handoff, recent outcomes.

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|--------|
| Create | `src/workflow_dataset/action_cards/__init__.py` | Package exports. |
| Create | `src/workflow_dataset/action_cards/models.py` | ActionCard, ActionPreview, HandoffTarget (enum), CardState (enum), TrustRequirement; source_suggestion ref, expected_artifact. |
| Create | `src/workflow_dataset/action_cards/store.py` | Card store (JSON under data/local/action_cards): save_card, load_card, list_cards (filter by state), update_card_state. |
| Create | `src/workflow_dataset/action_cards/builder.py` | suggestion_to_cards: from personal suggestions table, graph_review accepted items, style suggestions → list of ActionCard with handoff_type and params. |
| Create | `src/workflow_dataset/action_cards/preview.py` | build_preview(card) → ActionPreview (summary, what_would_happen, trust_note, command_hint). |
| Create | `src/workflow_dataset/action_cards/handoff.py` | execute_handoff(card_id, repo_root): resolve card → open_view | prefill_command | queue_simulated | approval_studio | create_draft | compile_plan; call planner/executor/supervised_loop/materialize as needed; respect approval/trust; return outcome dict. |
| Create | `src/workflow_dataset/cli.py` (extend) | Add action_cards_group: list, show, accept, dismiss, preview, execute. |
| Extend | `src/workflow_dataset/mission_control/state.py` | Add action_cards_summary: highest_value_card, blocked_count, recent_executed, awaiting_approval_count, recent_outcomes. |
| Extend | `src/workflow_dataset/mission_control/report.py` | Add [Action cards] line(s) from action_cards_summary. |
| Create | `tests/test_action_cards.py` | Card create, preview, handoff (simulate path), blocked, trust note. |
| Create | `docs/M32I_M32L_ACTION_CARDS.md` | Short doc: model, flow, CLI, safety. |
| Create | `docs/M32I_M32L_DELIVERABLE.md` | Deliverable: files, samples, tests, gaps. |

## 4. Safety/risk note

- **No hidden execution**: execute_handoff only performs the handoff type declared on the card (e.g. “queue to approval” or “open view”); real execution only after operator approves via existing supervised_loop/approval flow.
- **Preview always available**: Every card has a preview; execute is optional and explicit.
- **Trust/approval preserved**: Handoffs that would run real executor or desktop_adapters go through existing approval queue or check ApprovalRegistry/trust; we do not add new bypass paths.
- **Reversible/dismissible**: Cards can be dismissed; “accept” means “confirm card and enable execute”, not “run without further confirmation” unless the handoff_type is explicitly “open_view” or “prefill_command” (no execution).

## 5. What this block will NOT do

- Will **not** bypass trust/approval/policy gates; real execution still goes through supervised_loop or approval registry.
- Will **not** create hidden or autonomous execution; every handoff is user-initiated (e.g. `action-cards execute --id X`).
- Will **not** rebuild executor, planner, workspace, or review_studio; we call into them.
- Will **not** hide what a card would do; preview and show are first-class.
- Will **not** implement full desktop autopilot; only guided, explicit micro-handoffs.
