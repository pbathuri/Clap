# M38I–M38L — Safe Real-User Adaptation + Boundary Manager (Before Coding)

## 1. What adaptation/preference/review behavior already exists

- **personal/preference_model.py**: `PreferenceRecord` (key, value, source=teaching|inferred); get/set_preference are stubs.
- **personal/style_profiles, style_suggestion_engine, imitation_candidates**: Style patterns, style-aware suggestions (pending|accepted|dismissed); no cohort/surface boundary.
- **corrections**: `CorrectionEvent`, `propose_updates` → `ProposedUpdate` (target_type, target_id, before/after, risk_level); LEARNING_RULES; no cohort or supported-surface gating.
- **teaching**: `Skill` (draft|accepted|rejected), skill_store; no link to cohort or surface matrix.
- **personal_adaptation (M31I–M31L)**: PreferenceCandidate, StylePatternCandidate, AcceptedPreferenceUpdate; generate_preference_candidates, apply_accepted_preference, explain_preference; CLI `personal` group; mission_control personal_adaptation block. **Scope:** per-user preference/style; no cohort or supported/experimental surface enforcement.
- **cohort (Pane 1)**: `CohortProfile`, `surface_support` (supported|experimental|blocked), `surface_matrix`, get_supported_surfaces, get_experimental_surfaces, get_blocked_surfaces; gates, transitions; store (active_cohort_id).
- **triage (Pane 2)**: `CohortEvidenceItem`, `UserObservedIssue`, list_evidence, list_issues, build_cohort_health_summary, supportability (supported_surface_involved, experimental_surface_involved).
- **trust**: scope, contracts, tiers; no adaptation-specific gating.

**Summary:** Preference/style and correction-proposal flows exist; cohort profiles and supported-surface matrix exist; triage evidence exists. **Missing:** a single layer that (1) turns real-user evidence into **adaptation candidates** scoped by cohort and surface, (2) **evaluates** them against supported/experimental/blocked and trust boundaries, (3) **quarantines** or blocks risky ones, (4) **applies** only within allowed boundaries and records rationale/delta.

---

## 2. What is missing for a real cohort-safe adaptation layer

- **Explicit models**: Adaptation candidate (id, cohort_id, affected_surface_ids, surface_type supported|experimental, evidence_refs, risk, review_status); supported-surface adaptation vs experimental-surface adaptation vs blocked adaptation; quarantine state; cohort boundary check result; adaptation evidence bundle; review decision (accept/reject/quarantine) with rationale and behavior delta.
- **Boundary-aware evaluation**: Whether candidate affects supported surfaces; whether safe for current cohort; whether it changes trust/authority posture; whether it should remain experimental only; whether it must be quarantined for broader review.
- **Review/application flow**: Inspect candidate, review evidence, accept/reject/quarantine; apply only within allowed cohort/surface boundaries; record rationale and resulting behavior delta.
- **CLI**: `adaptation candidates`, `adaptation show --id`, `adaptation boundary-check --id`, `adaptation apply --id`, `adaptation quarantine --id`.
- **Mission control**: Safe-to-review adaptation candidates count, quarantined count, supported-surface deltas pending review, recent accepted/rejected, next recommended adaptation review.

---

## 3. Exact file plan

| Area | Action | Path |
|------|--------|------|
| Models | Create | `src/workflow_dataset/safe_adaptation/models.py` — AdaptationCandidate, SupportedSurfaceAdaptation, ExperimentalSurfaceAdaptation, BlockedAdaptation, QuarantineState, CohortBoundaryCheck, AdaptationEvidenceBundle, ReviewDecision |
| Boundary | Create | `src/workflow_dataset/safe_adaptation/boundary.py` — evaluate_boundary_check, affects_supported_surface, safe_for_cohort, changes_trust_posture, experimental_only, must_quarantine |
| Store | Create | `src/workflow_dataset/safe_adaptation/store.py` — save_candidate, list_candidates, load_candidate, update_review_status, list_quarantined, list_recent_decisions |
| Review/apply | Create | `src/workflow_dataset/safe_adaptation/review.py` — inspect_candidate, accept/reject/quarantine, apply_within_boundaries, record_rationale_and_delta |
| Evidence | Create | `src/workflow_dataset/safe_adaptation/evidence_bundle.py` — build_evidence_bundle (from triage evidence + optional corrections) |
| Init | Create | `src/workflow_dataset/safe_adaptation/__init__.py` |
| CLI | Modify | `src/workflow_dataset/cli.py` — adaptation group: candidates, show, boundary-check, apply, quarantine |
| Mission control state | Modify | `src/workflow_dataset/mission_control/state.py` — adaptation_state block |
| Mission control report | Modify | `src/workflow_dataset/mission_control/report.py` — [Safe adaptation] section |
| Tests | Create | `tests/test_safe_adaptation.py` |
| Docs | Create | `docs/M38I_M38L_SAFE_ADAPTATION_DELIVERABLE.md` |

---

## 4. Safety/risk note

- **No silent broadening:** Boundary check uses cohort surface matrix; supported scope is not expanded without explicit review.
- **No trust bypass:** Adaptations that change trust/authority posture are quarantined or rejected; apply does not modify trust tiers or approval registry.
- **Quarantine visible:** Quarantined and blocked candidates are listed and visible in CLI and mission control; nothing hidden.
- **Explicit and reviewable:** All candidates have evidence refs and review decisions with rationale; behavior delta recorded on apply.

---

## 5. Adaptation boundary principles

1. **Supported-surface adaptations** may be applied only for surfaces in the cohort’s supported list; they require explicit review and stay within that list.
2. **Experimental-surface adaptations** are allowed only where the cohort has that surface as experimental; no automatic promotion of a surface from experimental to supported by this layer.
3. **Trust/authority changes** (e.g. new trusted routine, broader approval scope) force quarantine or reject; no silent elevation.
4. **Low evidence or high risk** (e.g. single session, critical surface) → quarantine pending broader review.
5. **Cohort profile remains stable:** This layer does not change the cohort’s surface_support map; it only allows applying behavior changes within existing boundaries.

---

## 6. What this block will NOT do

- **No** hidden continual self-modification or silent product drift.
- **No** silent expansion of supported scope; no opaque model tuning loops.
- **No** bypass of trust/review boundaries.
- **No** rebuild of personal, observe, teaching, corrections, packs; integration via existing cohort, triage, corrections.
- **No** automatic application of unreviewed or quarantined candidates.
