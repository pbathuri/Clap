# M47E–M47H — High-Frequency Workflow Speed + Friction Reduction: Before Coding

## 1. What high-frequency workflows likely matter most now

- **Morning entry → first action**: `continuity_engine/morning_flow` builds `MorningEntryBrief` with change since last, top queue, first_mode/first_action/first_command. Default first_action is "Review inbox" or "Process queue"; handoff is `inbox list` or `queue view`. Repeated daily; any ambiguity or extra step multiplies.
- **Queue item → action**: `unified_queue` produces items with `actionability_class`, `routing_target`, `section_id`; `action_cards` have `HandoffTarget` (open_view, prefill_command, queue_simulated, approval_studio, compile_plan, executor_run). Path from "see item" to "do thing" can involve queue view → card accept → handoff; multiple surfaces.
- **Review item → decision**: `review_studio/inbox` builds intervention items (approval_queue, blocked_run, replan, stalled, etc.); decisions are apply/reject/defer. No single "grouped review" or "batch decision" flow; each item can require a separate context switch.
- **Continuity resume → correct context**: `continuity_engine/resume_flow`, `carry_forward_policy`; next session recommendation. If resume state is wrong or stale, user re-orients manually.
- **Operator routine → safe execution/review**: Founder pack recommends `operator_mode`, `review_and_approvals` after startup; routines (e.g. morning_ops, weekly_status) from `core_workflow_path`. Execution goes through supervised/approval; repeated "approve then run" adds steps.
- **Vertical draft/handoff → completion**: In-flow drafts, action cards with handoff to draft_composer or executor; common vertical path from "draft ready" to "applied" can have extra review or navigation.

## 2. Where handoff friction and repeated overhead exist

- **Queue → action**: Unified queue has `routing_target` but no single "route to action" API that returns the minimal next command or view; assist queue and action cards are separate; accepting a card then performing handoff is two steps.
- **Review → decision**: Inbox items and approval queue are built separately; no "grouped review" (e.g. "all approval_queue items" with batch approve/defer); each item = one decision surface.
- **Morning → first action**: `first_action`/`first_command` are heuristics (inbox list or queue view); not personalized to "most frequent successful morning path" for the vertical; no "repeat last successful morning" shortcut.
- **Resume → context**: Next session recommendation is in continuity store; not always aligned with "what the vertical user actually does next" (e.g. day start → queue vs. day start → focus_work); no "resume to last workflow" shortcut.
- **Operator routine**: Running a routine (e.g. morning_ops) may require: find routine → approve/run → wait; no "trusted shortcut" for routines that are already approved for the vertical.
- **Unnecessary branches**: Multiple entry points (inbox list, queue view, review studio, queue summary) for overlapping content; repeated transitions (startup → review_and_approvals → focus_work) without "skip if empty" or "combine steps" for calm days.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/vertical_speed/__init__.py` |
| Create | `src/workflow_dataset/vertical_speed/models.py` — FrequentWorkflow, FrictionCluster, RepeatedHandoff, SlowTransition, UnnecessaryBranch, RepeatValueBottleneck, SpeedUpCandidate |
| Create | `src/workflow_dataset/vertical_speed/identification.py` — Identify frequent workflows from vertical pack, queue, morning, continuity, action_cards (read-only aggregation) |
| Create | `src/workflow_dataset/vertical_speed/friction.py` — Build friction clusters (queue→action, review→decision, morning→first, resume→context, routine→execution), repeated handoffs, slow transitions |
| Create | `src/workflow_dataset/vertical_speed/action_route.py` — Fast route from queue item or review item to single command/view (route-to-action) |
| Create | `src/workflow_dataset/vertical_speed/repeat_value.py` — Repeat-value flows: prefilled defaults, grouped review hint, blocked-workflow recovery suggestion |
| Create | `src/workflow_dataset/vertical_speed/mission_control.py` — Mission control slice: top workflow, biggest friction cluster, speed-up candidate, repeat-value bottleneck, next recommended friction-reduction action |
| Modify | `src/workflow_dataset/cli.py` — vertical-speed top-workflows, friction-report, action-route, repeat-value |
| Modify | `src/workflow_dataset/mission_control/state.py` — vertical_speed_state |
| Modify | `src/workflow_dataset/mission_control/report.py` — [Vertical speed] section |
| Create | `tests/test_vertical_speed.py` |
| Create | `docs/samples/M47_frequent_workflow.json`, `M47_friction_cluster.json`, `M47_speed_up_candidate.json` |
| Create | `docs/M47E_M47H_VERTICAL_SPEED_DELIVERABLE.md` |

## 4. Safety/risk note

- No removal of trust/approval/review boundaries: route-to-action suggests the next command or view but does not auto-execute gated actions; grouped review is a recommendation, not auto-approve.
- All identification is read-only aggregation from existing stores (queue, assist, action_cards, morning, continuity, vertical pack); no new persistent state that could drift from source of truth.
- Speed-up candidates are suggestions; execution still goes through existing flows (approve then run, etc.).

## 5. Speed/friction-reduction principles

- **Fewer steps in common loops**: Prefer one command or one view that gets the user to the right place over "queue view → pick item → open card → handoff."
- **Better prefilled defaults**: When a route-to-action is known (e.g. top queue item → prefill_command), surface it as the default.
- **Clearer route-to-action**: For each high-value queue/review item, expose a single "do this" command or view_id.
- **Grouped review where appropriate**: Identify when multiple items can be reviewed in one surface (e.g. "5 approval items → open approval studio") and recommend that.
- **Faster recovery from minor blocked**: Suggest the minimal unblock (e.g. "run workflow-dataset recovery suggest --subsystem X") instead of generic "check mission control."
- **Calmer transitions**: Recommend "skip to focus_work if queue empty" or "combine startup + review if single item" to reduce mode thrash.

## 6. What this block will NOT do

- Will not remove or bypass trust, approval, or review gates.
- Will not optimize non-core verticals first; identification is scoped to the active vertical pack (e.g. founder_operator_core) when available.
- Will not rebuild queue, review_studio, continuity, or action_cards from scratch; will consume their APIs and add a speed/friction layer on top.
- Will not chase low-value micro-optimizations (e.g. caching unrelated to user-facing workflow steps).
