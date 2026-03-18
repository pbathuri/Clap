# M31L.1 — Personal Profile Presets + Reviewable Behavior Deltas

## Overview

Extension to the personal adaptation layer (M31I–M31L):

- **Personal profile presets**: Named sets of preference/style candidates that can be applied as a group and reviewed together.
- **Behavior deltas**: Explicit before/after for each affected surface (packs, workspace, recommendations) when applying a learned preference, for safer review.
- **Dry-run**: `apply-preference --dry-run` shows deltas without accepting or applying.

## Sample personal profile preset

```json
{
  "preset_id": "preset_abc123",
  "name": "Report output style",
  "description": "Prefer bullet output and report paths for weekly_report job",
  "candidate_ids": ["pref_output_style_1", "pref_paths_1"],
  "created_utc": "2025-03-16T12:00:00Z",
  "updated_utc": "2025-03-16T12:00:00Z"
}
```

## Sample behavior-delta output

For a candidate that changes `specialization_output_style` for `weekly_report`:

```
# Behavior delta (before → after)

Candidate: pref_output_style_1

## specialization_output_style
  Key/target: weekly_report
  Before: 'paragraph'
  After:  'bullet'
  → Packs: output style for 'weekly_report' will change from 'paragraph' to 'bullet'.
```

For a candidate that sets `workspace_preset`:

```
## workspace_preset
  Key/target: workspace.focus_project
  Before: None
  After:  '~/projects/ops'
  → Workspace Preset: 'workspace.focus_project' will be set to '~/projects/ops'.
```

## CLI

- `workflow-dataset personal behavior-delta --id <candidate_id>` — show deltas for one candidate.
- `workflow-dataset personal behavior-delta --preset <preset_id>` — show deltas for all candidates in preset.
- `workflow-dataset personal apply-preference --id <candidate_id> --dry-run` — show deltas only; do not apply.
- `workflow-dataset personal profile-presets` — list presets.
- `workflow-dataset personal profile-preset --id <preset_id>` — show preset.
- `workflow-dataset personal profile-preset --create --name "My preset" --candidates pref_1,pref_2` — create preset.

## Storage

- Presets: `data/local/personal_adaptation/presets/<preset_id>.json`

## Tests

Run: `python3 -m pytest tests/test_personal_adaptation.py -v` (includes 7 tests for M31L.1).
