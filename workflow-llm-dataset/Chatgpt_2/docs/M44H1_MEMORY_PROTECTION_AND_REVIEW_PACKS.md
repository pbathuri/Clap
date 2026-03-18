# M44H.1 — Memory Protection Rules + Review Packs (Deliverable)

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/memory_curation/models.py` | Added `operator_explanation` to CompressionCandidate, ForgettingCandidate, ReviewRequiredDeletionCandidate; added `policy_id` to ArchivalState; added MemoryProtectionRule, ReviewPackItem, ReviewPack, ArchivalPolicyCuration. |
| `src/workflow_dataset/memory_curation/store.py` | Load/save now include new fields; added load/save for protection_rules, review_packs, archival_policies. |
| `src/workflow_dataset/memory_curation/forgetting.py` | When generating candidates, sets `operator_explanation` via build_forgettable_explanation and build_review_required_explanation. |
| `src/workflow_dataset/memory_curation/__init__.py` | Exported MemoryProtectionRule, ReviewPack, ReviewPackItem, ArchivalPolicyCuration. |
| `src/workflow_dataset/cli.py` | Added memory-curation protection-rules, review-packs, review-pack-approve, archival-policies. |
| `tests/test_memory_curation.py` | Added tests for protection rules, match/explain, explanations, review pack create/list/get, archival policies, store round-trip for protection rules. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/memory_curation/protection_rules.py` | get_default_protection_rules(), match_unit_against_rules(), explain_why_protected(). |
| `src/workflow_dataset/memory_curation/explanations.py` | build_forgettable_explanation(), build_compressible_explanation(), build_review_required_explanation(). |
| `src/workflow_dataset/memory_curation/review_packs.py` | create_review_pack(), get_review_pack(), list_review_packs(), record_review_decision(). |
| `src/workflow_dataset/memory_curation/archival_policies.py` | get_default_archival_policies(), get_archival_policy_by_id(), ensure_archival_policies_saved(). |
| `docs/M44H1_MEMORY_PROTECTION_AND_REVIEW_PACKS.md` | This deliverable. |

## 3. Sample memory protection rule

```json
{
  "rule_id": "corrections",
  "label": "Correction-linked memory",
  "match_source": "corrections",
  "match_tags": [],
  "match_source_ref_pattern": "",
  "protection_reason": "This memory is linked to user corrections; it is protected from automatic forgetting so that correction context is preserved.",
  "created_at_utc": "",
  "active": true
}
```

**Operator-facing explanation** when a unit matches:  
*"This memory is linked to user corrections; it is protected from automatic forgetting so that correction context is preserved."*

## 4. Sample review pack

```json
{
  "pack_id": "pack_abc123",
  "label": "Review pack pack_abc123",
  "items": [
    {
      "item_id": "rpi_xyz",
      "kind": "forgetting",
      "candidate_id": "forget_xyz",
      "unit_ids": ["s1_2024-01-01T12:00:00Z"],
      "reason": "policy_medium_term",
      "operator_explanation": "Medium-term working memory past retention (e.g. 30 days); review recommended before forgetting.",
      "approved": null
    },
    {
      "item_id": "rpi_comp1",
      "kind": "compression",
      "candidate_id": "comp_session_1",
      "unit_ids": ["u1", "u2", "u3"],
      "reason": "session_history",
      "operator_explanation": "Session history rollup; many units from one session become one summary. (3 units would become one summary.)",
      "approved": null
    }
  ],
  "created_at_utc": "2025-03-16T14:00:00+00:00",
  "reviewed_at_utc": "",
  "status": "pending"
}
```

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_memory_curation.py -v
```

**Result:** 30 passed (21 existing + 9 M44H.1).

New tests:

- `test_protection_rules_default`
- `test_match_unit_against_rules_corrections`
- `test_explain_why_protected`
- `test_explanations_forgettable`
- `test_explanations_compressible`
- `test_review_pack_create_empty`
- `test_review_pack_create_with_pending`
- `test_archival_policies_default`
- `test_store_protection_rules_roundtrip`

## 6. Next recommended step for the pane

- **Wire protection rules into forgetting/compression flows**  
  Before generating forgetting candidates, check each unit against `match_unit_against_rules()` and skip or tag as protected so they never appear as forgettable; use `explain_why_protected()` in UI when showing “why is this protected?”.

- **Apply review-pack decisions to substrate**  
  When `record_review_decision(..., approved=True)` is called for a forgetting item, persist “applied” in the curation store only; add an optional step that actually removes or archives the corresponding units in the memory substrate (or outcome history) so that “approve” has a visible effect.

- **Archival policy enforcement**  
  When creating an archive (e.g. from state_durability or a new “archive now” CLI), enforce `ArchivalPolicyCuration`: check `min_age_days`, `require_review_before_archive`, and `max_archives_per_scope` before writing archival state.

- **Mission control slice**  
  Add to `memory_curation_state`: `protection_rules_count`, `review_packs_pending_count`, and `archival_policies_count` (or a short summary) so the pane has one-place visibility for protection, review backlog, and archival policy status.
