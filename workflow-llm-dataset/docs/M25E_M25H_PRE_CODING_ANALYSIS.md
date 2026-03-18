# M25E–M25H Pack-Driven Behavior Engine — Pre-Coding Analysis

## 1. What pack resolution / runtime behavior already exists

- **behavior_models.py**: `PackPromptAsset`, `PackTaskDefaults`, `PackRetrievalProfilePreset`, `PackOutputProfilePreset`, `ParserOutputHint`, `ResolvedBehavior`, `BehaviorResolutionResult`; allowed-key sets for retrieval/output/parser; prompt asset kinds.
- **behavior_assets.py**: Load from `manifest.behavior` — `get_prompt_assets_from_manifest`, `get_task_defaults_from_manifest`, `get_retrieval_profile_presets_from_manifest`, `get_output_profile_presets_from_manifest`, `get_parser_output_hints_from_manifest`.
- **behavior_resolver.py**: `resolve_behavior_for_task(task_id, workflow_id, role, packs_dir)` → `BehaviorResolutionResult`; precedence (pinned > primary > secondary); merge of prompt assets, task defaults, retrieval/output presets, parser hints; winning pack and why; `get_active_behavior_summary(packs_dir)` for mission control.
- **pack_resolution_graph.py**: `resolve_with_priority(role, workflow_type, task_type, packs_dir)` → `ActiveCapabilities`, `ResolutionExplanation` (primary, pinned, secondary, excluded, conflicts).
- **pack_activation.py**: Activation state (primary_pack_id, pinned, suspended, current_role, current_workflow, current_task).
- **pack_conflicts.py**: `detect_conflicts(active_packs, ...)` → conflict list; `ConflictClass` (e.g. BLOCKED).
- **PackManifest** (pack_models.py): `behavior: dict[str, Any]` for prompt_assets, task_defaults, retrieval_profile_presets, output_profile_presets, parser_output_hints.
- **CLI**: `packs behavior explain|active|prompt|defaults|retrieval-profile|output-profile` with `--task`, `--workflow`, `--role`, `--packs-dir`.
- **Mission control**: `pack_behavior` slice (winning_pack_id, active_pack_ids, task_defaults, retrieval/output profile, why_*, excluded, conflicts); report section [Pack behavior].
- **Tests**: test_pack_behavior.py — prompt/task_defaults loading, resolution result structure, resolved prompt assets, task defaults resolution, active summary, retrieval/output presets, parser hints, why_* explanations.

## 2. What is missing for true pack-driven behavior

- **Runtime consumption**: No execution path currently calls `resolve_behavior_for_task` and uses the result to change prompts, adapter, or model. Job run (`job_packs/execute.run_job`), release_demo (CLI), and generate/trial paths build prompts from constants or context only; they do not inject pack prompt assets or apply pack task defaults.
- **Job/task mapping**: No API that takes `job_pack_id` (or workflow/task id) and returns resolved behavior for that scope so that runners can “use pack behavior for this job.”
- **Merged prompt text for runtime**: Resolved `prompt_assets` are returned as a list; there is no helper that produces a single “instruction” or “system + task prompt” string that a runner can prepend to its prompt.
- **Conflict/exclusion in explain**: explain already prints conflicts and why_excluded; a dedicated “conflicts” subcommand or clearer conflict-blocked explanation could help.
- **Docs**: No single doc that describes the full behavior engine, manifest shape, resolution, precedence, and how runtime should consume it.

## 3. Exact file plan

| Action | File | Purpose |
|--------|------|---------|
| Create | `packs/behavior_runtime.py` | `get_resolved_behavior_for_job(job_pack_id, repo_root)`, `get_resolved_behavior_for_task(task_id, workflow_id, repo_root)`, `merge_pack_prompts_into_instruction(resolved)` for runtime callers. |
| Modify | `job_packs/execute.py` | In `run_job`, resolve behavior for job (task_id from job.source.ref or job_pack_id); attach `resolved_behavior` (or key fields) to result so behavior is used/inspectable. Optionally pass merged prompt into any prompt-building hook if present. |
| Modify | `cli.py` (release_demo path) | When building `user_prompt` by workflow kind, optionally call behavior runtime for that workflow/task and prepend merged pack prompt_assets to instructions (first-draft, behind existing flow). |
| Add | `packs behavior conflicts` | CLI command to list conflicts and exclusions from current resolution. |
| Modify | `mission_control/state.py` or report | Ensure pack_behavior includes `conflict_summary` / excluded reasons when present (already have excluded_pack_ids and conflicts). |
| Create | `docs/M25E_M25H_PACK_BEHAVIOR_ENGINE.md` | Objective, prompt assets, task defaults, resolution engine, precedence, CLI, mission control, runtime usage, safety, sample manifest and resolution/conflict examples. |
| Add | Tests in `test_pack_behavior.py` | Test `get_resolved_behavior_for_job` (or for_task) returns expected structure; test `merge_pack_prompts_into_instruction`; test conflict/exclusion in explanation output. |

## 4. Safety / risk note

- Packs do not execute code; behavior is data (prompt text, adapter/model/profile names). Resolution is read-only from manifest and activation state.
- Task defaults (adapter, model_class, output_mode) are hints; they must not bypass `check_job_policy`, trust, or approval. Job execution already enforces policy; we only attach resolved behavior to the result or pass it into existing prompt-building paths.
- No new execution paths; we wire existing `resolve_behavior_for_task` into call sites that already run jobs or build prompts.

## 5. What this block will NOT do

- Will not rebuild runtime mesh, value packs, starter kits, onboarding, trust cockpit, acceptance, mission control, or desktop/operator foundations.
- Will not allow packs to execute arbitrary logic or to bypass trust/approval.
- Will not implement full LLM adapter/model selection in runtime mesh from pack defaults (only expose defaults in resolution and in run result; actual backend selection can be a later step).
- Will not change pack conflict detection algorithm; only expose it better and wire resolution into runtime.
