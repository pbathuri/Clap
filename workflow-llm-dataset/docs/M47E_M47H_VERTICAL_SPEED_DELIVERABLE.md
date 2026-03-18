# M47E–M47H — High-Frequency Workflow Speed + Friction Reduction: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/mission_control/state.py` | Added 6j: `vertical_speed_state` from `vertical_speed_slice()`. |
| `src/workflow_dataset/mission_control/report.py` | Added `[Vertical speed]` section: vertical_pack_id, top_workflow, friction_cluster, speed_up_candidate, repeat_value_bottleneck, next action. |
| `src/workflow_dataset/cli.py` | Added `vertical-speed` group and commands: top-workflows, friction-report, action-route, repeat-value. |

## 2. Files created

| File | Purpose |
|------|---------|
| `docs/M47E_M47H_VERTICAL_SPEED_BEFORE_CODING.md` | Before-coding: high-frequency workflows, friction, file plan, safety, principles, will NOT do. |
| `src/workflow_dataset/vertical_speed/__init__.py` | Public API. |
| `src/workflow_dataset/vertical_speed/models.py` | FrequentWorkflow, FrictionCluster, RepeatedHandoff, SlowTransition, UnnecessaryBranch, RepeatValueBottleneck, SpeedUpCandidate; WorkflowKind, FrictionKind. |
| `src/workflow_dataset/vertical_speed/identification.py` | list_frequent_workflows (morning, queue→action, review→decision, resume→context, operator routine, draft→completion); get_top_workflows; uses active vertical pack. |
| `src/workflow_dataset/vertical_speed/friction.py` | build_friction_clusters (queue→action handoff, review detour, morning transition, resume branch, routine approval); get_speed_up_candidates; get_repeat_value_bottlenecks. |
| `src/workflow_dataset/vertical_speed/action_route.py` | route_item_to_action (queue item → single command); get_grouped_review_recommendation; ROUTING_TO_COMMAND map. |
| `src/workflow_dataset/vertical_speed/repeat_value.py` | get_morning_first_action_prefill; get_blocked_recovery_suggestion; repeat_value_report (morning prefill, grouped review, blocked recovery, bottlenecks). |
| `src/workflow_dataset/vertical_speed/mission_control.py` | vertical_speed_slice for mission control. |
| `tests/test_vertical_speed.py` | 12 tests: models, identification, friction, action_route, repeat_value, mission_control, no-history. |
| `docs/samples/M47_frequent_workflow.json` | Sample frequent workflow (morning_entry_first_action). |
| `docs/samples/M47_friction_cluster.json` | Sample friction cluster (queue_to_action_handoff). |
| `docs/samples/M47_speed_up_candidate.json` | Sample speed-up candidate. |
| `docs/M47E_M47H_VERTICAL_SPEED_DELIVERABLE.md` | This deliverable. |

## 3. Exact CLI usage

```bash
workflow-dataset vertical-speed top-workflows [--limit 10] [--output out.json]
workflow-dataset vertical-speed friction-report [--output out.json]
workflow-dataset vertical-speed action-route [--item <item_id>]
workflow-dataset vertical-speed repeat-value [--output out.json]
```

## 4. Sample frequent-workflow report

From `vertical-speed top-workflows` (see `docs/samples/M47_frequent_workflow.json`):

- **workflow_id**: morning_entry_first_action  
- **label**: Morning entry → first action  
- **estimated_frequency**: daily  
- **entry_point**: continuity morning or day status  
- **typical_steps**: day start or resume, continuity morning, open queue or inbox, first action  
- **current_step_count**: 4, **suggested_step_count**: 2  

## 5. Sample friction cluster output

From `vertical-speed friction-report` (see `docs/samples/M47_friction_cluster.json`):

- **cluster_id**: queue_to_action_handoff  
- **kind**: handoff_overhead  
- **label**: Queue to action handoff  
- **repeated_handoffs**: queue view → action card/handoff, suggested_single_step: `workflow-dataset vertical-speed action-route --item <item_id>`  
- **impact_summary**: 4 steps typical; can reduce to 2 with route-to-action.  
- **suggested_action**: Use vertical-speed action-route for top queue item to get single command.  

## 6. Sample speed-up recommendation output

From friction-derived candidates (see `docs/samples/M47_speed_up_candidate.json`):

- **candidate_id**: route_top_queue_item  
- **label**: Route top queue item to single action  
- **workflow_id**: queue_item_to_action  
- **friction_cluster_id**: queue_to_action_handoff  
- **route_to_action**: workflow-dataset vertical-speed action-route  
- **expected_step_reduction**: 2  
- **priority**: high  

## 7. Exact tests run

```bash
pytest tests/test_vertical_speed.py -v
# 12 passed
```

## 8. Remaining gaps for later refinement

- **Observed frequency**: Workflows are identified from vertical pack and static patterns; no instrumentation yet of actual step counts or frequency from usage.
- **Route-to-action depth**: action_route maps routing_target and source to a command; could be extended to resolve action_cards source_ref to handoff_params.command for a tighter single command.
- **Grouped review UX**: Recommendation is "queue view --mode review"; no dedicated batch-approve or batch-defer API; review studio remains per-item.
- **Morning prefill one-click**: first_action_command is in the brief; no persisted "last successful morning command" or one-click surface in UI.
- **Blocked recovery**: Suggestion is recovery suggest or action-route; could integrate with repair_loops propose when subsystem is known.
- **Vertical pack fallback**: When no active pack is set, identification uses founder_operator_core; could default from workspace or day preset.
