# OSS Evaluation Policy

External OSS is a **reference** and **pattern source**, not an architecture owner.

## Adoption criteria
- Solves a **specific, present** gap in this repo.
- Preserves **local-first**, **approval-gated**, **auditable** behavior.
- Has clear integration tests and bounded surface area.

## Rejection criteria
- Large framework import without a scoped integration plan.
- Framework assumes uncontrolled autonomy.
- Adds dependency sprawl or duplicates existing subsystems.

## Required process
1. Map the OSS capability to existing modules.
2. Define the integration boundary (API shape + tests).
3. Verify it does **not** replace the repo’s workflow-tree direction.

## Default stance
Prefer **wrapping patterns** and **re-implementing small abstractions** inside this repo.
