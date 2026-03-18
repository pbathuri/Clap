# M46E–M46H — Reliability Repair Loops + Maintenance Control: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/mission_control/state.py` | Added 6i: `repair_loops_state` from `repair_loops_mission_control_slice`. |
| `src/workflow_dataset/mission_control/report.py` | Added `[Repair loops]` section: top_repair_needed, active_loop, failed_requiring_escalation, verified_successful, next. |

## 2. Files created

| File | Purpose |
|------|---------|
| `docs/M46E_M46H_RELIABILITY_REPAIR_BEFORE_CODING.md` | Before-coding: existing behavior, gaps, file plan, safety, principles, will NOT do. |
| `src/workflow_dataset/repair_loops/__init__.py` | Public API. |
| `src/workflow_dataset/repair_loops/models.py` | RepairLoop, BoundedRepairPlan, MaintenanceAction, RepairTargetSubsystem, Precondition, RequiredReviewGate, RepairResult, PostRepairVerification, RollbackOnFailedRepair. |
| `src/workflow_dataset/repair_loops/patterns.py` | Known patterns: queue_calmness_retune, memory_curation_refresh, runtime_route_fallback_reset, operator_mode_narrowing, automation_suppression, benchmark_refresh_rollback, degraded_feature_quarantine, continuity_resume_reconciliation. |
| `src/workflow_dataset/repair_loops/signal_to_repair.py` | propose_plan_from_signal, propose_plan_from_reliability_run, propose_plan_from_drift, list_signal_mappings. |
| `src/workflow_dataset/repair_loops/flow.py` | propose_repair_plan, review_repair_plan, approve_bounded_repair, execute_bounded_repair, verify_repair, escalate_if_failed, rollback_if_needed. |
| `src/workflow_dataset/repair_loops/store.py` | save_repair_loop, load_repair_loop, list_repair_loops; data under `data/local/repair_loops/loops/`. |
| `src/workflow_dataset/repair_loops/mission_control.py` | repair_loops_mission_control_slice for dashboard. |
| `src/workflow_dataset/cli.py` | repair-loops list, propose, show, approve, execute, verify, escalate, rollback. |
| `tests/test_repair_loops.py` | Tests for models, patterns, signal→repair, flow, store, mission control, no-known-repair, execute-without-approve, rollback/escalate/verify guards. |
| `docs/samples/M46_repair_plan.json` | Sample repair loop (proposed) JSON. |
| `docs/M46E_M46H_RELIABILITY_REPAIR_DELIVERABLE.md` | This deliverable. |

## 3. Exact CLI usage

```bash
# List repair loops (optional --status filter, --limit)
workflow-dataset repair-loops list
workflow-dataset repair-loops list --status approved --limit 20

# Propose from drift or reliability signal
workflow-dataset repair-loops propose --from drift_123
workflow-dataset repair-loops propose --from run_abc --signal-type reliability_run --subsystem packs
workflow-dataset repair-loops propose --from drift_1 --pattern queue_calmness_retune

# Show one loop
workflow-dataset repair-loops show --id rl_<id>

# Approve (required before execute)
workflow-dataset repair-loops approve --id rl_<id> --by operator

# Execute approved plan (runs actions via workflow-dataset CLI)
workflow-dataset repair-loops execute --id rl_<id>

# Run post-repair verification
workflow-dataset repair-loops verify --id rl_<id>

# Escalate failed/rolled-back repair
workflow-dataset repair-loops escalate --id rl_<id> --reason "Manual escalation"

# Rollback failed repair (actions with rollback_command)
workflow-dataset repair-loops rollback --id rl_<id>
```

## 4. Sample repair plan

See `docs/samples/M46_repair_plan.json`: proposed loop for "Queue calmness re-tune" with two actions (queue summary, queue calmness review), operator_approval gate, verification command queue summary, escalation_target mission_control.

## 5. Sample repair execution / verification output

```
$ workflow-dataset repair-loops execute --id rl_abc123
Executed: rl_abc123  status=verifying
  queue_summary: success  ...
  queue_calmness_review: success  ...
Next: workflow-dataset repair-loops verify --id rl_abc123

$ workflow-dataset repair-loops verify --id rl_abc123
Verification: passed=True  status=verified
```

## 6. Sample failed-repair escalation output

```
$ workflow-dataset repair-loops execute --id rl_xyz
Executed: rl_xyz  status=failed
  queue_summary: success  ...
  queue_calmness_review: success=False  workflow-dataset not found
Repair failed. Consider: repair-loops rollback --id rl_xyz  or repair-loops escalate --id rl_xyz

$ workflow-dataset repair-loops escalate --id rl_xyz --reason "CLI not in PATH"
Escalated: rl_xyz  reason=Manual escalation
```

## 7. Exact tests run

```bash
pytest tests/test_repair_loops.py -v
```

Tests cover: repair loop model, known patterns, propose from reliability_run/drift/signal override, list_signal_mappings, no-known-repair and override; propose_repair_plan + save/load/list; review and approve flow; execute requires approved; verify/escalate/rollback require correct state; mission control slice; execute-without-approve returns None.

## 8. Remaining gaps for later refinement

- **Drift IDs**: `--from drift_123` is a placeholder; Pane 1 drift layer may expose concrete drift IDs to pass here.
- **CLI discovery**: Some patterns call subcommands that may not exist in every environment (e.g. `memory-curation refresh`, `operator-mode narrow`, `automations pause`, `continuity reconcile`, `quarantine feature`). Execute records success/failure; missing commands surface as failed action and optional rollback.
- **Council integration**: Review gate kind `council_review` is modeled but not wired to `run_council_review`; approval is operator-only in this draft.
- **Verification semantics**: Verification command is run once; no retries or threshold for “verified”.
- **Mission control next_action**: Recommendation string is heuristic (show/execute/verify/escalate/rollback/propose); could be driven by a small rules table.
- **No-known-repair UX**: When no pattern matches, CLI exits 1; could suggest `recovery suggest --subsystem X` or list known pattern IDs.
