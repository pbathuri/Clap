# M31D.1 — Observation Profiles + Safe Retention Policies

First-draft observation profiles and retention policy output. Extends M31 observation runtime; does not replace it.

## Profiles

| Profile ID | Enabled sources | Metadata depth | Suitable for |
|------------|-----------------|----------------|--------------|
| minimal | file | observe_only | Privacy-first users; audit-only |
| standard | file, app, calendar | observe_only | General knowledge workers; routine + calendar |
| teaching-heavy | file, teaching, calendar | rich_metadata | Instructors, coaches; feedback loops, skill capture |
| document-heavy | file, app, browser | rich_metadata | Content creators, editors; document workflows, research |
| developer-focused | file, terminal, app, browser | observe_only | Developers; coding, builds, repos |

## Sample observation profile (standard)

```yaml
profile_id: standard
display_name: Standard
enabled_sources: [file, app, calendar]
metadata_depth: observe_only
retention_global_default_days: 90
retention_overrides_days: {}
redaction_expectations: "Standard: metadata only; no content. Calendar: title and times only; attendees optional."
suitable_user_types: [general knowledge workers, office roles]
suitable_workflow_types: [routine work, calendar-aware scheduling, project presence]
```

## Sample retention policy output

From `workflow-dataset observe retention-policy --profile standard` (or `format_retention_policy_output()`):

```json
{
  "profile_id": "standard",
  "global_default_days": 90,
  "per_source_retention_days": {
    "file": 90,
    "app": 30,
    "calendar": 90
  },
  "per_source_max_events_per_day": {
    "file": 50000,
    "app": 10000,
    "calendar": 1000
  },
  "summary": "default=90d; file=90d; app=30d; calendar=90d"
}
```

## CLI

- `workflow-dataset observe profiles` — list all profile ids and one-line summary
- `workflow-dataset observe profiles <profile_id>` — show full profile (e.g. `observe profiles standard`)
- `workflow-dataset observe retention-policy [--profile NAME]` — show retention policy (default profile: standard)

## Tests

Run: `pytest workflow-llm-dataset/tests/test_observe_profiles.py -v`

## Next step

- **Apply profile to runtime**: allow selecting a profile (e.g. in observation state or config) so that `observe run` and boundaries use that profile’s enabled_sources and retention policy when writing or rotating events.
