# M27H.1 — Batched Approvals + Operator Policies

Extension to the supervised agent loop: batch approval of low-risk actions, operator policies for auto-queue vs manual review, clearer queue prioritization, and safer deferral/revisit.

## Sample operator policy

File: `data/local/supervised_loop/operator_policy.json` (create or edit; defaults used if missing).

```json
{
  "batch_approve_max_risk": "low",
  "auto_queue_action_types": ["planner_compile"],
  "always_manual_review_action_types": ["executor_resume"],
  "always_manual_review_risk_levels": ["high"],
  "always_manual_review_modes": ["real"],
  "defer_revisit_max_days": 7
}
```

- **batch_approve_max_risk**: Only pending items with `risk_level` ≤ this are eligible for `approve-batch` (`"low"` or `"medium"`).
- **auto_queue_action_types**: Action types that may be auto-queued without an extra gate (informational).
- **always_manual_review_action_types**: Never batch-approved; must be approved individually (e.g. `executor_resume`).
- **always_manual_review_risk_levels**: e.g. `["high"]` — high-risk always manual.
- **always_manual_review_modes**: e.g. `["real"]` — real mode always manual.
- **defer_revisit_max_days**: Advisory max days for `--revisit-after` when deferring.

See also: `docs/M27H1_OPERATOR_POLICY_EXAMPLE.json`.

## Sample batched approval output

```
Batch approval  max_risk=low  approved=2
  Approved q_abc123
  Approved q_def456
  executed q_abc123  handoff=h_1  status=completed
  executed q_def456  handoff=h_2  status=completed
  Skipped (manual review): ['q_ghi789']
  Skipped (risk): []
```

When no items are eligible:

```
Batch approval  max_risk=low  approved=0
  Skipped (manual review): ['q_ghi789', 'q_jkl012']
  Skipped (risk): ['q_mno345']
```

## CLI

- **policy**: Show current operator policy (and path to JSON).
- **approve-batch** [--max-risk low|medium] [--no-execute]: Batch approve eligible pending items; optionally execute each.
- **defer** --id q_xxx [--reason "…"] [--revisit-after 2025-02-01]: Defer with optional reason and revisit-after date.
- **list-deferred**: List deferred items with defer_reason and revisit_after.
- **revisit** --id q_xxx: Move a deferred item back to pending.

Queue listing is sorted: manual-review first, then by risk (low first), then by created_at. Batch hint is printed at the bottom of `agent-loop queue`.

## Tests run

```bash
pytest tests/test_supervised_loop.py -v --tb=short
```

Covers: operator policy roundtrip, requires_manual_review, risk_within_batch_limit, list_pending_sorted, defer with reason/revisit_after, list_deferred, revisit_deferred, approve_batch (low-risk approved, manual-review skipped).

## Next recommended step for the pane

1. **Wire policy into next-action proposal**  
   When proposing actions, tag or filter by policy (e.g. do not auto-queue action types that are in `always_manual_review_action_types`, or surface a “manual review” hint in the queue).

2. **Revisit reminders**  
   Optional: `agent-loop list-deferred` could highlight items whose `revisit_after` is in the past, or a small “deferred due for revisit” in mission control.

3. **Policy schema validation**  
   Validate `operator_policy.json` on load (allowed keys, allowed values for `batch_approve_max_risk`, etc.) and print a clear error if invalid.
