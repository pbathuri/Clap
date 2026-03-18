# M39A–M39D Vertical Selection + Scope Lock + Surface Pruning

First-draft vertical narrowing layer: evidence-based vertical candidates, ranking, primary/secondary recommendation, scope lock (core / advanced_available / non_core), CLI, mission control, tests.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added **verticals_group**: `verticals candidates`, `verticals recommend`, `verticals show --id`, `verticals lock --id`, `verticals scope-report`. |
| `src/workflow_dataset/mission_control/state.py` | Added **vertical_selection_state**: recommended_primary_vertical_id/label, recommended_secondary_vertical_id/label, active_vertical_id, surfaces_hidden_by_scope_count, next_scope_review. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Vertical selection]** section: primary, secondary, active, surfaces_hidden_by_scope, next. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/vertical_selection/__init__.py` | Package exports. |
| `src/workflow_dataset/vertical_selection/models.py` | VerticalCandidate; SURFACE_CLASS_CORE, ADVANCED_AVAILABLE, NON_CORE. |
| `src/workflow_dataset/vertical_selection/candidates.py` | build_candidates() from vertical_packs + cohort/release evidence; get_candidate(). |
| `src/workflow_dataset/vertical_selection/selection.py` | rank_candidates(), recommend_primary_secondary(), explain_vertical(). |
| `src/workflow_dataset/vertical_selection/scope_lock.py` | get_core_surfaces(), get_optional_surfaces(), get_excluded_surfaces(), get_surface_class_for_vertical(), get_surfaces_hidden_by_scope(), get_scope_report(). |
| `src/workflow_dataset/vertical_selection/store.py` | get_active_vertical_id(), set_active_vertical_id(); data/local/vertical_selection/active_vertical.txt. |
| `docs/M39A_M39D_VERTICAL_SELECTION_BEFORE_CODING.md` | Before-coding analysis. |
| `tests/test_vertical_selection.py` | 11 tests: candidates, ranking, recommend, explain, scope lock, surface class, store, no-evidence fallback. |
| `docs/M39A_M39D_VERTICAL_SELECTION_AND_SCOPE_LOCK.md` | This document. |

---

## 3. Exact CLI usage

```bash
# List vertical candidates (ranked by evidence + readiness - burden)
workflow-dataset verticals candidates
workflow-dataset verticals candidates --json

# Recommend primary and optional secondary vertical
workflow-dataset verticals recommend
workflow-dataset verticals recommend --json

# Show one vertical (scores, core workflows, surfaces)
workflow-dataset verticals show --id founder_operator_core
workflow-dataset verticals show --id analyst_core --json

# Set active vertical (scope lock)
workflow-dataset verticals lock --id founder_operator_core

# Scope report: core / optional / hidden surfaces (default: active vertical)
workflow-dataset verticals scope-report
workflow-dataset verticals scope-report --id analyst_core --json
```

---

## 4. Sample vertical candidate

**founder_operator_core** (from curated pack):

| Field | Value |
|-------|--------|
| vertical_id | founder_operator_core |
| label | Founder / Operator (core) |
| description | Curated pack for founders and small-team operators: morning ops, weekly status, portfolio-first workday, supervised operator trust. |
| evidence_score | 0.0–1.0 (from cohort sessions/usefulness) |
| readiness_score | 0.2–1.0 (from release readiness status) |
| support_burden_score | 0.0–1.0 (from open triage issues) |
| core_workflow_ids | morning_ops, weekly_status_from_notes, weekly_status, morning_reporting |
| required_surface_ids | workspace_home, day_status, queue_summary, approvals_urgent, continuity_carry_forward |
| optional_surface_ids | mission_control, review_studio, automation_inbox, trust_cockpit |
| excluded_surface_ids | (from pack hidden_for_vertical) |
| strength_reason | Curated pack; readiness=…; sessions=… |
| weakness_reason | Support burden: N open issues. |

---

## 5. Sample recommendation output

**verticals recommend** (no cohort evidence):

```
Recommended verticals
  primary: founder_operator_core  Founder / Operator (core)
  reason: Curated pack; readiness=unknown; sessions=0.
  No cohort evidence yet; ranking uses readiness and burden.
```

With **--json**: `{ "primary": { "vertical_id", "label", ... }, "secondary": { ... }, "primary_reason", "ranked_ids", "no_evidence": true }`.

---

## 6. Sample scope-lock report

**verticals scope-report --id analyst_core**:

```
Scope report  vertical=analyst_core
  core: workspace_home, day_status, queue_summary, continuity_carry_forward
  optional: review_studio, mission_control, trust_cockpit
  hidden/non_core count: 12
```

**verticals scope-report** (using active vertical): same shape, vertical=active_vertical_id.

---

## 7. Exact tests run

```bash
python3 -m pytest tests/test_vertical_selection.py -v
```

**Result:** 11 passed:
- test_build_candidates_returns_list
- test_rank_candidates_returns_sorted
- test_recommend_primary_secondary
- test_explain_vertical
- test_explain_vertical_unknown
- test_scope_lock_core_surfaces
- test_surface_class_for_vertical
- test_scope_report
- test_store_get_set_vertical
- test_no_evidence_fallback
- test_get_candidate

---

## 8. Exact remaining gaps for later refinement

- **Per-vertical evidence**: Evidence today is global (cohort aggregate); could attach sessions/usefulness per workflow or per vertical (e.g. tag cohort reports by vertical) for finer ranking.
- **Trust/risk score**: trust_risk_score is placeholder (0.2); could integrate trust preset or authority-tier usage per vertical.
- **Enforcement of non-core**: Surfaces classified non-core are reported but not enforced (e.g. no CLI warning when using a non-core surface for active vertical); optional later: warn or soft-block.
- **Alignment with cohort**: Active cohort and active vertical are independent; could suggest “lock vertical X when cohort is Y” or sync with cohort apply.
- **Vertical-specific default experience**: default_experience profile is not yet switched by vertical lock; vertical_packs apply sets workday/experience — verticals lock only sets active_vertical and scope report; could add “verticals lock --id X --apply-defaults” that also applies the pack’s workday/experience.
