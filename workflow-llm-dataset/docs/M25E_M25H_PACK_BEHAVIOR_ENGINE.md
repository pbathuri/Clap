# M25E–M25H — Pack-Driven Behavior Engine

## Objective

First-draft behavior engine so packs **meaningfully affect runtime behavior** in a structured, inspectable way:

- Pack-provided **prompt assets** (system guidance, task/workflow prompts, explanation and output hints)
- **Task-level defaults** (preferred adapter, model class, retrieval profile, output mode) without bypassing trust/approval
- **Retrieval and output profile** overrides with precedence
- **Parser/output hints** where safe
- **Explicit precedence** (pinned > primary > secondary) and **explainable** resolution
- **Conflict and exclusion** reporting

No arbitrary code execution from packs; no hidden behavioral mutation.

---

## Prompt assets

Declared under `manifest.behavior.prompt_assets` (or `prompts_behavior`):

| kind | Description |
|------|-------------|
| system_guidance | System-level instruction (e.g. tone, scope) |
| task_prompt | Task-scoped prompt text |
| workflow_prompt | Workflow-scoped prompt |
| explanation_style_hint | How to explain results |
| output_framing_hint | How to frame output |

Each asset: `kind`, `key` (task_id or workflow_id or empty for global), `content`, `priority_hint` (low/medium/high). Resolution merges assets from active packs in precedence order; runtime can use `merge_pack_prompts_into_instruction(resolved)` to get a single string for prepending to prompts.

---

## Task-level defaults

Declared under `manifest.behavior.task_defaults`:

- `task_id`, `workflow_id` (optional scope)
- `preferred_adapter`, `preferred_model_class`, `preferred_output_mode`
- `execution_mode_hint` (e.g. simulate_first)

First pack in precedence order that supplies a value wins. These are **hints**; they do not bypass `check_job_policy`, trust, or approval. Runtime may use them to choose adapter/model when multiple are allowed.

---

## Retrieval and output profiles

- **Retrieval**: `manifest.behavior.retrieval_profile_presets` — `preset_id`, `task_id`, `workflow_id`, `top_k`, `corpus_filter`, `rerank`, etc. Only allowed keys (e.g. top_k, corpus_filter, max_tokens, min_score, rerank, include_metadata) are applied.
- **Output**: `manifest.behavior.output_profile_presets` — adapter, format_hint, max_length_hint, sections_hint.

Resolution picks the first matching preset in precedence order; `why_retrieval_profile` and `why_output_profile` explain the choice.

---

## Behavior resolution engine

- **Entry**: `resolve_behavior_for_task(task_id, workflow_id, role, packs_dir)` → `BehaviorResolutionResult`.
- **Precedence**: pinned pack(s) first, then primary role pack, then secondary. For single-value (task defaults, retrieval/output preset), first in order wins; prompt assets are merged in order.
- **Output**: `resolved` (ResolvedBehavior: prompt_assets, task_defaults, retrieval_profile, output_profile, parser_output_hints, winning_pack_id, *_source_pack, contributing_pack_ids, excluded_pack_ids, exclusion_reasons, conflict_summary, why_*), plus `why_winning`, `why_excluded`, `conflicts`.

**Runtime API** (for job/task execution):

- `get_resolved_behavior_for_job(job_pack_id, repo_root)` — uses job.source.ref as task_id when source is task_demo.
- `get_resolved_behavior_for_task(task_id, workflow_id, role, repo_root)` — direct task/workflow scope.
- `merge_pack_prompts_into_instruction(resolved)` — builds one instruction string from prompt_assets.
- `get_behavior_summary_for_job(job_pack_id, repo_root)` — compact summary for attaching to run result.

---

## Wiring runtime

- **run_job** (job_packs/execute.py): After policy check, calls `get_behavior_summary_for_job` and attaches `resolved_behavior` to the result dict (task_demo and benchmark_case). Downstream can use `resolved_behavior.prompt_instruction`, `task_defaults`, `retrieval_profile`, `output_profile`, and why_* for prompts and adapter choice.

---

## CLI

| Command | Description |
|---------|-------------|
| `workflow-dataset packs behavior explain --task weekly_status` | Why this pack behavior applies; winning pack, exclusions, conflicts |
| `workflow-dataset packs behavior active` | Current active overrides and sources |
| `workflow-dataset packs behavior prompt --task stakeholder_update` | Resolved prompt assets for task |
| `workflow-dataset packs behavior defaults --workflow founder_ops` | Resolved task-level defaults |
| `workflow-dataset packs behavior retrieval-profile --task weekly_status` | Resolved retrieval profile and why |
| `workflow-dataset packs behavior output-profile --task weekly_status` | Resolved output profile and why |
| `workflow-dataset packs behavior conflicts [--task T] [--workflow W]` | Conflicts and exclusions from resolution |

---

## Mission control

- **pack_behavior** slice: winning_pack_id, active_pack_ids, primary_pack_id, pinned_pack_id, prompt_asset_count, prompt_asset_sources, task_defaults, retrieval_profile, output_profile, *_source_pack, why_retrieval_profile, why_output_profile, excluded_pack_ids, exclusion_reasons, conflict_summary, why_current_behavior, conflicts, why_excluded.
- **Report**: [Pack behavior] section with winning/active, task_defaults, why, retrieval/output profile and source, excluded, conflict_summary, conflicts.

---

## Sample prompt asset definition (manifest)

```json
{
  "behavior": {
    "prompt_assets": [
      { "kind": "system_guidance", "key": "weekly_status", "content": "Be concise and ops-focused.", "priority_hint": "high" },
      { "kind": "task_prompt", "key": "weekly_status", "content": "Generate weekly status from notes.", "priority_hint": "medium" }
    ]
  }
}
```

---

## Sample task-level default definition (manifest)

```json
{
  "behavior": {
    "task_defaults": [
      {
        "task_id": "weekly_status",
        "workflow_id": "founder_ops",
        "preferred_adapter": "ops_handoff",
        "preferred_model_class": "general_chat_reasoning",
        "preferred_output_mode": "ops_handoff"
      }
    ]
  }
}
```

---

## Sample behavior resolution explanation

- **why_winning**: "primary pack ops_pack supplies task defaults for task=weekly_status workflow=founder_ops"
- **why_retrieval_profile**: "primary pack ops_pack supplies retrieval profile for task=weekly_status workflow=founder_ops"
- **why_excluded**: ["other_pack: excluded (suspended or conflict-blocked)"]

---

## Sample conflict / exclusion explanation

- **conflict_summary**: "precedence_required: default_adapter (pack_a, pack_b)"
- **conflicts**: ["blocked: network_required (strict_local_pack, proxy_pack)"]
- **why_excluded**: ["proxy_pack: excluded (suspended or conflict-blocked)"]

---

## Safety

- Packs supply only data (prompt text, adapter/model names, profile keys). No code execution.
- Task defaults do not bypass `check_job_policy` or approval; they are hints for allowed paths.
- Resolution is read-only from manifest and activation state. Stricter safety constraints win when merged.

---

## Remaining gaps (for later)

- Full wiring of pack prompt_instruction into release_demo / generate prompt build (optional prepend).
- Runtime mesh actually selecting adapter/model from pack task_defaults when multiple backends exist.
- Richer exclusion_reasons (per-pack reason strings from conflict detection).
