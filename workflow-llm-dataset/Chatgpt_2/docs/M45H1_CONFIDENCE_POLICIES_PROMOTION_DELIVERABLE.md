# M45H.1 — Confidence Policies + Limited Real-Run Promotion: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/shadow_execution/models.py` | Added `ConfidencePolicy`, `PromotionEligibilityReport`. |
| `src/workflow_dataset/shadow_execution/__init__.py` | Exported `ConfidencePolicy`, `PromotionEligibilityReport`, `get_policy_for_loop_type`, `evaluate_promotion_eligibility`, `build_promotion_eligibility_report`. |
| `src/workflow_dataset/cli.py` | Added `shadow-runs` group (if not present) with `list`, `show`, `confidence`, `gate-report`, `takeover`, `run`; added M45H.1 `policy-list`, `policy-show`, `promotion-report`. |
| `tests/test_shadow_execution.py` | Added tests: `test_get_policy_for_loop_type`, `test_evaluate_promotion_eligibility_shadow_only`, `test_evaluate_promotion_eligibility_eligible`, `test_build_promotion_eligibility_report_not_found`, `test_build_promotion_eligibility_report_success`. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/shadow_execution/policies.py` | `get_policy_for_loop_type(loop_type)`, `evaluate_promotion_eligibility(run_dict, policy)`, `build_promotion_eligibility_report(shadow_run_id, repo_root)`; built-in policies per loop type (routine, job, macro). |
| `src/workflow_dataset/shadow_execution/policy_store.py` | `load_policies(repo_root)`, `save_policies(policies, repo_root)` — optional overlay from `data/local/shadow_execution/policies.json`. |
| `docs/samples/M45H1_confidence_policy.json` | Sample confidence policy (default_job). |
| `docs/samples/M45H1_promotion_eligibility_report.json` | Sample promotion eligibility report (shadow-only with reasons). |
| `docs/M45H1_CONFIDENCE_POLICIES_PROMOTION_DELIVERABLE.md` | This deliverable. |

## 3. Sample confidence policy

See `docs/samples/M45H1_confidence_policy.json`. Fields:

- **policy_id**, **loop_type**, **label**
- **min_loop_confidence_for_bounded_real**: 0.75
- **max_risk_level_for_bounded_real**: "medium"
- **require_min_step_confidence**: 0.4
- **allow_high_risk**: false
- **operator_summary_shadow_only**: text shown when loop remains shadow-only
- **operator_summary_eligible**: text when eligible for bounded real

## 4. Sample promotion eligibility report

See `docs/samples/M45H1_promotion_eligibility_report.json`. Fields:

- **shadow_run_id**, **eligible_for_bounded_real**
- **reason_shadow_only**: list of reasons (e.g. loop confidence below minimum)
- **reason_eligible**: list when eligible (e.g. step confidences meet requirement, no high risk)
- **applied_policy_id**, **applied_policy_label**
- **operator_summary**: single operator-facing line
- **details**: loop_confidence, min_step_confidence, has_high_risk

## 5. Exact tests run

```bash
python3 -m pytest tests/test_shadow_execution.py -v
```

All **14** tests passed, including M45H.1:

- test_get_policy_for_loop_type
- test_evaluate_promotion_eligibility_shadow_only
- test_evaluate_promotion_eligibility_eligible
- test_build_promotion_eligibility_report_not_found
- test_build_promotion_eligibility_report_success

## 6. Next recommended step for the pane

- **Policy overlay**: Allow operators to add or edit policies in `data/local/shadow_execution/policies.json` (e.g. stricter routine policy, relaxed job policy) and have `policy-list` / `policy-show` and promotion evaluation use the overlay.
- **Promotion flow**: Add an explicit “promote to bounded real” step that (1) requires promotion-report eligible, (2) still goes through existing approval/trust, (3) creates or schedules a real run with the same plan_ref and records that it was promoted from a shadow run.
- **Mission control**: Surface “recent eligible for promotion” shadow run and “next policy to review” (e.g. loop type with most shadow-only runs) in the shadow_execution_state block.
