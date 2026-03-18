# Sample profile: local_standard

**Tier:** `local_standard`  
**Description:** Standard local: core paths and LLM; adapter/retrieval optional.

## When to use

Use this profile for typical local runs: core workspaces, packages, pilot, review, staging, LLM runs, packs. No devlab/incubator/trials required. LLM is required for full workflows.

## Required paths (relative to repo root)

- `data/local/workspaces`
- `data/local/packages`
- `data/local/pilot`
- `data/local/review`
- `data/local/staging`
- `data/local/llm/runs`
- `data/local/packs`
- `data/local/input_packs`

## LLM requirement

**Required.** Full workflow runs need an LLM backend. Adapter and retrieval corpus are optional (baseline fallback).

## Workflow support

All ops/reporting workflows are **supported**: weekly_status, status_action_bundle, stakeholder_update_bundle, meeting_brief_bundle, ops_reporting_workspace.

## Example commands

```bash
workflow-dataset edge profile --tier local_standard
workflow-dataset edge package-report --tier local_standard --output data/local/edge/pkg_local.md
workflow-dataset edge smoke-check --tier local_standard
workflow-dataset edge compare --tier local_standard --tier-b constrained_edge
```

## Example readiness outcome

- **Ready:** true when config exists, Python ≥3.10, and core paths (workspaces, review, configs) exist.
- If **optional** checks fail (e.g. llm_config), workflows may still run in baseline mode; see smoke-check output.
