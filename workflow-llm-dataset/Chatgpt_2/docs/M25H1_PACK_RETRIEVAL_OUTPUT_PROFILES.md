# M25H.1 — Pack-Specific Retrieval / Output Profiles

Extension to the pack-driven behavior engine: pack-specific retrieval profile tuning, output profile presets, safer parser/output hints, and clearer operator-readable explanation of why a profile was applied.

---

## Retrieval profile presets

Packs declare retrieval tuning under `manifest.behavior.retrieval_profile_presets`. Only allowed keys are applied: `top_k`, `corpus_filter`, `max_tokens`, `min_score`, `rerank`, `include_metadata`. Scope by `task_id` and/or `workflow_id`.

**Sample retrieval profile preset (manifest):**

```json
{
  "behavior": {
    "retrieval_profile_presets": [
      {
        "preset_id": "ops_retrieval",
        "task_id": "weekly_status",
        "workflow_id": "founder_ops",
        "top_k": 5,
        "corpus_filter": "reporting",
        "rerank": true,
        "include_metadata": false
      }
    ]
  }
}
```

Resolution picks the first matching preset in precedence order (pinned > primary > secondary). The resolved behavior includes `retrieval_profile` (dict), `retrieval_profile_source_pack`, `retrieval_profile_preset_id`, and `why_retrieval_profile` (operator-readable string).

---

## Output profile presets

Packs declare output presets under `manifest.behavior.output_profile_presets`. Allowed keys: `adapter`, `format_hint`, `max_length_hint`, `sections_hint` (and any in `OUTPUT_PROFILE_ALLOWED_KEYS`). Scope by `task_id` and/or `workflow_id`.

**Sample output profile preset (manifest):**

```json
{
  "behavior": {
    "output_profile_presets": [
      {
        "preset_id": "ops_output",
        "task_id": "weekly_status",
        "workflow_id": "founder_ops",
        "adapter": "ops_handoff",
        "format_hint": "bullets",
        "max_length_hint": 500,
        "sections_hint": "summary,next_steps"
      }
    ]
  }
}
```

Resolution sets `output_profile`, `output_profile_source_pack`, `output_profile_preset_id`, and `why_output_profile`.

---

## Safer parser/output hints

Parser hints are under `manifest.behavior.parser_output_hints`. Only safe keys are read: `key` (or `task_id`/`workflow_id`), `preferred_format`, `max_length_hint`, `bullet_preference`, `stakeholder_safe`. Keys not in this set are ignored; no arbitrary logic from packs.

---

## Why a profile was applied (operator-readable)

After resolution, the engine sets:

- **why_retrieval_profile**: e.g. `"Applied retrieval preset 'ops_retrieval' from pack ops_pack (primary). Scope: task=weekly_status workflow=founder_ops."`
- **why_output_profile**: e.g. `"Applied output preset 'ops_output' from pack ops_pack (primary). Scope: task=weekly_status workflow=founder_ops."`

If no precedence override applies, the message indicates "first matching; no precedence override". Preset id is also available as `retrieval_profile_preset_id` and `output_profile_preset_id` on the resolved behavior.

CLI:

- `workflow-dataset packs behavior retrieval-profile --task weekly_status` — shows preset id, pack, key-value profile, and **why**.
- `workflow-dataset packs behavior output-profile --task weekly_status` — same for output profile.

Mission control pack_behavior slice includes `retrieval_profile_preset_id`, `output_profile_preset_id`, and the why_* strings.

---

## Allowed keys reference

- **Retrieval**: `top_k`, `corpus_filter`, `max_tokens`, `min_score`, `rerank`, `include_metadata`
- **Output**: `adapter`, `format_hint`, `max_length_hint`, `sections_hint`
- **Parser/output hint**: `preferred_format`, `max_length_hint`, `bullet_preference`, `stakeholder_safe` (and scope key/task_id/workflow_id)
