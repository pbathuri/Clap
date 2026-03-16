# Sample profile: dev_full

**Tier:** `dev_full`  
**Description:** Full dev: all sandbox paths, LLM required, adapter/retrieval optional.

## When to use

Use this profile when you have a full local dev setup: all sandbox directories, an LLM backend (e.g. configs/llm_training_full.yaml), and optionally adapters and retrieval corpus.

## Required paths (relative to repo root)

- `data/local/workspaces`
- `data/local/packages`
- `data/local/pilot`
- `data/local/review`
- `data/local/staging`
- `data/local/devlab`
- `data/local/eval`
- `data/local/llm/runs`
- `data/local/llm/corpus`
- `data/local/llm/sft`
- `data/local/incubator`
- `data/local/packs`
- `data/local/input_packs`
- `data/local/trials`

## LLM requirement

**Required.** All reporting workflows expect an LLM backend. Adapter and retrieval are optional (baseline used if missing).

## Workflow support

All ops/reporting workflows are **supported**: weekly_status, status_action_bundle, stakeholder_update_bundle, meeting_brief_bundle, ops_reporting_workspace.

## Example commands

```bash
workflow-dataset edge profile --tier dev_full
workflow-dataset edge matrix --tier dev_full --output data/local/edge/dev_full_matrix.md
workflow-dataset edge package-report --tier dev_full
workflow-dataset edge smoke-check --tier dev_full
```

## Example readiness outcome

- **Ready:** true when config exists, Python ≥3.10, and core sandbox paths (e.g. data/local/workspaces, data/local/review, configs) exist.
- **Optional disabled:** e.g. when LLM config or extra paths are missing; workflows still run with baseline where applicable.
