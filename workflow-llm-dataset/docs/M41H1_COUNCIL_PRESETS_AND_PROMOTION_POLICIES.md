# M41H.1 — Council Presets + Promotion Policies (Deliverable)

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/council/models.py` | Added CouncilPreset, PromotionPolicyRule, PromotionPolicy; PRESET_* and DEFAULT_PRESET_ID. |
| `src/workflow_dataset/council/synthesis.py` | synthesize_decision(review, preset=..., policy_outcome_override=...); uses preset thresholds (min_score_to_promote, min_evidence_to_promote, reject_if_safety_below, quarantine_if_adaptation_risk_below, allow_limited_rollout, allow_safe_experimental_only); applies policy_outcome_override first for clearer quarantine/reject/limited/experimental_only. |
| `src/workflow_dataset/council/review.py` | run_council_review(..., preset_id=..., cohort_id=...); loads preset and effective policy, builds policy_context for adaptation subjects, calls apply_policy_outcome and synthesize_decision with preset and policy override. |
| `src/workflow_dataset/council/__init__.py` | Exported CouncilPreset, PromotionPolicy, PromotionPolicyRule, get_preset, list_presets, get_default_preset, get_effective_policy, apply_policy_outcome. |
| `src/workflow_dataset/cli.py` | council review: --preset, --cohort; added council presets (list | show --id), council policy (--cohort, --production-cut). |
| `tests/test_council.py` | Added test_list_presets, test_get_preset, test_get_default_preset, test_effective_policy, test_apply_policy_outcome, test_run_council_review_with_preset. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/council/presets.py` | Council preset registry: conservative_production, balanced_improvement, research_mode; get_preset(id), list_presets(), get_default_preset(). |
| `src/workflow_dataset/council/promotion_policy.py` | PromotionPolicy and rules; get_effective_policy(cohort_id, production_cut_id, repo_root); apply_policy_outcome(policy, context) for boundary-based override (trust_change->quarantine, high_risk->quarantine, affects_supported->limited_rollout, experimental_only->experimental_only). Optional load from data/local/council/policies/cohort_<id>.json. |
| `docs/M41H1_COUNCIL_PRESETS_AND_PROMOTION_POLICIES.md` | This deliverable. |

## 3. Sample council preset

```json
{
  "preset_id": "conservative_production",
  "label": "Conservative production",
  "description": "Strict thresholds for production; prefer quarantine over limited rollout when uncertain.",
  "min_score_to_promote": 0.75,
  "min_evidence_to_promote": 3,
  "required_perspectives_pass": ["safety_trust", "adaptation_risk"],
  "allow_limited_rollout": true,
  "allow_safe_experimental_only": true,
  "reject_if_safety_below": 0.5,
  "quarantine_if_adaptation_risk_below": 0.5,
  "quarantine_if_any_high_severity_disagreement": true,
  "needs_evidence_if_low_evidence": true
}
```

## 4. Sample promotion policy

```json
{
  "policy_id": "default",
  "label": "Default promotion policy",
  "cohort_id": "",
  "production_cut_id": "",
  "description": "Boundary-based rules: supported surface and trust changes trigger quarantine or limited rollout.",
  "rules": [
    {"rule_id": "trust_change", "condition": "changes_trust_posture", "outcome": "quarantine", "reason": "Changes trust posture; must be reviewed before promote."},
    {"rule_id": "high_risk_supported", "condition": "high_risk", "outcome": "quarantine", "reason": "High risk on supported surface; quarantine."},
    {"rule_id": "supported_surface", "condition": "affects_supported_surface", "outcome": "limited_rollout", "reason": "Affects supported surface; promote only in limited cohort until validated."},
    {"rule_id": "experimental_only", "condition": "affects_experimental_only", "outcome": "experimental_only", "reason": "Affects only experimental surfaces; safe for experimental_only scope."}
  ]
}
```

## 5. Exact tests run

```bash
python3 -m pytest tests/test_council.py -v
```

**14 passed** (8 existing + 6 M41H.1): test_list_presets, test_get_preset, test_get_default_preset, test_effective_policy, test_apply_policy_outcome, test_run_council_review_with_preset.

## 6. Next recommended step for the pane

- **Per-cohort policy files**: Add optional JSON under `data/local/council/policies/cohort_<cohort_id>.json` so operators can customize rules per cohort without code changes; get_effective_policy already attempts to load them.
- **Production-cut policy**: When production-cut is defined (Pane 1), add production_cut_id to get_effective_policy and a policy file pattern for production-cut (e.g. `production_cut_<id>.json`) so promotion rules can differ by cut.
- **Preset in stored review**: Optionally store preset_id (and policy_id) on CouncilReview so reports show which preset was used for a given review.
