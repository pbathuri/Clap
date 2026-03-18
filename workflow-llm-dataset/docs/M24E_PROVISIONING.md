# M24E — Specialization Recipe Runner + Domain Provisioning

## Purpose

Turn domain packs, starter kits, and specialization recipes into **runnable local provisioning flows**. The system already recommends packs and recipes; this layer **executes** domain-specialization provisioning in a safe, local, explicit, and approval-aware way.

## What this phase does

- **Recipe run model:** Each run has run_id, source recipe, target domain/value pack, machine assumptions, approvals required, steps done, outputs, status, reversible flag, rollback notes.
- **Provisioning runner:** Prepares local sample/demo assets, writes pack manifest under `data/local/provisioning/<pack_id>/`, stages specialization dirs (e.g. corpus). Stops if prerequisites are missing (unless `--no-strict`).
- **Domain environment summary:** What is provisioned, jobs/routines/macros ready, what needs activation, what remains simulate-only, recommended first-value run.
- **Sample execution targets:** Strong local provisioning for founder_ops_plus, analyst_research_plus, developer_plus, document_worker_plus (and operations_logistics_plus).
- **Mission control:** Provisioned packs, failed provisioning runs, recommended next first-value flow, missing prerequisites.

## What this phase does NOT do

- No auto-download of large models or datasets.
- No auto-train or hidden background adaptation.
- No cloud-managed specialization.
- No bypass of approvals or trust boundaries.

## CLI

```bash
# Recipe runs (provisioning history)
workflow-dataset recipe runs list [--repo-root PATH] [--limit N]
workflow-dataset recipe run --id founder_ops_recipe [--repo-root] [--dry-run] [--no-strict]
workflow-dataset recipe preview --id founder_ops_recipe [--repo-root]
workflow-dataset recipe report [--latest] [--repo-root]

# Value pack provisioning (by pack id)
workflow-dataset packs provision --id founder_ops_plus [--repo-root] [--dry-run] [--no-strict]

# Domain environment (readiness per pack)
workflow-dataset value-packs domain-env --id founder_ops_plus [--repo-root]
```

Recipe aliases (e.g. `founder_ops_recipe`) map to value pack ids (e.g. `founder_ops_plus`).

## Storage

- **Recipe runs:** `data/local/specialization/recipe_runs/<run_id>.json`
- **Provisioning manifests:** `data/local/provisioning/<value_pack_id>/provisioning_manifest.json`
- **Sample assets:** `data/local/value_packs/samples/` (and stubs created by provisioning if missing)

## Safety

- All writes are under `data/local/`. No arbitrary script execution; only declarative steps (prepare assets, write manifest, create dirs).
- Prerequisite check uses existing job pack, routine, and approval registry checks; provisioning can refuse to run when strict.
- Rollback: remove provisioning dir and recipe run state; no hidden state elsewhere.

## Mission control

The mission control dashboard includes a **Provisioning** section:

- provisioned_packs
- failed_provisioning_runs
- recommended_next_first_value_flow
- missing_prerequisites

Run `workflow-dataset mission-control` (or equivalent) to see the full report.
