# First real role pack scope: ops_reporting_pack

## Pack id

`ops_reporting_pack`

## Target user type

- Operator / founder doing recurring reporting and status updates.
- Single device, local-first; no cloud or multi-user.

## Supported workflows

- **Reporting:** Summarize reporting workflow, suggest weekly status structure.
- **Scaffold:** Scaffold weekly status report in user's style.
- **Next steps:** Recommend next steps from projects and routines.

## Excluded workflows

- Spreadsheet/finance workflows.
- Creative/design workflows.
- Founder handoff package (beyond ops_handoff adapter).
- Multi-user, cloud, or automated execution.

## Supported tasks (trial ids)

- `ops_summarize_reporting`
- `ops_scaffold_status`
- `ops_next_steps`

## Expected inputs

- Project context (from work graph).
- Style signals / style context (optional).
- Routines (for next_steps).
- Parsed artifacts (optional; for retrieval mode).

## Expected outputs

- Summary and suggested structure (summarize).
- Scaffold / report package structure (scaffold).
- Recommendations (next_steps).
- Optional: ops_handoff bundle when user requests bundle creation.

## Supported runtime modes

- `baseline` (no model; placeholder).
- `adapter` (primary; use fine-tuned adapter).
- `adapter_retrieval` (adapter + retrieval when corpus available).

## Required / recommended models

- **Required:** None (baseline works without model).
- **Recommended:** Local small adapter (e.g. from `data/local/llm/runs`).

## Retrieval requirements

- Optional retrieval: `top_k` 5 when mode is adapter_retrieval.
- Corpus path from LLM config (e.g. `data/local/llm/corpus/corpus.jsonl`).

## Safety boundaries

- Sandbox-only: all generated output to sandbox dirs.
- Require apply confirm before writing to user's real paths.
- No network by default.
- Pack does not override these; validation rejects any manifest that weakens them.

## Success criteria for the pack

1. Pack installs and validates; appears in `packs list` and resolves for `--role ops`.
2. Release run with `--role ops` (or active pack) runs the pack's three trials and uses pack retrieval_profile when applicable.
3. Pilot verify/status reports active pack when ops_reporting_pack is installed and role=ops.
4. A user can install the pack, run release run, and see meaningful ops-specific outputs (summarize, scaffold, next_steps) without changing code.
5. Pack evaluation report can be generated comparing behavior with vs without pack (or with baseline vs adapter).
