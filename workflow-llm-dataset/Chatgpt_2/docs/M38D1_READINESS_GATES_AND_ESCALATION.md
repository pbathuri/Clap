# M38D.1 — Readiness Gates + Cohort Escalation Paths

Extends M38 cohort layer with: readiness gates per cohort, explicit escalation/downgrade paths, and recommended transition from current state.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cohort/models.py` | ReadinessGate, CohortTransition; gate sources and transition triggers (existing). |
| `src/workflow_dataset/cohort/__init__.py` | Exports gates and transitions (existing). |
| `src/workflow_dataset/cli.py` | Added `cohort gates --id <cohort>` (list and evaluate gates), `cohort transitions [--id] [--direction escalation\|downgrade]`, `cohort recommend [--id]` (suggest transition from current state). |
| `src/workflow_dataset/mission_control/state.py` | cohort_state: added `gates_summary` (e.g. "3/4 pass"), `recommended_transition` (direction, suggested_cohort_id, reason) when get_recommended_transition returns a result. |
| `src/workflow_dataset/mission_control/report.py` | [Cohort]: added gates line and recommend line when recommended_transition is set. |
| `tests/test_cohort.py` | Tests for get_gates_for_cohort, evaluate_gates, get_transitions_for_cohort, get_recommended_transition (existing). |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/cohort/gates.py` | BUILTIN_GATES (release_not_blocked, no_critical_triage, no_downgrade_recommended, reliability_pass_or_na); get_gates_for_cohort(), evaluate_gates(cohort_id, repo_root). |
| `src/workflow_dataset/cohort/transitions.py` | BUILTIN_TRANSITIONS (downgrade to careful_first_user on triage/reliability; escalation careful->bounded, careful->document, bounded->developer; manual->internal_demo); get_transitions_for_cohort(), get_recommended_transition(). |
| `docs/M38D1_READINESS_GATES_AND_ESCALATION.md` | This document. |

## 3. Sample readiness gate

**release_not_blocked**

- **gate_id**: `release_not_blocked`
- **label**: Release not blocked
- **description**: Release readiness status is not blocked.
- **check_source**: `release_readiness`
- **required_value**: `ready_or_degraded`
- **Applies to**: Any cohort with `required_readiness` not `any` (e.g. careful_first_user, bounded_operator_pilot).

Evaluation: runs `build_release_readiness(repo_root)`; **passed** if `status != blocked`.

CLI: `workflow-dataset cohort gates --id careful_first_user` (evaluates and shows pass/fail); `workflow-dataset cohort gates --id careful_first_user --json`

## 4. Sample escalation/downgrade path

**Downgrade (triage recommends downgrade)**

- **from**: `*` (any cohort)
- **to**: `careful_first_user`
- **direction**: `downgrade`
- **trigger**: `triage_recommend_downgrade`
- **criteria_hint**: "Triage cohort health recommends downgrade (critical issue or should_downgrade)."

**Escalation (readiness met)**

- **from**: `careful_first_user`
- **to**: `bounded_operator_pilot`
- **direction**: `escalation`
- **trigger**: `readiness_met`
- **criteria_hint**: "All readiness gates pass; no downgrade recommended; release not blocked."

CLI: `workflow-dataset cohort transitions`, `workflow-dataset cohort transitions --id careful_first_user --direction escalation`, `workflow-dataset cohort recommend --id careful_first_user`

## 5. Exact tests run

```bash
python3 -m pytest workflow-llm-dataset/tests/test_cohort.py -v
```

**Result:** 15 passed (existing 11 + test_get_gates_for_cohort, test_evaluate_gates_returns_list, test_get_transitions_for_cohort, test_get_recommended_transition_returns_dict_or_none).

## 6. Next recommended step for the pane

- **Apply on recommend**: Add `workflow-dataset cohort recommend --apply` (or `--yes`) that, when a transition is recommended, runs `cohort apply --id <suggested_cohort_id>` so one command can suggest and apply the transition.
- **Gate source trust**: Add a readiness gate that checks trust posture (e.g. active authority tier within cohort’s allowed_trust_tier_ids) and wire it into evaluate_gates so trust drift can contribute to downgrade recommendation.
- **Cohort state in mission control**: Already added: gates_summary and recommended_transition in cohort_state and [Cohort] report section.
