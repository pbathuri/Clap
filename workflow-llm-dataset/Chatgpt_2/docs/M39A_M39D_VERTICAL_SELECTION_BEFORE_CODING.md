# M39A–M39D Vertical Selection + Scope Lock — Before Coding

## 1. What supported-surface and cohort-evidence structures already exist

- **Cohort**: CohortProfile (cohort_id, surface_support map, allowed_trust/workday/automation), surface_matrix (get_matrix(cohort_id) → supported|experimental|blocked), cohort health (open issues, severity, recommended_downgrade). Active cohort in data/local/cohort/active_profile.txt.
- **Cohort evidence**: release/dashboard_data aggregates cohort from pilot (cohort_*_report.json, aggregate_report.json): sessions_count, avg_usefulness, recommendation/graduation. Triage: list_issues(cohort_id), list_evidence(cohort_id), supportability (supported_surface_involved).
- **Vertical packs (M39E–M39H)**: CuratedVerticalPack (pack_id, required_surfaces.required_surface_ids, optional_surface_ids, hidden_for_vertical, core_workflow_path.workflow_ids). Pack ids: founder_operator_core, analyst_core, developer_core, document_worker_core. Mission control has vertical_packs_state (active pack, milestones, blocked step).
- **Release readiness**: build_release_readiness(), status ready|blocked|degraded. No per-vertical readiness.
- **Default experience**: Surface classification (default_visible, advanced, expert); no “core for vertical X” or “non-core for vertical X”.

## 2. What is missing for real vertical selection and scope locking

- **Vertical candidate model**: A single type that represents a near-term product vertical with evidence_score, readiness_score, support_burden_score, trust_risk_score, core_workflow_ids, required/optional/excluded surfaces. Today vertical_packs define packs but not “candidates” ranked by evidence.
- **Evidence-based ranking**: No aggregation that scores verticals from cohort evidence (sessions, usefulness, workflow tags) and readiness/triage. Need a first-draft scorer that consumes dashboard cohort + triage and outputs per-vertical scores (or defaults when no evidence).
- **Primary/secondary recommendation**: No “recommended primary vertical” and “recommended secondary vertical” from ranked candidates; no explanation of why strong/weak.
- **Scope lock**: No “active vertical” that locks which surfaces are core vs advanced-but-available vs non-core for the product. vertical_packs have required_surfaces per pack but no global “scope lock” and no persistence of “active vertical” for mission control.
- **Surface pruning labels**: No “core surface”, “advanced-but-available”, “non-core” or “not recommended for this vertical” that combines cohort + vertical. Default experience has default_visible/advanced/expert (UX); cohort has supported/experimental/blocked (supportability). Missing: vertical-scope classification for narrowing.
- **CLI and mission control**: No `verticals candidates`, `verticals recommend`, `verticals show`, `verticals lock`, `verticals scope-report`; no mission-control block for recommended primary/secondary vertical, active vertical, surfaces hidden by scope.

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|--------|
| Create | `src/workflow_dataset/vertical_selection/__init__.py` | Exports |
| Create | `src/workflow_dataset/vertical_selection/models.py` | VerticalCandidate; SURFACE_CLASS_CORE, ADVANCED_AVAILABLE, NON_CORE; core_workflow_ids, required/optional/excluded surfaces, scores |
| Create | `src/workflow_dataset/vertical_selection/candidates.py` | Build candidates from vertical_packs + cohort/evidence; evidence_score from dashboard_data cohort + triage; readiness_score from release_readiness; support_burden from open issues on supported surfaces |
| Create | `src/workflow_dataset/vertical_selection/selection.py` | rank_candidates(), recommend_primary_secondary(), explain_vertical() |
| Create | `src/workflow_dataset/vertical_selection/scope_lock.py` | get_core_surfaces(vertical_id), get_non_core_surfaces(vertical_id), get_scope_report(vertical_id), get_surface_class_for_vertical(surface_id, vertical_id) |
| Create | `src/workflow_dataset/vertical_selection/store.py` | get_active_vertical_id(), set_active_vertical_id(); data/local/vertical_selection/active_vertical.txt |
| Modify | `src/workflow_dataset/cli.py` | verticals_group: verticals candidates, recommend, show --id, lock --id, scope-report |
| Modify | `src/workflow_dataset/mission_control/state.py` | vertical_selection_state: recommended_primary, recommended_secondary, active_vertical_id, surfaces_hidden_by_scope_count, next_scope_review |
| Modify | `src/workflow_dataset/mission_control/report.py` | [Vertical selection] section |
| Create | `tests/test_vertical_selection.py` | Candidate model, ranking, scope lock, surface class, no-evidence fallback |
| Create | `docs/M39A_M39D_VERTICAL_SELECTION_AND_SCOPE_LOCK.md` | Files, CLI, samples, tests, gaps |

## 4. Safety/risk note

- **No silent hiding of safety**: Review, trust, and approval surfaces remain accessible; “non-core” or “hidden by scope” means “not in the primary supported flow for this vertical,” not “removed from product.” Mission control and cohort health continue to show full state.
- **Evidence-based**: When no cohort evidence exists, ranking uses defaults (e.g. readiness + support burden only) and does not invent fake evidence. “Recommend” is advisory; lock is explicit user/operator choice.
- **Scope lock is additive**: Locking a vertical sets active_vertical and narrows default surfaces; it does not delete or disable subsystems. Unlock = clear active vertical or set to empty.

## 5. Vertical-selection principles

- **Evidence first**: Prefer verticals with real cohort evidence (sessions, usefulness, workflows). When evidence is thin, use readiness and support burden to rank.
- **1–2 verticals**: Recommend one primary and optionally one secondary to keep product shape sharp.
- **Core vs non-core**: For a chosen vertical, define core surfaces (required for that vertical), advanced-but-available (optional), non-core (excluded or not recommended for this vertical). Align with vertical_packs required_surfaces where possible.
- **Explain**: Every recommendation explains why (evidence, readiness, burden). Weak or no-evidence cases get explicit fallback messaging.

## 6. What this block will NOT do

- Will not delete or disable major subsystems; only classify and narrow default/scope.
- Will not invent verticals with no basis; candidates are derived from vertical_packs and cohort/workflow alignment.
- Will not hide critical review/trust/approval state from mission control or operators.
- Will not rebuild vertical_packs or cohort; only consume and add a selection/scope layer on top.
