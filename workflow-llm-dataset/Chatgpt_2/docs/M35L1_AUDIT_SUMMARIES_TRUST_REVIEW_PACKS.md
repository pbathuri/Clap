# M35L.1 — Audit Summaries + Trust Review Packs

Extends M35I–M35L with:
- **Audit summaries** by project, routine, or authority tier
- **Trust review packs** for periodic high-trust operator mode review
- **Clearer periodic review** of what the system has been allowed to do

## Audit summary

Aggregates ledger entries for a scope (project_id, routine_id, or authority tier_id):
- total_entries, approved_count, rejected_count, deferred_count
- by_action_kind (commit/send/apply)
- execution_success_count, execution_failed_count, execution_blocked_count, rollback_count
- recent_entry_ids, period, generated_at_utc

**CLI:**
```bash
workflow-dataset audit summary --project founder_case_alpha [--json]
workflow-dataset audit summary --routine routine_daily [--json]
workflow-dataset audit summary --tier commit_or_send_candidate [--json]
```

## Trust review pack

Bundles for periodic human review:
- audit_summaries (by project and by authority tier)
- pending_gate_ids, pending_count
- recent_signed_off_gate_ids
- anomaly_entry_ids (failed/blocked execution)
- next_recommended_action
- label: "High-trust operator mode review"

**CLI:**
```bash
workflow-dataset trust-review pack [--days 7] [--json]
```

## Models

- **AuditSummary**: scope, scope_value, period_*, counts, by_action_kind, execution_*_count, rollback_count, recent_entry_ids, generated_at_utc
- **TrustReviewPack**: pack_id, generated_at_utc, period_description, audit_summaries, pending_*, recent_signed_off_*, anomaly_entry_ids, next_recommended_action, for_operator_mode, label

## Next recommended step for the pane

- Wire mission control to show "Trust review due" when a trust review pack has pending gates or anomalies and last pack is older than N days (optional).
- Optional: persist latest trust review pack (e.g. `data/local/sensitive_gates/latest_trust_review_pack.json`) for "last review at" visibility.
