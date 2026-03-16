# Edge Readiness — Docs and Sample Profiles

Local deployment profiles for the workflow-dataset edge layer. No hardware device specs; no cloud. All outputs under `data/local/edge/`.

## Sample profiles

| Tier | Description | Workflows | LLM |
|------|-------------|-----------|-----|
| [dev_full](sample_profiles/dev_full.md) | Full dev: all sandbox paths, LLM required | All supported | Required |
| [local_standard](sample_profiles/local_standard.md) | Standard local: core paths and LLM | All supported | Required |
| [constrained_edge](sample_profiles/constrained_edge.md) | Constrained: minimal paths; LLM optional | Degraded | Optional |
| [minimal_eval](sample_profiles/minimal_eval.md) | Eval-only: data/local + eval | Unavailable | None |

## Operator guide

See [EDGE_OPERATOR_GUIDE.md](../EDGE_OPERATOR_GUIDE.md) for:

- How to run profile, matrix, compare, package-report, smoke-check
- How to read degraded-mode output
- How to interpret missing dependencies

## Commands (quick reference)

```bash
workflow-dataset edge profile --tier local_standard
workflow-dataset edge matrix --tier constrained_edge
workflow-dataset edge compare --tier local_standard --tier-b constrained_edge
workflow-dataset edge package-report --tier local_standard
workflow-dataset edge smoke-check --tier local_standard --no-demo
workflow-dataset edge degraded-report --tier constrained_edge
```
