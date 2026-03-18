# M47I–M47L — Quality Signals + Delightful Operator Guidance: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `quality-signals` command; added `guidance` typer with `next-action`, `explain`, `ambiguity-report` commands. |
| `src/workflow_dataset/mission_control/state.py` | Added `quality_guidance` slice: strongest_ready_to_act_item, strongest_ready_rationale, most_ambiguous_current_guidance, best_recovered_blocked_state, weakest_guidance_surface, next_recommended_guidance_improvement; local_sources["quality_guidance"]. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M47I_M47L_QUALITY_SIGNALS_GUIDANCE_BEFORE_CODING.md` | Before-coding: existing guidance, gaps, file plan, safety, principles, what we will not do. |
| `src/workflow_dataset/quality_guidance/__init__.py` | Package exports. |
| `src/workflow_dataset/quality_guidance/models.py` | QualitySignal, ClarityScore, ConfidenceWithEvidence, AmbiguityWarning, ReadyToActSignal, NeedsReviewSignal, StrongNextStepSignal, WeakGuidanceWarning, GuidanceItem, GuidanceKind. |
| `src/workflow_dataset/quality_guidance/signals.py` | build_quality_signals(): aggregates from mission_control next_action, development/product state (review needed), executor (blocked recovery), supervised_loop (resume), progress recovery; returns next_action_signal, review_needed_signal, blocked_recovery_signal, resume_signal, ambiguity_warnings, weak_guidance_warnings, strongest_ready_to_act, most_ambiguous. |
| `src/workflow_dataset/quality_guidance/guidance.py` | next_best_action_guidance(), review_needed_guidance(), blocked_state_guidance(), resume_guidance(), operator_routine_guidance(), support_recovery_guidance(); each returns GuidanceItem with quality_signal. |
| `src/workflow_dataset/quality_guidance/surfaces.py` | ready_now_states(), not_safe_yet_states(), ambiguity_report(), weak_guidance_report(), next_recommended_guidance_improvement(). |
| `src/workflow_dataset/quality_guidance/store.py` | save_latest_guidance(), get_guidance_by_id(), list_latest_guide_ids(); data/local/quality_guidance/latest_guidance.json. |
| `tests/test_quality_guidance.py` | 17 tests: model to_dict, build_quality_signals structure, ambiguity/weak report structure, ready_now/not_safe_yet, next_best_action/blocked/resume guidance, store save/get, low-evidence weak warning. |
| `docs/M47I_M47L_QUALITY_SIGNALS_GUIDANCE_DELIVERABLE.md` | This file. |

## 3. Exact CLI usage

```bash
# Quality signals summary
workflow-dataset quality-signals [--repo-root PATH] [--json]

# Next best action with quality signal
workflow-dataset guidance next-action [--repo-root PATH] [--json]

# Explain a guidance item by id (from latest set)
workflow-dataset guidance explain <guide_id> [--repo-root PATH] [--json]

# Ambiguity report
workflow-dataset guidance ambiguity-report [--repo-root PATH] [--json]
```

## 4. Sample quality-signal output (JSON shape)

```json
{
  "next_action_signal": {
    "clarity": {"score": 0.4, "reason": "No urgent signal; recommendation is generic.", "evidence_refs": ["mission_control_next_action"]},
    "confidence": {"level": "low", "evidence_refs": ["mission_control"], "disclaimer": "No strong evidence; review state and choose."},
    "weak_guidance_warnings": [{"message": "Next action is hold with no urgent signal.", "improvement_hint": "Run mission-control and act on a specific subsystem.", "source": "next_action"}],
    "strong_next_step": {"step_label": "hold", "rationale": "No urgent signal; review mission-control state and choose next step.", "evidence_refs": ["mission_control_next_action"], "command_or_ref": "Consider: planner recommend-next, ..."}
  },
  "ambiguity_warnings": [],
  "weak_guidance_warnings": [...],
  "strongest_ready_to_act": null,
  "most_ambiguous": null
}
```

## 5. Sample ambiguity report

```json
{
  "ambiguity_count": 1,
  "most_ambiguous": {
    "message": "Could not compute next action: ...",
    "suggested_clarification": "Run workflow-dataset mission-control for full state.",
    "source": "next_action"
  },
  "warnings": [...],
  "summary": "1 ambiguity warning(s). Top: Could not compute next action..."
}
```

## 6. Sample ready-to-act guidance output

```
Next: build
Pending patch proposals need operator review; apply or reject.
  Confidence: high
  Action: Pending: 2. Use devlab show-proposal and review-proposal.
```

When hold (weak):
```
Next: hold
No urgent signal; review mission-control state and choose next step.
  Confidence: low
  Evidence is weak; recommendations are generic.
  Action: Consider: planner recommend-next, incubator list, or eval board.
```

## 7. Exact tests run

```bash
python3 -m pytest tests/test_quality_guidance.py -v
```

**17 tests:** test_clarity_score_to_dict, test_confidence_with_evidence_to_dict, test_ambiguity_warning_to_dict, test_ready_to_act_signal_to_dict, test_quality_signal_to_dict, test_guidance_item_to_dict, test_build_quality_signals_returns_dict, test_ambiguity_report_structure, test_weak_guidance_report_structure, test_ready_now_states_returns_list, test_not_safe_yet_states_returns_list, test_next_recommended_guidance_improvement_returns_dict, test_next_best_action_guidance_returns_item_or_none, test_blocked_state_guidance_may_return_none, test_resume_guidance_may_return_none, test_store_save_and_get_by_id, test_low_evidence_next_action_has_weak_warning.

Note: Tests that call `build_quality_signals(root)` or mission_control state with the real repo may take longer (mission_control loads many subsystems). Unit tests (models, to_dict, report structure) complete quickly.

## 8. Exact remaining gaps for later refinement

- **Conversational ask integration**: Wire quality_guidance next_best_action and ambiguity into conversational answer_what_next so the chat surface shows clarity/confidence and suggested clarification when ambiguous.
- **Review studio / queue**: Surface “needs review” and “ready to act” in review_studio or unified_queue UI so operators see one place for “do this next.”
- **Vertical-scoped copy**: support_recovery_guidance uses vertical playbook when blocked; operator_routine_guidance could be tightened per vertical (e.g. founder_operator_core routine steps).
- **Confidence calibration**: Confidence level (low/medium/high) is heuristic from signal source; could be driven by explicit evidence counts or thresholds.
- **Persistence of “explain” ids**: guide_id is generated at guidance build time; explain --id looks up from latest_guidance.json. If user never ran guidance next-action or explain, list_latest_guide_ids may be empty; consider generating latest set on quality-signals or mission_control build.
- **Mission control report**: format_mission_control_report does not yet include a quality_guidance subsection; could add a short “Quality & guidance” block with strongest ready-to-act and next improvement.
