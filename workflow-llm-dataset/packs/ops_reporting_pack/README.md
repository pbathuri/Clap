# Ops reporting pack

First real installable role pack for the workflow-llm-dataset runtime. Aligns with narrow release scope (Operations reporting assistant).

## Scope

- **Role:** ops
- **Workflows:** reporting, summarize_reporting, scaffold_status, next_steps
- **Tasks:** ops_summarize_reporting, ops_scaffold_status, ops_next_steps
- **Output adapter:** ops_handoff

## External references (M21/M22)

Pattern alignment only; no imported code:

- **OpenClaw:** Runtime layer model (channel, planner, memory, tools, policy, pack).
- **World Monitor:** Readiness report structure (scope, ready, evidence, recommendation) reflected in pilot report and pack report.

## Install

```bash
workflow-dataset packs install packs/ops_reporting_pack/manifest.json
workflow-dataset packs activate ops_reporting_pack
```

See docs/packs/FIRST_ROLE_PACK_DEMO.md for full demo flow.
