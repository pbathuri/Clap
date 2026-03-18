# M38I–M38L — Safe Real-User Adaptation + Boundary Manager (Deliverable)

First-draft safe adaptation layer: learn from real-user evidence, propose adaptations without silent drift, enforce supported/experimental boundaries, reject or quarantine risky adaptations, keep cohort profiles stable.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added **adaptation_group**: `adaptation candidates`, `adaptation show --id`, `adaptation boundary-check --id`, `adaptation apply --id`, `adaptation quarantine --id`, `adaptation accept`, `adaptation reject`. |
| `src/workflow_dataset/mission_control/state.py` | Added **adaptation_state**: safe_to_review_candidates_count, quarantined_count, supported_surface_deltas_pending_count, recent_accepted/rejected counts, next_recommended_adaptation_review_id, quarantined_sample_ids. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Safe adaptation]** section: safe_to_review, quarantined, supported_deltas_pending, recent_accepted/rejected, next_review command, quarantined_sample. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/safe_adaptation/__init__.py` | Package exports. |
| `src/workflow_dataset/safe_adaptation/models.py` | AdaptationCandidate, AdaptationEvidenceBundle, CohortBoundaryCheck, ReviewDecision, QuarantineState, SupportedSurfaceAdaptation, ExperimentalSurfaceAdaptation, BlockedAdaptation. |
| `src/workflow_dataset/safe_adaptation/store.py` | save_candidate, load_candidate, list_candidates, update_review_status, list_quarantined, append_quarantine, append_decision, list_recent_decisions. |
| `src/workflow_dataset/safe_adaptation/boundary.py` | evaluate_boundary_check, classify_adaptation, affects_supported_surface, affects_experimental_surface, affects_blocked_surface, safe_for_cohort, must_quarantine, changes_trust_posture, experimental_only. |
| `src/workflow_dataset/safe_adaptation/evidence_bundle.py` | build_evidence_bundle, build_bundle_from_session_feedback (from triage evidence + corrections). |
| `src/workflow_dataset/safe_adaptation/review.py` | inspect_candidate, accept_candidate, reject_candidate, quarantine_candidate, apply_within_boundaries, record_rationale_and_delta. |
| `src/workflow_dataset/safe_adaptation/candidates.py` | create_candidate (create and persist candidate from cohort, surfaces, target, evidence). |
| `docs/M38I_M38L_SAFE_ADAPTATION_BEFORE_CODING.md` | Before-coding: existing/missing, file plan, safety, principles, what this block will NOT do. |
| `docs/M38I_M38L_SAFE_ADAPTATION_DELIVERABLE.md` | This deliverable. |
| `tests/test_safe_adaptation.py` | Tests: candidate creation, boundary check, quarantine, accept/reject/apply, supported vs experimental, low-evidence handling. |

---

## 3. Exact CLI usage

```bash
# List adaptation candidates (optional filters)
workflow-dataset adaptation candidates [--repo PATH] [--cohort ID] [--status pending|accepted|rejected|quarantined] [--limit N] [--json]

# Show one candidate
workflow-dataset adaptation show --id ADAPT_ID [--repo PATH] [--json]

# Run boundary check for a candidate
workflow-dataset adaptation boundary-check --id ADAPT_ID [--cohort ID] [--repo PATH] [--json]

# Accept candidate (must pass boundary check)
workflow-dataset adaptation accept --id ADAPT_ID [--rationale TEXT] [--delta TEXT] [--repo PATH] [--json]

# Reject candidate
workflow-dataset adaptation reject --id ADAPT_ID [--rationale TEXT] [--repo PATH] [--json]

# Quarantine candidate
workflow-dataset adaptation quarantine --id ADAPT_ID [--reason TEXT] [--notes TEXT] [--repo PATH] [--json]

# Apply accepted candidate within boundaries
workflow-dataset adaptation apply --id ADAPT_ID [--delta TEXT] [--repo PATH] [--json]
```

---

## 4. Sample adaptation candidate

Created via `create_candidate()` (or in tests); stored under `data/local/safe_adaptation/candidates/<adaptation_id>.json`:

```json
{
  "adaptation_id": "adapt_abc123def456",
  "cohort_id": "careful_first_user",
  "affected_surface_ids": ["workspace_home", "queue_summary"],
  "surface_type": "supported",
  "target_type": "output_style",
  "target_id": "prefer_bullets",
  "before_value": "paragraphs",
  "after_value": "bullets",
  "evidence": {
    "evidence_ids": ["ev_1", "ev_2"],
    "correction_ids": [],
    "session_ids": [],
    "summary": "2 evidence; 0 corrections",
    "evidence_count": 2
  },
  "risk_level": "low",
  "review_status": "pending",
  "created_at_utc": "2025-03-16T12:00:00.000000+00:00",
  "updated_at_utc": "2025-03-16T12:00:00.000000+00:00",
  "summary": "Prefer bullet output on workspace_home"
}
```

---

## 5. Sample boundary-check output

```bash
workflow-dataset adaptation boundary-check --id adapt_abc123def456
```

Human-readable:

```
Boundary check  candidate=adapt_abc123def456  cohort=careful_first_user
  safe_for_cohort=True  must_quarantine=False  experimental_only=False
  affects_supported=True  affects_experimental=False  affects_blocked=False
  changes_trust_posture=False
  reasons: ['supported_surface_ok_with_review']
  allowed_surfaces=['workspace_home', 'queue_summary']  blocked_surfaces=[]
```

With `--json`: full `CohortBoundaryCheck` dict.

---

## 6. Sample quarantine / apply flow

**Quarantine:**

```bash
workflow-dataset adaptation quarantine --id adapt_xyz --reason "low_evidence_supported_surface" --notes "Single session; need more evidence"
# Quarantined adapt_xyz  reason=low_evidence_supported_surface
```

**Accept then apply:**

```bash
workflow-dataset adaptation boundary-check --id adapt_abc123def456
workflow-dataset adaptation accept --id adapt_abc123def456 --rationale "Approved for pilot"
workflow-dataset adaptation apply --id adapt_abc123def456 --delta "Applied bullets on workspace_home and queue_summary"
# Applied adapt_abc123def456  delta=Applied bullets...
```

---

## 7. Exact tests run

```bash
python3 -m pytest tests/test_safe_adaptation.py -v
```

Covers: adaptation candidate creation, boundary check (supported surface, experimental only), quarantine behavior, accept/reject flow, apply within boundaries (only accepted), inspect candidate, low-evidence quarantine, supported vs experimental enforcement.

---

## 8. Remaining gaps for later refinement

- **Apply implementation**: `apply_within_boundaries` records the decision and behavior delta but does not yet mutate pack defaults, corrections, or personal_adaptation store; wire to existing apply surfaces in a follow-up.
- **Candidate generation from triage/corrections**: `create_candidate` is manual; a pipeline that builds candidates from triage evidence + corrections (e.g. propose_updates) and writes to safe_adaptation store is not implemented.
- **Mission control “next recommended”**: Heuristic is “first pending candidate”; could be driven by supported-surface delta priority or evidence strength.
- **Quarantine review-by date**: QuarantineState has `review_recommended_by_utc` but no CLI to set it or mission-control reminder.
- **Trust-related target types**: TRUST_RELATED_TARGET_TYPES in boundary.py is a fixed set; could be configurable or derived from trust module.
