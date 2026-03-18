# M50I–M50L — Stable v1 Gate: Remaining Gaps for Later Refinement

## Delivered in this block

- Models: `StableV1ReadinessGate`, `FinalEvidenceBundle`, `GateBlocker`, `GateWarning`, `StableV1Recommendation`, `StableV1Decision`, `ConfidenceSummary`, `StableV1Report`.
- Evidence aggregation from: production cut, release readiness, launch decision pack, stability decision pack, v1_ops, continuity_confidence, deploy_health, vertical value, drift/repair.
- Gate evaluation: blockers (production_cut not frozen, release_readiness blocked, launch pause/repair, stability pause/rollback/repair); warnings (degraded, launch_narrowly, stability narrow/watch, v1_ops/continuity errors).
- Final decision: stable_v1_approved, stable_v1_approved_narrow, not_yet_repair_required, not_yet_scope_narrow.
- CLI: `workflow-dataset stable-v1 gate | report | blockers | decision | explain`.
- Mission-control slice: `stable_v1_gate_state` with recommendation, top blocker, narrow condition, evidence for/against, next action.
- Tests: 18 tests for models, gate evaluation, decision mapping, report, explain, state slice.

## Remaining gaps (for later refinement)

1. **v1 contract explicit artifact**  
   The gate infers “v1 contract” from production cut + release readiness. Pane 1 may introduce a frozen v1 contract file or schema; the gate could then read that artifact directly and add a dedicated evidence field.

2. **Configurable gate criteria**  
   Blocker/warning rules are hardcoded in `gate.py`. Later: allow override via config (e.g. which launch/stability decisions block, or downgrade some blockers to warnings).

3. **Persistence of decision**  
   Decision is computed on demand only. Optional: persist last stable-v1 decision (e.g. to `data/local/stable_v1_gate/last_decision.json`) for audit and “last approved at” visibility.

4. **Strongest evidence for/against**  
   Currently short heuristics. Later: rank evidence by source weight or operator-defined priority and surface top N for/against.

5. **Narrow condition details**  
   For `stable_v1_approved_narrow`, narrow_condition is a concatenation of warning summaries. Could be structured (e.g. list of conditions with source and remediation).

6. **Integration with release workflow**  
   No automatic hook into release packaging or tagging. Later: optional “pre-tag” check that runs the gate and fails the step if recommendation is not approved or approved_narrow.

7. **Time-windowed evidence**  
   Evidence is point-in-time. For “sustained” stable v1, later: optionally require N consecutive gate passes or stability “continue” windows before recommending approved.

8. **Local_sources in evidence**  
   `FinalEvidenceBundle.raw_snapshot` holds raw payloads but not paths. Mission-control already has `local_sources`; could add stable_v1_gate evidence paths for provenance.

9. **Doc and runbook**  
   Add a short operator runbook: “How to run the stable-v1 gate before release” and “How to interpret approved / narrow / repair / scope_narrow” with concrete follow-up commands.

10. **No-go and narrow-go regression tests**  
    Tests are unit-style with explicit evidence. Add one or two integration-style tests (e.g. with a minimal fixture repo) that assert no-go when production_cut is missing and narrow-go when only warnings exist, if such a fixture can run without hanging.
