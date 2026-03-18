# Sample profile: constrained_edge

**Tier:** `constrained_edge`  
**Description:** Constrained: minimal paths; LLM optional (baseline only when present).

## When to use

Use this profile for minimal local setups: only `data/local`, `data/local/workspaces`, and `data/local/packages`. LLM is optional; if present, baseline runs are possible. Workflows are in **degraded** mode: they can run in a reduced way when LLM config is available.

## Required paths (relative to repo root)

- `data/local`
- `data/local/workspaces`
- `data/local/packages`

## LLM requirement

**Optional.** With LLM config you can run baseline workflow demos. Without LLM, reporting workflows are not runnable; use this tier for packaging checks or pair with minimal_eval for eval-only.

## Workflow support

All ops/reporting workflows are **degraded**:

- **Why:** LLM optional; with LLM runs baseline only. Without LLM workflows not runnable.
- **Missing (when degraded):** Adapter, Retrieval, Full sandbox.
- **Fallback:** Provide LLM config for baseline runs; or use minimal_eval for eval-only.

## Example commands

```bash
workflow-dataset edge profile --tier constrained_edge
workflow-dataset edge matrix --tier constrained_edge
workflow-dataset edge degraded-report --tier constrained_edge
workflow-dataset edge smoke-check --tier constrained_edge --no-demo
```

## Example readiness outcome

- **Ready:** can be true with only config + minimal paths. Workflow runs still require LLM for demo steps.
- **Degraded workflows:** see `edge degraded-report --tier constrained_edge` for full list and fallback text.
