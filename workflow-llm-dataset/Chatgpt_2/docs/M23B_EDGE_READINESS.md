# M23B — Edge / Hardware Readiness Layer

Local deployment/readiness layer that prepares the product for future appliance/edge packaging. No hardware device specs; deployment assumptions and readiness only.

## Edge tiers (M23B-F2)

Local deployment tiers (profile categories, not hardware products):

| Tier | Description |
|------|-------------|
| `dev_full` | Full dev: all sandbox paths, LLM required, adapter/retrieval optional. |
| `local_standard` | Standard local: core paths and LLM; adapter/retrieval optional. |
| `constrained_edge` | Constrained: minimal paths; LLM optional (baseline only when present). |
| `minimal_eval` | Eval-only: data/local + eval; no reporting workflows. |

Per tier, workflows are classified as **supported**, **degraded**, or **unavailable**, with reason, missing functionality, and fallback.

## Commands

All under `workflow-dataset edge`:

| Command | Description |
|--------|-------------|
| `edge report` | Full edge readiness report. Default output: `data/local/edge/edge_readiness_report.md` |
| `edge missing-deps` | Missing dependency report. Default: `data/local/edge/missing_dependency_report.md` |
| `edge workflow-matrix` | Supported workflow matrix (markdown or JSON). Default: `data/local/edge/supported_workflow_matrix.md` |
| `edge profile` | Print edge profile summary. Use `--tier` for tier-scoped profile. |
| `edge matrix` | Workflow support matrix by tier (supported/degraded/unavailable, reason, fallback). Optional `--tier`. |
| `edge compare` | Compare two tiers (workflow status diff, paths diff, LLM requirement). |

Options (where applicable):

- `--config`, `-c`: Config path (default `configs/settings.yaml`)
- `--tier`, `-t`: Tier (dev_full, local_standard, constrained_edge, minimal_eval)
- `--tier-b`: Second tier for `edge compare`
- `--output`, `-o`: Output file path
- `--repo-root`: Override repo root
- `--format`, `-f`: For `workflow-matrix` / `matrix`: `markdown` or `json`

## Example usage

```bash
# Full readiness report
workflow-dataset edge report

# Profile for a specific tier
workflow-dataset edge profile --tier local_standard

# Workflow matrix for one tier
workflow-dataset edge matrix --tier constrained_edge --output data/local/edge/constrained_matrix.md

# Workflow matrix for all tiers
workflow-dataset edge matrix --output data/local/edge/all_tiers_matrix.md

# Compare two tiers
workflow-dataset edge compare --tier local_standard --tier-b constrained_edge
workflow-dataset edge compare --tier local_standard --tier-b constrained_edge --output data/local/edge/tier_compare.md

# Missing dependencies only
workflow-dataset edge missing-deps --output data/local/edge/missing_dependency_report.md

# Workflow matrix as JSON
workflow-dataset edge workflow-matrix --format json --output data/local/edge/matrix.json
```

## Outputs

1. **Edge readiness report** — Profile summary, readiness checks, supported workflows.
2. **Missing dependency report** — Required/optional dependency reference, path status, warnings.
3. **Supported workflow matrix** — Per-workflow: description, required/optional components.
4. **Tier workflow matrix** (`edge matrix`) — Per-tier: workflow status (supported/degraded/unavailable), reason, missing functionality, fallback.
5. **Tier comparison** (`edge compare`) — LLM requirement diff, workflow status diff, paths only in A vs B.

All outputs are local and inspectable (markdown or JSON under `data/local/edge/` by default).

## What this layer does not do

- Does not define or assume hardware devices.
- Does not add cloud-first behavior.
- Does not weaken local-first / privacy-first behavior.
- Does not broaden end-user scope.

It only makes runtime/dependency/storage/workflow assumptions explicit and validates local deployment requirements for future edge-style packaging.
