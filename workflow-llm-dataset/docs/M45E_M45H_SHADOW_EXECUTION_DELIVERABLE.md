# M45E–M45H — Shadow Execution + Confidence/Intervention Gates: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `shadow-runs` Typer group with commands: list, show, confidence, gate-report, takeover, run. |
| `src/workflow_dataset/mission_control/state.py` | Added `shadow_execution_state` block: active_shadow_run_count, lowest_confidence_run_id/score, next_intervention_gate_run_id, forced_takeover_candidate_count, recent_safe_to_promote_run_id. |
| `src/workflow_dataset/mission_control/report.py` | Added "[Shadow execution]" section: active, takeover_candidates, lowest_confidence, next_gate, safe_to_promote. |

## 2. Files created

| File | Purpose |
|------|---------|
| `docs/M45E_M45H_SHADOW_EXECUTION_BEFORE_CODING.md` | Before-coding doc: existing behavior, gaps, file plan, safety, intervention principles, what we will not do. |
| `src/workflow_dataset/shadow_execution/__init__.py` | Package exports. |
| `src/workflow_dataset/shadow_execution/models.py` | ShadowRun, ExpectedOutcome, ObservedOutcome, ConfidenceScore, RiskMarker, InterventionGate, GateFailureReason, SafeToContinueState, ForcedTakeoverState, GateType. |
| `src/workflow_dataset/shadow_execution/confidence.py` | evaluate_confidence_step, evaluate_confidence_loop, evaluate_risk_step, evaluate_risk_loop (benchmark, runtime, memory, trust, degraded). |
| `src/workflow_dataset/shadow_execution/gates.py` | evaluate_gates_for_run, next_intervention_gate, should_force_takeover, compute_safe_to_continue, compute_forced_takeover. |
| `src/workflow_dataset/shadow_execution/runner.py` | create_shadow_run, run_shadow_loop (create from plan, run steps, record observed, score confidence/risk, apply gates). |
| `src/workflow_dataset/shadow_execution/store.py` | save_shadow_run, load_shadow_run, list_shadow_runs (under data/local/shadow_execution/runs). |
| `tests/test_shadow_execution.py` | Tests: run creation, confidence/risk, gates, safe-to-continue, forced takeover, persist, list, no-confidence case. |
| `docs/samples/M45_shadow_run.json` | Sample shadow run. |
| `docs/samples/M45_gate_report.json` | Sample gate report. |
| `docs/samples/M45_forced_takeover_output.json` | Sample forced-takeover output. |
| `docs/M45E_M45H_SHADOW_EXECUTION_DELIVERABLE.md` | This deliverable. |

## 3. Exact CLI usage

```bash
workflow-dataset shadow-runs list
workflow-dataset shadow-runs list --status completed --json
workflow-dataset shadow-runs show shadow_abc123
workflow-dataset shadow-runs show shadow_abc123 --json
workflow-dataset shadow-runs confidence shadow_abc123
workflow-dataset shadow-runs confidence shadow_abc123 --json
workflow-dataset shadow-runs gate-report shadow_abc123
workflow-dataset shadow-runs gate-report shadow_abc123 --json
workflow-dataset shadow-runs takeover shadow_abc123
workflow-dataset shadow-runs takeover shadow_abc123 --json
workflow-dataset shadow-runs run --plan-ref weekly_status_from_notes --plan-source job
workflow-dataset shadow-runs run --plan-ref morning_ops --plan-source routine --project founder_case_alpha --json
```

## 4. Sample shadow run

See `docs/samples/M45_shadow_run.json`. Summary: shadow_run_id, plan_source/plan_ref, status=completed, expected_outcomes and observed_outcomes per step, confidence_loop (score, factors), confidence_step list, risk_markers, safe_to_continue (may_continue, mode_allowed), forced_takeover (forced=false).

## 5. Sample confidence/gate report

See `docs/samples/M45_gate_report.json`. Gates: must_review_next_step, must_stop_loop, may_continue_shadow_only, may_continue_bounded_real, must_downgrade_profile, must_handoff_human; each with passed, failure_reason when failed, recommended_action. safe_to_continue and forced_takeover summary.

## 6. Sample forced-takeover output

See `docs/samples/M45_forced_takeover_output.json`. When forced_takeover.forced is true: reason, failed_gate_type=must_handoff_human, handoff_summary for operator.

## 7. Exact tests run

```bash
python3 -m pytest tests/test_shadow_execution.py -v
```

All 9 tests passed: test_shadow_run_creation, test_confidence_step_evaluation, test_confidence_loop_evaluation, test_risk_step_and_loop, test_gates_evaluation, test_safe_to_continue_and_forced_takeover, test_run_shadow_loop_persist, test_list_shadow_runs, test_no_confidence_weak_evidence.

## 8. Exact remaining gaps for later refinement

- **Executor wiring**: run_shadow_loop currently records observed outcomes from expected (placeholder match). A later step can wire to executor.run_with_checkpoints(mode=simulate) and map real step results to ObservedOutcome with drift comparison.
- **Benchmark contribution**: _benchmark_contribution uses eval board report; could be refined to use plan_ref/step-specific benchmark results when available.
- **Degraded detection**: Runtime stability uses a file data/local/reliability/degraded_active.json; could be wired to reliability harness or background_run degraded state when that API is stable.
- **Promotion path**: “Safe-to-promote” is surfaced in mission control; no CLI or flow yet to promote a shadow run to a real run (would still go through existing approval/executor).
- **Gate tuning**: Thresholds (CONFIDENCE_GATE_THRESHOLD, etc.) are constants; could become configurable or profile-based.
- **Audit**: Shadow runs are stored under data/local/shadow_execution; integration with audit log or executor hub for unified run history is not implemented.
