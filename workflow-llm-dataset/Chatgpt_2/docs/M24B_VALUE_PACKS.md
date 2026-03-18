# M24B — Vertical Value Packs

## Purpose

Turn the product into **strong, concrete, end-user value packs** so it feels like “this product is immediately useful for my field” rather than a generic AI framework.

## What is a value pack

A value pack defines, for a vertical (founder/operator, analyst, developer, document worker, operations/logistics):

- **Target field and job family**
- **Recommended profile defaults** and **runtime/model class**
- **Recommended jobs, routines, macros**
- **First-value sequence**: install/bootstrap → first simulate run → first trusted-real candidate
- **Benchmark and trust notes**, **approvals likely needed**, **expected outputs**
- **Sample demo assets** (optional local files under `data/local/value_packs/samples/`)

No auto-download; no auto-enable of integrations; trust and approval boundaries unchanged.

## CLI

```bash
workflow-dataset value-packs list
workflow-dataset value-packs show --id founder_ops_plus
workflow-dataset value-packs recommend [--repo-root PATH] [--output FILE]
workflow-dataset value-packs first-run --id analyst_research_plus [--repo-root PATH]
workflow-dataset value-packs compare --id founder_ops_plus --id developer_plus [--repo-root PATH]
```

## Built-in packs

| Pack ID | Target | Why useful | First simulate | First trusted-real candidate |
|--------|--------|------------|----------------|------------------------------|
| founder_ops_plus | Founder / operator | Light ops, reporting, stakeholder updates | macro run morning_ops --mode simulate | jobs run weekly_status_from_notes --mode real |
| analyst_research_plus | Analyst / researcher | Data analysis, reports, retrieval | jobs run weekly_status_from_notes --mode simulate | same job --mode real |
| developer_plus | Developer / coding | Code assistance, task replay | jobs run replay_cli_demo --mode simulate | same --mode real after approvals |
| document_worker_plus | Document-heavy knowledge worker | Long-form docs, summarization | jobs run weekly_status_from_notes --mode simulate | same --mode real |
| operations_logistics_plus | Operations / logistics | Reporting, ops workflows | jobs run weekly_status_from_notes --mode simulate | jobs run weekly_status --mode real |

## What each pack needs

- **founder_ops_plus:** Job packs (e.g. weekly_status_from_notes, weekly_status), routine morning_ops if using macro; approval registry for real mode.
- **analyst_research_plus:** Job packs; approval registry and path_workspace for real/data_export.
- **developer_plus:** Job replay_cli_demo; path_repo and apply_confirm for real.
- **document_worker_plus:** Job packs; path_workspace and apply_confirm.
- **operations_logistics_plus:** Job packs; path_workspace, apply_confirm; external_api approval if using APIs.

## What first value looks like

1. **Install / bootstrap:** `workflow-dataset package first-run` — dirs created, install-check, onboarding status.
2. **Check runtime:** `workflow-dataset runtime backends` — see available backends.
3. **Onboard approvals:** `workflow-dataset onboard status` — then `onboard approve` when ready for real execution.
4. **First simulate run:** Run the pack’s first_simulate command (e.g. `macro run --id morning_ops --mode simulate` or `jobs run --id weekly_status_from_notes --mode simulate`). You see simulated output and run records; no writes.
5. **First trusted-real candidate:** After approvals, run the suggested job/routine with `--mode real` (e.g. `jobs run --id weekly_status_from_notes --mode real`).

## Sample assets

Optional local files under `data/local/value_packs/samples/`:

- `example_notes.txt` — example notes for weekly status / morning ops demos.
- `weekly_notes_sample.md` — weekly notes sample for document-worker and founder-ops.

Use these as example inputs for simulate runs; no sensitive data; local-only.

## Relationship to starter kits

Value packs extend the starter-kit idea with a **concrete first-value sequence**, **benchmark/trust notes**, **pack comparison**, and optional **sample assets**. They map to existing starter kits (e.g. founder_ops_plus → founder_ops_starter) and use the same profile-based recommendation when available.
