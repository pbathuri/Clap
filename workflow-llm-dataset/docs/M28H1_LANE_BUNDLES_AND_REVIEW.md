# M28H.1 — Lane Bundles + Parent/Child Review

## Summary

- **Reusable lane bundles** for common work types (e.g. `extract_only`, `summarize_only`), stored under `data/local/lanes/bundles/`.
- **Parent/child review summaries** for operator review: parent project/goal, child lane summary, artifacts, handoff status, recommendation.
- **Operator approval** before accepting lane results: handoff status `delivered` → `approved` or `rejected`; then **accept into project** attaches artifacts to the project (only when approved).
- **Lane-level trust/readiness reporting**: `trust_summary`, `readiness_status`, `readiness_reason` on the lane; CLI `lanes trust-report --id <lane_id>`.

## CLI

- `workflow-dataset lanes bundles` — List lane bundles (ensures default bundles exist).
- `workflow-dataset lanes create --project X --goal Y [--bundle extract_only]` — Create lane, optionally from a bundle.
- `workflow-dataset lanes review --id <lane_id>` — Show parent/child review summary.
- `workflow-dataset lanes approve --id <lane_id>` — Approve handoff (operator).
- `workflow-dataset lanes reject --id <lane_id> --reason "..."` — Reject handoff.
- `workflow-dataset lanes accept --id <lane_id>` — Accept approved results into project (attach artifacts).
- `workflow-dataset lanes trust-report --id <lane_id>` — Show trust and readiness for the lane.

## Handoff lifecycle

1. Lane completes → `lanes handoff --id X` → status `delivered`.
2. Operator runs `lanes review --id X` → sees summary and recommendation.
3. Operator runs `lanes approve --id X` or `lanes reject --id X --reason "..."`.
4. If approved, operator runs `lanes accept --id X` → artifacts attached to project, handoff status `accepted`.

## Default bundles

- `extract_only` — Extract data only; no writes.
- `summarize_only` — Summarize content; no external actions.

Both use `simulate_only` permissions and scoped step classes.
