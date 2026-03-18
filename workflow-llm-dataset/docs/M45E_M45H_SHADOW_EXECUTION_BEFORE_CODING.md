# M45E–M45H — Shadow Execution + Confidence/Intervention Gates: Before Coding

## 1. What simulation/shadow/review behavior already exists

- **Executor** (`executor/`): `ExecutionRun`, `ActionEnvelope`, mode `simulate` | `trusted_real_candidate`; `run_with_checkpoints()` runs plan step-by-step, persists to hub, status `awaiting_approval` at checkpoints, `blocked` when step blocked; checkpoint decisions (proceed/cancel/defer); recovery decisions (retry/skip/substitute). No explicit “shadow run” or expected-vs-observed comparison.
- **Background run** (`background_run/`): `ExecutionMode.SIMULATE`, `DEGRADED_SIMULATE`, `SIMULATE_THEN_REAL`; `GatingResult` (allowed, simulate_only, approval_required, degraded_fallback); `evaluate_background_policy()`; `FailureRetryState` with handoff_to_review; async degraded fallback profiles (transient, blocked_approval, policy_suppressed, degraded_simulate). No per-step confidence or intervention gate types.
- **Desktop adapters**: `run_simulate()` dry-run only; `run_execute()` for real. Task demos `replay_task_simulate()`; lanes `run_lane_simulate()`; macros `macro_run(mode=simulate)`; job_packs `run_job(mode)`.
- **Benchmark board**: Slices, baseline/candidate, scorecard dimensions (task_success, safety_trust, etc.). No direct wiring to execution confidence.
- **Trust**: Presets, tiers, eligibility matrix (routine_type → max tier). Not yet used for shadow confidence thresholds.
- **Approvals**: Approval state and registry; executor/background respect approval_required. No “intervention gate” abstraction.
- **Audit**: Execution runs persisted in executor hub; no separate audit log model referenced in executor.

## 2. What is missing for real shadow execution and intervention gates

- **Shadow execution run**: A dedicated run type that (a) runs in shadow/simulated mode, (b) records expected outcome per step, (c) records observed outcome per step, (d) compares and stores drift.
- **Confidence/risk by step and loop**: Explicit confidence score and risk marker per step and aggregate for the loop; inputs from benchmark results, runtime stability, memory prior cases, trust posture, loop/step type, degraded mode.
- **Intervention gates**: Typed gates (must_review_next_step, must_stop_loop, may_continue_shadow_only, may_continue_bounded_real, must_downgrade_profile, must_handoff_human) with gate failure reason and clear semantics.
- **Safe-to-continue vs forced-takeover state**: Explicit state that either allows continuation (in shadow or bounded real) or forces takeover/handoff; no silent escalation.
- **CLI and mission control**: Commands to list/show shadow runs, confidence report, gate report, takeover; mission control visibility for active shadow runs, lowest-confidence step, next gate, takeover candidate, safe-to-promote run.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/shadow_execution/__init__.py` |
| Create | `src/workflow_dataset/shadow_execution/models.py` — ShadowRun, ExpectedOutcome, ObservedOutcome, ConfidenceScore, RiskMarker, InterventionGate, GateFailureReason, SafeToContinueState, ForcedTakeoverState |
| Create | `src/workflow_dataset/shadow_execution/confidence.py` — evaluate_confidence_step(), evaluate_confidence_loop(), evaluate_risk_step(), using benchmark, runtime, memory, trust, loop/step type, degraded |
| Create | `src/workflow_dataset/shadow_execution/gates.py` — gate types, evaluate_gates_for_run(), next_intervention_gate(), should_force_takeover() |
| Create | `src/workflow_dataset/shadow_execution/runner.py` — create_shadow_run(), run_shadow_loop() (simulate steps, record expected/observed, score confidence, apply gates) |
| Create | `src/workflow_dataset/shadow_execution/store.py` — save/load/list shadow runs |
| Modify | `src/workflow_dataset/cli.py` — shadow-runs list, show, confidence, gate-report, takeover |
| Modify | `src/workflow_dataset/mission_control/state.py` — shadow_execution_state block |
| Modify | `src/workflow_dataset/mission_control/report.py` — [Shadow execution] section |
| Create | `tests/test_shadow_execution.py` |
| Create | `docs/samples/M45_shadow_run.json`, gate report, takeover output |
| Create | `docs/M45E_M45H_SHADOW_EXECUTION_DELIVERABLE.md` |

## 4. Safety/risk note

- Shadow runs do not perform real actions by default; they simulate and record. Promotion to real (if any) remains gated by existing approval/trust.
- Intervention gates are explicit: when a gate fails, the run state reflects it (e.g. forced_takeover); no hidden override.
- This block does not add automatic production escalation or cloud simulation; all local and reviewable.
- Forced takeover is a state flag and CLI action to hand off to human; it does not auto-invoke external systems.

## 5. Intervention principles

- **Explicit gates**: Each gate has a type and optional failure reason; no implicit “confidence low” without a gate.
- **Bounded continuation**: “May continue bounded real” is a gate outcome that still respects existing approval/trust; shadow layer only adds the gate recommendation.
- **Takeover is explicit**: Forced takeover state is set when gates require it; operator sees it in gate-report and takeover CLI.
- **Safe-to-continue is explicit**: When the run may continue (shadow or bounded real), state says so with the applicable gate.

## 6. What this block will NOT do

- Will not replace or bypass executor, trust, approvals, or audit.
- Will not implement cloud or remote simulation infrastructure.
- Will not auto-promote shadow runs to real without existing approval flow.
- Will not remove or change existing simulate/real modes in executor or background_run.
