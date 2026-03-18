# M50H.1 — Stable-v1 Maintenance Packs + Support Review Summaries: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/v1_ops/models.py` | Added `MaintenanceObligation`, `MaintenanceObligationsSummary`, `SupportReviewSummary`. |
| `src/workflow_dataset/v1_ops/__init__.py` | Exported new models, `save_maintenance_pack`, `load_maintenance_pack`, `list_maintenance_packs`, `build_maintenance_obligations_summary`, `build_support_review_summary`. |
| `src/workflow_dataset/cli.py` | Added `v1-ops maintenance-pack-save`, `v1-ops maintenance-pack-list`, `v1-ops support-review-summary`, `v1-ops maintenance-obligations`. |
| `tests/test_v1_ops.py` | Added tests for M50H.1 models, store, obligations summary, support review summary. |

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/v1_ops/store.py` | Persist/list stable-v1 maintenance packs: `save_maintenance_pack`, `load_maintenance_pack`, `list_maintenance_packs`. Packs under `data/local/v1_ops/maintenance_packs/`. |
| `src/workflow_dataset/v1_ops/maintenance_obligations.py` | `build_maintenance_obligations_summary` — what must be maintained to preserve stable-v1 (daily/weekly, review cadence, rollback, support paths). |
| `src/workflow_dataset/v1_ops/support_review_summary.py` | `build_support_review_summary` — operator/owner summary: items reviewed, overdue, next actions, ownership roles. |
| `docs/M50H1_STABLE_V1_MAINTENANCE_PACKS_DELIVERABLE.md` | This file. |

## 3. Sample maintenance pack

Saved via `workflow-dataset v1-ops maintenance-pack-save`; one JSON file per pack, e.g. `stable_v1_maintenance_pack_2025-03-17T12-00-00.json`:

```json
{
  "pack_id": "stable_v1_maintenance_pack",
  "label": "Stable v1 maintenance pack",
  "generated_at_utc": "2025-03-17T12:00:00Z",
  "support_posture": {
    "posture_id": "v1_stable_posture",
    "support_level": "sustained",
    "support_paths": ["release_readiness: workflow-dataset supportability", "stability_reviews: ...", "deploy_bundle: ..."],
    "maintenance_rhythm_id": "stable_v1_daily_weekly",
    "review_cadence_id": "rolling_stability",
    "recovery_posture_summary": "Run workflow-dataset deploy-bundle recovery-report for recovery steps.",
    "rollback_ready": false,
    "as_of_utc": "2025-03-17T12:00:00Z"
  },
  "maintenance_rhythm": {
    "rhythm_id": "stable_v1_daily_weekly",
    "label": "Stable v1 daily/weekly",
    "daily_tasks": ["Run: workflow-dataset supportability", "Check: workflow-dataset repair-loops list ...", "Optional: workflow-dataset v1-ops status"],
    "weekly_tasks": ["Run: workflow-dataset stability-reviews generate", "Run: workflow-dataset stability-decision pack", "Review: workflow-dataset v1-ops maintenance-pack"]
  },
  "review_cadence_ref": { "cadence_id": "rolling_stability", "label": "Rolling stability review (7d)", "next_due_iso": "..." },
  "recovery_paths": [...],
  "escalation_paths": [...],
  "rollback_readiness": { "ready": false, "prior_stable_ref": "", "reason": "...", "recommended_action": "..." },
  "ownership_notes": [
    { "role_or_owner": "Operator / release owner", "responsibility": "Daily supportability, stability decision, rollback decision", "scope_note": "Stable v1" },
    { "role_or_owner": "Reliability owner", "responsibility": "Recovery playbooks, repair loops, golden path", "scope_note": "v1 health" }
  ]
}
```

## 4. Sample support review summary

Output of `workflow-dataset v1-ops support-review-summary --json`:

```json
{
  "review_id": "v1_support_review_20250317",
  "period_label": "Stable v1 support review",
  "reviewed_at_iso": "2025-03-10T14:00:00Z",
  "items_reviewed": [
    "Stability decision: continue",
    "Window: Last 7 days"
  ],
  "overdue_items": [],
  "next_actions": [
    "Run: workflow-dataset v1-ops maintenance-pack and stability-reviews latest.",
    "Address overdue items above; run stability-reviews generate if review is overdue."
  ],
  "ownership_roles": [
    "Operator / release owner: Daily supportability, stability decision, rollback decision",
    "Reliability owner: Recovery playbooks, repair loops, golden path"
  ],
  "summary_text": "Support review: 2. Overdue: 0. Next: Run: workflow-dataset v1-ops maintenance-pack.... Owners: Operator / release owner: Daily supportability....",
  "generated_at_utc": "2025-03-17T12:00:00Z"
}
```

## 5. Exact tests run

```bash
pytest tests/test_v1_ops.py -v
```

M50H.1-related tests:

- `test_maintenance_obligation_model`
- `test_maintenance_obligations_summary_model`
- `test_support_review_summary_model`
- `test_save_load_list_maintenance_pack`
- `test_build_maintenance_obligations_summary`
- `test_build_support_review_summary`

## 6. Next recommended step for the pane

- **Wire support review into a cadence**: Persist support review summaries (e.g. `data/local/v1_ops/support_reviews/`) when operators run a review, and surface “last support review” in mission control or `v1-ops status`.
- **Maintenance-obligations in runbook**: Reference `v1-ops maintenance-obligations` from the operator runbook (e.g. docs or `v1-ops maintenance-pack` output) so “what must be maintained” is a single place to look.
- **Optional**: Add `v1-ops maintenance-pack-load --id <path_stem>` to show a previously saved pack by stem/id.
