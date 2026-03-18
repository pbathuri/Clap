# M46I–M46L — Sustained Deployment Review Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `stability_reviews_group` and `stability_decision_group` with commands: stability-reviews latest/generate/history, stability-decision pack/explain. |
| `src/workflow_dataset/mission_control/state.py` | Added `stability_reviews` slice: current_sustained_use_recommendation, top_stability_risk, next_scheduled_deployment_review_iso, watch_degraded_repair_state, strongest_reason_to_continue, strongest_reason_to_pause; and local_sources["stability_reviews"]. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M46I_M46L_SUSTAINED_DEPLOYMENT_REVIEW_BEFORE_CODING.md` | Before-coding doc: existing structures, gaps, file plan, safety, principles, “what we will not do”. |
| `src/workflow_dataset/stability_reviews/__init__.py` | Package exports. |
| `src/workflow_dataset/stability_reviews/models.py` | SustainedDeploymentReview, StabilityWindow, StabilityDecisionPack, StabilityDecision, Continue/Narrow/Repair/Pause/RollbackRecommendation, EvidenceBundle. |
| `src/workflow_dataset/stability_reviews/store.py` | save_review, load_latest_review, list_reviews, get_review_by_id; persistence under data/local/stability_reviews/reviews_index.json. |
| `src/workflow_dataset/stability_reviews/pack_builder.py` | build_stability_decision_pack: assembles evidence from launch_decision_pack, ongoing_summary, post_deployment_guidance, review_cycles, sustained_use, triage/reliability (read-only); produces EvidenceBundle + StabilityDecisionPack. |
| `src/workflow_dataset/stability_reviews/decisions.py` | build_decision_output, explain_stability_decision: continue/narrow/repair/pause/rollback outputs with rationale and evidence links. |
| `tests/test_stability_reviews.py` | Focused tests: decision-pack generation, evidence-bundle composition, continue/narrow/repair/pause/rollback outcomes, contradictory evidence, no-review/weak-evidence, historical review tracking. |
| `docs/M46I_M46L_SUSTAINED_DEPLOYMENT_REVIEW_DELIVERABLE.md` | This file. |

## 3. Exact CLI usage

```bash
# Latest sustained deployment review (if any)
workflow-dataset stability-reviews latest [--repo-root PATH] [--json]

# Generate stability decision pack and optionally persist review
workflow-dataset stability-reviews generate [--repo-root PATH] [--window daily|weekly|rolling_7|rolling_30] [--write|--no-write] [--json]

# List sustained deployment reviews (newest first)
workflow-dataset stability-reviews history [--repo-root PATH] [--limit N] [--json]

# Build stability decision pack (no persist)
workflow-dataset stability-decision pack [--repo-root PATH] [--window rolling_7] [--json]

# Explain current stability decision
workflow-dataset stability-decision explain [--repo-root PATH]
```

## 4. Sample stability decision pack (JSON shape)

```json
{
  "recommended_decision": "continue_with_watch",
  "rationale": "Continue operating; evidence is weak or warnings present—watch state.",
  "evidence_refs": ["launch_decision_pack", "post_deployment_guidance", "ongoing_summary", "evidence_bundle"],
  "generated_at_iso": "2026-03-17T12:00:00Z",
  "vertical_id": "founder_operator_core",
  "evidence_bundle": {
    "health_summary": "Warnings: 2. Open triage issues: 1.",
    "drift_signals": [],
    "repair_history_summary": "Latest review cycle: continue.",
    "support_triage_burden": "Open triage issues: 1. high",
    "operator_burden": "workflow-dataset release triage",
    "vertical_value_retention": "Guidance=continue Blockers=0 ...",
    "trust_review_posture": "Trust cockpit: ...",
    "production_scope_compliance": "In scope",
    "raw_snapshot": {
      "launch_recommended_decision": "launch_narrowly",
      "guidance": "continue",
      "blocker_count": 0,
      "warning_count": 2,
      "failed_gates_count": 0,
      "triage_open_issues": 1,
      "reliability_outcome": "pass"
    }
  },
  "stability_window": {
    "kind": "rolling_7",
    "start_iso": "2026-03-10T12:00:00Z",
    "end_iso": "2026-03-17T12:00:00Z",
    "label": "Last 7 days (rolling)"
  },
  "continue_rec": {
    "decision": "continue_with_watch",
    "rationale": "Continue operating; evidence is weak or warnings present—watch state.",
    "evidence_refs": ["evidence_bundle", "ongoing_summary"],
    "confidence": "low"
  }
}
```

## 5. Sample continue / narrow / repair / pause output

**Continue as-is:**
```
Decision: continue — Continue as-is
No blockers; continue as-is. Run regular review cycles.

Recommended actions:
  - Schedule next sustained deployment review (e.g. workflow-dataset stability-reviews generate).
  - Run production-runbook review-cycle and sustained-use checkpoint per runbook.
```

**Narrow:**
```
Decision: narrow — Narrow supported scope
High-severity issues open; narrow scope until triaged.

Recommended actions:
  - Restrict to current cohort/scope; do not add new users or expand until issues resolved.
  - Run workflow-dataset release triage; address high-severity issues.
  - Re-run stability-reviews generate after narrowing.
```

**Repair:**
```
Decision: repair — Run repair bundle
Blockers present; run repair bundle then re-review.

Recommended actions:
  - Execute repair: workflow-dataset launch-decision pack
  - Re-run production gates and post-deployment guidance after repair.
  - Run workflow-dataset stability-reviews generate to re-evaluate.
```

**Pause:**
```
Decision: pause — Pause deployment
Pause deployment until blockers resolved.

Recommended actions:
  - Do not promote or expand deployment until blockers resolved.
  - Resolve blockers; re-run launch-decision pack and stability-reviews generate.
  - Resume when: Resolve blockers and re-run stability-reviews generate.
```

**Rollback:**
```
Decision: rollback — Rollback to prior stable state
Release readiness blocked or guidance=needs_rollback.

Recommended actions:
  - Evaluate prior stable state (review_id or checkpoint); execute rollback per runbook.
  - Do not rely on this layer to execute rollback—operator decision required.
  - After rollback, run workflow-dataset stability-reviews generate.
```

## 6. Sample historical review output

```
Sustained deployment reviews  (last 3)
  2026-03-17T12:00:00Z  2026-03-17T12-00-00  decision=continue_with_watch
  2026-03-10T12:00:00Z  2026-03-10T12-00-00  decision=continue
  2026-03-03T12:00:00Z  2026-03-03T12-00-00  decision=repair
```

## 7. Exact tests run

```bash
python3 -m pytest tests/test_stability_reviews.py -v
```

**18 tests:** test_stability_window_to_dict, test_evidence_bundle_to_dict, test_continue_recommendation_to_dict, test_decision_pack_to_dict, test_build_decision_output_continue, test_build_decision_output_narrow, test_build_decision_output_repair, test_build_decision_output_pause, test_build_decision_output_rollback, test_decision_output_unknown_fallback, test_explain_stability_decision_with_pack, test_pack_generation_returns_pack, test_evidence_bundle_composition, test_no_review_weak_evidence_valid_decision, test_store_save_and_load_latest, test_list_reviews_newest_first, test_get_review_by_id, test_contradictory_evidence_handling.

## 8. Remaining gaps for later refinement

- **Prior stable ref for rollback:** RollbackRecommendation.prior_stable_ref is not yet populated from historical reviews or install/rollback checkpoints; operator must identify prior stable state manually.
- **Drift signals:** Currently only post-deployment degraded and sustained-use criteria; no dedicated drift-detection integration from Pane 1 (health/drift layer).
- **Repair bundle execution:** Repair recommendation points to launch-decision pack and workflow-dataset commands; no automated “run repair bundle” step.
- **Next scheduled review:** Computed as +7 days from review at save time; no calendar/ops_jobs integration for “next scheduled deployment review”.
- **Confidence calibration:** continue_with_watch vs continue is heuristic (weak evidence + warnings); could be tuned with explicit confidence thresholds.
- **Mission control:** stability_reviews slice is additive; no UI widget or dashboard panel yet.
- **Documentation:** No RST or user-facing runbook section yet; only this deliverable and the before-coding doc.
