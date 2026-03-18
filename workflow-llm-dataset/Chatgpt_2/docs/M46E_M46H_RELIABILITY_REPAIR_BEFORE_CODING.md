# M46E–M46H — Reliability Repair Loops + Maintenance Control: Before Coding

## 1. What repair/maintenance behavior already exists

- **Context drift** (`context/drift.py`): `compare_snapshots` yields newly_blocked_jobs, newly_recommendable_jobs, approvals_changed; used by progress replan signals and daily digest.
- **Edge drift** (`edge/drift.py`): `compute_drift` compares readiness checks (worse/improved); no repair execution.
- **Progress signals** (`progress/signals.py`): ReplanSignal from new_blocker, repeated_failed_action, capability_changed; feeds replan, not repair loops.
- **Reliability** (`reliability/`): Harness runs golden paths (pass/degraded/blocked/fail); `RecoveryCase` playbooks (broken_pack_state, failed_upgrade, etc.) with steps_guide; `DegradedModeProfile` and `FallbackRule` (fallback_matrix); recovery_playbooks suggest steps but do not execute or track a repair plan.
- **Ops jobs** (`ops_jobs/`): Registry has reliability_refresh, queue_calmness_review, triage_health, etc.; run_command, escalation_targets; no “repair plan” or “maintenance control” abstraction.
- **Council** (`council/`): run_council_review, save_review, promotion_policy; used for model/candidate review, not repair approval.
- **Background run**: Simulate/real gating, degraded fallback; no repair-loop trigger.
- **Trust/approvals**: Approval state and registry; no repair-specific approval gate.

## 2. What is missing for bounded repair loops

- **Repair loop model**: Explicit repair_loop_id, target subsystem, preconditions, bounded repair plan (ordered actions), required_review_gate, repair_result, rollback_on_failed_repair, post_repair_verification.
- **Signal → repair mapping**: Translating drift/degradation signals (e.g. reliability outcome=degraded, subsystem=packs) into a proposed maintenance action or repair pattern (e.g. memory_curation_refresh, queue_calmness_retune, runtime_fallback_reset).
- **Maintenance control flow**: Propose repair plan → review → approve bounded repair → execute (bounded actions) → verify outcome → escalate if failed → rollback if needed.
- **Known repair patterns**: First-draft patterns (queue calmness re-tune, memory curation refresh, runtime route fallback reset, operator-mode narrowing, automation suppression, benchmark refresh, degraded quarantine, continuity reconciliation) as templates, not hidden self-healing.
- **CLI and mission control**: repair-loops list/propose/show/execute/verify; mission control visibility for top repair-needed subsystem, active repair loop, failed repair, verified repair, next recommended maintenance action.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/repair_loops/__init__.py` |
| Create | `src/workflow_dataset/repair_loops/models.py` — RepairLoop, MaintenanceAction, RepairTargetSubsystem, Precondition, BoundedRepairPlan, RequiredReviewGate, RepairResult, RollbackOnFailedRepair, PostRepairVerification |
| Create | `src/workflow_dataset/repair_loops/patterns.py` — Known repair patterns (queue_calmness_retune, memory_curation_refresh, etc.) as BoundedRepairPlan templates |
| Create | `src/workflow_dataset/repair_loops/signal_to_repair.py` — Map drift/reliability signals to proposed repair plan |
| Create | `src/workflow_dataset/repair_loops/flow.py` — propose_repair_plan, review_repair_plan, approve_bounded_repair, execute_bounded_repair, verify_repair, escalate_if_failed, rollback_if_needed |
| Create | `src/workflow_dataset/repair_loops/store.py` — save/load/list repair loops and plans |
| Modify | `src/workflow_dataset/cli.py` — repair-loops list, propose, show, execute, verify |
| Modify | `src/workflow_dataset/mission_control/state.py` — repair_loops_state block |
| Modify | `src/workflow_dataset/mission_control/report.py` — [Repair loops] section |
| Create | `tests/test_repair_loops.py` |
| Create | `docs/samples/M46_repair_plan.json`, execution/verification, failed escalation |
| Create | `docs/M46E_M46H_RELIABILITY_REPAIR_DELIVERABLE.md` |

## 4. Safety/risk note

- All repair actions are bounded and explicit; no hidden self-healing. Execute step runs only actions listed in the approved plan (e.g. CLI commands or ops-job triggers).
- Review gate is required before execute; approval respects existing trust/approval surfaces (no bypass).
- Rollback-on-failed-repair is a defined step (e.g. revert config, re-enable suppressed automation); no automatic architecture change.
- Escalation routes to council/recovery/operator as already defined (escalation_targets); no new autonomous escalation path.

## 5. Maintenance-control principles

- **Explicit**: Every repair plan has a visible list of actions and a required review gate; operator sees what will run.
- **Bounded**: Plan is finite and scoped to a target subsystem or pattern; no open-ended “fix everything.”
- **Reviewable**: propose → review → approve before execute; verify after execute.
- **Reversible**: Rollback path is part of the model; failed repair can trigger rollback and escalation.

## 6. What this block will NOT do

- Will not create hidden self-healing or autonomous repair without review.
- Will not bypass trust, approval, or council/review boundaries.
- Will not rebuild ops_jobs, reliability harness, or recovery playbooks from scratch; will use them as inputs and optionally trigger jobs.
- Will not implement cloud maintenance orchestration; local-first only.
- Will not blur repair (restore degraded state) with promotion of new behavior (e.g. candidate rollback is a defined pattern, not general “promote”).
