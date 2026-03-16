# Tier Comparison

**local_standard** vs **constrained_edge**

- **local_standard**: Standard local: core paths and LLM; adapter/retrieval optional.
- **constrained_edge**: Constrained: minimal paths; LLM optional (baseline only when present).

## LLM requirement

- local_standard: required
- constrained_edge: optional

## Workflow status diff

- **weekly_status**: local_standard=supported → constrained_edge=degraded
- **status_action_bundle**: local_standard=supported → constrained_edge=degraded
- **stakeholder_update_bundle**: local_standard=supported → constrained_edge=degraded
- **meeting_brief_bundle**: local_standard=supported → constrained_edge=degraded
- **ops_reporting_workspace**: local_standard=supported → constrained_edge=degraded

## Paths only in first tier
- data/local/input_packs
- data/local/llm/runs
- data/local/packs
- data/local/pilot
- data/local/review
- data/local/staging

## Paths only in second tier
- data/local
