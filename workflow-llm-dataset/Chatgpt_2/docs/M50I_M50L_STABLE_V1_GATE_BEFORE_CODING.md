# M50I–M50L — Final Release Decision Pack + Stable v1 Readiness Gate: Before Coding

## 1. What release/readiness/gate structures already exist

- **Production launch** (`production_launch/`): `LaunchDecision` (launch, launch_narrowly, pause, repair_and_review); `build_launch_decision_pack` aggregates vertical, gate results, blockers/warnings from release_readiness + production gates; `evaluate_production_gates` (supported surface, deployment bundle, upgrade/recovery, trust, reliability golden path, operator playbooks, vertical first-value, release_readiness_not_blocked).
- **Stability reviews** (`stability_reviews/`): `StabilityDecision` (continue, continue_with_watch, narrow, repair, pause, rollback); `StabilityDecisionPack` + `EvidenceBundle`; `build_stability_decision_pack` aggregates launch pack, ongoing summary, post-deployment guidance, review cycles, sustained-use checkpoints, triage/reliability; thresholds and rollback policy; `build_decision_output` produces rationale and recommended_actions.
- **Release readiness** (`release_readiness/`): `build_release_readiness` → status (ready | blocked | degraded), blockers, warnings, supportability; gates (env, acceptance, first_user_ready, release_readiness_not_blocked, trust_approval_ready).
- **Production cut** (`production_cut/`): Scope freeze, locked vertical, surfaces (included/excluded/quarantined), `get_active_cut`, `build_frozen_scope_report`.
- **v1 ops** (`v1_ops/`): `build_v1_support_posture`, `build_stable_v1_maintenance_pack`; mission-control slice: support posture, overdue maintenance, top v1 risk, recommended_stable_v1_support_action, rollback readiness.
- **Continuity confidence** (`continuity_confidence/`): Post-restore confidence, device class, post-restore presets, safe operating guidance; mission-control slice for post-restore readiness.
- **Deploy bundle** (`deploy_bundle/`): Health, upgrade/rollback readiness, recovery posture.
- **Reliability** (`reliability/`): Latest run outcome, golden paths.
- **Vertical selection** (`vertical_selection/`): Active vertical, scope report.
- **CLI**: `launch-decision-pack`, `production-gates`, `stability-reviews`, `stability-decision`, `v1-ops` (status, support-posture, maintenance-pack, etc.).

There is **no** dedicated “v1 contract” module; production_cut + release_readiness + launch decision + stability decision + v1_ops collectively represent the frozen scope and operational discipline.

## 2. What is missing for a true stable-v1 gate

- **Explicit stable-v1 recommendation**: A single yes/no/narrow/repair/reject outcome labeled as “stable v1” (not just “launch” or “continue”).
- **Final evidence bundle** scoped to “does the system meet the v1 contract?” (contract = scope freeze + support posture + gates + migration readiness + sustained health).
- **Gate blockers and gate warnings** typed for the stable-v1 gate (can reuse/adapt launch blockers/warnings but with stable_v1 semantics).
- **Final decision outputs**: stable v1 approved; approved with narrow conditions; not yet — repair required; not yet — scope must narrow further; with confidence/rationale and evidence refs.
- **CLI and mission-control** for: stable-v1 gate evaluation, report, blockers, decision, explain; and a mission-control slice (current recommendation, top blocker, narrow condition, evidence for/against, next action).
- **Single entry point** that assembles all evidence and produces the final release decision artifact for stable v1.

## 3. Exact file plan

| Area | Path | Purpose |
|------|------|--------|
| Doc | `docs/M50I_M50L_STABLE_V1_GATE_BEFORE_CODING.md` | This before-coding analysis. |
| Models | `src/workflow_dataset/stable_v1_gate/models.py` | StableV1ReadinessGate, FinalEvidenceBundle, GateBlocker, GateWarning, StableV1Recommendation (approved / narrow / repair / reject), ConfidenceSummary. |
| Evidence | `src/workflow_dataset/stable_v1_gate/evidence.py` | Aggregate evidence from launch pack, production cut, release readiness, stability pack, v1_ops, continuity, deploy health, vertical value, drift/repair (read-only calls). |
| Gate | `src/workflow_dataset/stable_v1_gate/gate.py` | Evaluate gate (blockers/warnings from evidence), produce gate result. |
| Decision | `src/workflow_dataset/stable_v1_gate/decision.py` | Map evidence + gate to final recommendation (approved / narrow / repair / reject) and rationale. |
| Report | `src/workflow_dataset/stable_v1_gate/report.py` | Build full stable-v1 report (evidence + blockers + warnings + decision + explain). |
| Mission | `src/workflow_dataset/stable_v1_gate/mission_control.py` | Slice: current_stable_v1_recommendation, top_final_blocker, narrow_v1_condition, strongest_evidence_for, strongest_evidence_against, next_required_final_action. |
| Package | `src/workflow_dataset/stable_v1_gate/__init__.py` | Exports. |
| CLI | `src/workflow_dataset/cli.py` | New `stable_v1_group`: gate, report, blockers, decision, explain. |
| Mission state | `src/workflow_dataset/mission_control/state.py` | Add `stable_v1_gate_state` from mission_control slice. |
| Report print | `src/workflow_dataset/mission_control/report.py` | Optional [stable v1 gate] section. |
| Tests | `tests/test_stable_v1_gate.py` | Gate creation, evidence aggregation, blocker/warning handling, decision outputs, weak/contradictory/no-go/narrow-go cases. |
| Samples | `docs/samples/M50_stable_v1_report.json`, `M50_stable_v1_decision.json` | Sample report and decision output. |
| Gaps | `docs/M50I_M50L_STABLE_V1_GATE_REMAINING_GAPS.md` | Remaining gaps for later refinement. |

## 4. Safety/risk note

- The gate is **advisory**: it produces a recommendation and evidence; it does not auto-approve or auto-reject releases. Operators retain final authority.
- All evidence is **read-only** from existing layers; no changes to production_cut, release_readiness, or deployment state.
- Blockers/warnings are derived from existing launch and release_readiness semantics; no new arbitrary blocking criteria without grounding in existing gates/readiness.
- “Stable v1” is a **gated status**: the gate says whether the current product state meets the v1 contract; it does not move goalposts or redefine scope after the fact.

## 5. Stable-v1 gate principles

- **Evidence-backed**: Every recommendation is tied to aggregated evidence (launch pack, stability pack, production cut, v1_ops, continuity, deploy health, vertical value, drift/repair).
- **Explicit outcome**: One of: stable v1 approved; approved with narrow conditions; not yet — repair required; not yet — scope must narrow further.
- **Contract-grounded**: v1 contract = production-cut scope freeze + release/reliability/support posture + governance and review safety + migration/continuity readiness + sustained deployment health + vertical value retention + long-run drift/repair outcomes.
- **No new launch report**: This is the **final** release decision system for stable v1, not another status dashboard.
- **Roadmap-horizon artifact**: The decision and report form the final roadmap-horizon artifact for “can we call this stable v1?”.

## 6. What this block will NOT do

- Rebuild or replace release_readiness, production_launch, stability_reviews, v1_ops, production_cut, continuity_confidence, or deploy_bundle.
- Optimize for future roadmap items beyond stable v1.
- Add new production gates or change existing gate logic; we consume their results.
- Enforce the decision automatically (no auto-lock or auto-release).
- Define or change the v1 contract content (Pane 1); we consume scope freeze and existing posture as given.
