# Sample profile: minimal_eval

**Tier:** `minimal_eval`  
**Description:** Eval-only: data/local + eval; no reporting workflows.

## When to use

Use this profile when you only need the eval harness (e.g. data/local/eval) and do not run ops/reporting workflows. No LLM, no workspace workflows.

## Required paths (relative to repo root)

- `data/local`
- `data/local/eval`

## LLM requirement

**None.** This tier does not assume an LLM or reporting workflows.

## Workflow support

All ops/reporting workflows are **unavailable**:

- **Why:** Eval-only tier: no reporting workspace or LLM.
- **Fallback:** Use constrained_edge or local_standard for reporting; use this tier for eval harness only.

## Example commands

```bash
workflow-dataset edge profile --tier minimal_eval
workflow-dataset edge matrix --tier minimal_eval
workflow-dataset edge package-report --tier minimal_eval
```

## Example readiness outcome

- **Ready:** true when config exists, Python ≥3.10, and data/local + data/local/eval exist.
- **Workflows:** none runnable; tier is for eval/benchmark infrastructure only.
