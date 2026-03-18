# M26H.1 — Cross-App Action Bundles + Human-In-The-Loop Recovery

## Objective

Extend the executor with:

- **Reusable cross-app action bundles**: named sequences of `job_run` and `adapter_action` steps (e.g. `adapter_id:action_id`) stored under `data/local/executor/bundles.json`.
- **Blocked-step recovery flows**: options (retry, skip, substitute) and CLI to inspect and act.
- **Human-in-the-loop correction/resume**: record recovery decisions on the run; resume-from-blocked applies the choice and continues with artifact handoff.
- **Artifact handoff after recovery**: artifacts from before the block are preserved; new artifacts from retry or substitute are merged and persisted.

Safety-first: no new execution paths that bypass approvals; recovery is explicit and recorded.

## Action bundles

- **Model**: `ActionBundle(bundle_id, title, description, steps: list[BundleStep], tags)`. `BundleStep(action_type, action_ref, label)` with `action_type` in `job_run` | `adapter_action`; `action_ref` is `job_pack_id` or `adapter_id:action_id`.
- **Registry**: `data/local/executor/bundles.json` with a `bundles` array.
- **API**: `list_bundles`, `get_bundle`, `save_bundle`, `delete_bundle` (in `executor/bundles.py`).

## Recovery model

- **BlockedStepRecovery**: `step_index`, `decision` (retry | skip | substitute | record_correction), `substitute_bundle_id`, `substitute_action_ref`, `note`, `timestamp`.
- **ExecutionRun**: new field `recovery_decisions: list[BlockedStepRecovery]`; serialized in `run_state.json`.
- **Hub**: `get_recovery_options(run_id)` → options + suggested_bundles; `record_recovery_decision(run_id, step_index, decision, ...)`.

## Resume-from-blocked flow

1. Run is **blocked** at `current_step_index`.
2. Operator runs `workflow-dataset executor recovery-options --run <id>` to see retry/skip/substitute and suggested bundles.
3. Operator runs `workflow-dataset executor resume-from-blocked --run <id> --decision skip|retry|substitute [--substitute-bundle ID] [--substitute-action-ref job_id_or_adapter:action] [--note "..."]`.
4. Runner records the recovery decision, then:
   - **skip**: mark step skipped, advance to next step, continue plan (artifact list preserved).
   - **retry**: re-run same job; on success continue, on failure set blocked again.
   - **substitute**: run bundle steps or single substitute action; merge new artifacts; then continue from next step.
5. Artifacts from before the block are kept; any new artifacts from retry/substitute are appended and persisted via `save_artifacts_list`.

## CLI

| Command | Description |
|---------|-------------|
| `executor recovery-options --run <id>` | Show recovery options and suggested bundles for a blocked run |
| `executor resume-from-blocked --run <id> --decision skip \| retry \| substitute` | Apply recovery and continue |
| `executor resume-from-blocked ... --substitute-bundle <bundle_id>` | Use bundle when decision=substitute |
| `executor resume-from-blocked ... --substitute-action-ref <job_id or adapter:action>` | Single substitute action |
| `executor bundles` | List registered action bundles |

## Tests

- `test_action_bundle_shape`, `test_save_and_list_bundles`
- `test_recovery_options_requires_blocked_run`, `test_recovery_options_for_blocked_run`
- `test_record_recovery_decision`, `test_execution_run_serialize_recovery_decisions`
- `test_resume_from_blocked_not_found`, `test_resume_from_blocked_skip`

Run: `pytest tests/test_executor.py -v`
