# M37L.1 — State Compaction + Long-Run Maintenance Profiles

First-draft extension to the state durability layer (M37I–M37L):

- **Maintenance profiles** — Named profiles (light, balanced, aggressive) with per-subsystem retention and summarization thresholds.
- **Compaction recommendations** — Read-only scan of background_run history, automation_inbox decisions, event_log; operator-facing recommendations and suggested commands.
- **Safer archival/summarization** — No automatic archival; recommendations only. Operator can review and act.
- **Clearer operator-facing maintenance** — `operator_summary_lines` and per-recommendation `operator_summary` and `suggested_command`.

## CLI usage

```bash
# List maintenance profiles
workflow-dataset state maintenance-profiles [--json]

# Show one profile
workflow-dataset state maintenance-profiles --profile balanced [--json]
workflow-dataset state maintenance-profiles -p light

# Compaction recommendations (read-only; profile defaults to balanced)
workflow-dataset state compaction-recommendations [--repo PATH] [--profile light|balanced|aggressive] [--json]
```

## Sample maintenance profile (balanced)

```json
{
  "profile_id": "balanced",
  "label": "Balanced maintenance",
  "description": "Moderate retention and summarization thresholds. Default for long-run use.",
  "policies": [
    {
      "subsystem_id": "background_run",
      "retain_days": 30,
      "max_items_before_summarize": 500,
      "summarization_kind": "summarize_only",
      "description": "Background run history: suggest summarization after 500 entries or 30 days."
    },
    {
      "subsystem_id": "automation_inbox",
      "retain_days": 14,
      "max_items_before_summarize": 200,
      "summarization_kind": "summarize_only",
      "description": "Automation inbox decisions: suggest summarization after 200 or 14 days."
    },
    {
      "subsystem_id": "event_log",
      "retain_days": 30,
      "max_items_before_summarize": 1000,
      "summarization_kind": "summarize_only",
      "description": "Event/timeline log: suggest summarization after 1000 or 30 days."
    }
  ]
}
```

## Sample compaction recommendation output

```
Compaction recommendations (profile: Balanced maintenance)
  No compaction targets above threshold. State is within profile limits.
```

With some history present:

```
Compaction recommendations (profile: Balanced maintenance)
  background_run (background_run_history): 120 item(s).
  automation_inbox (automation_inbox_decisions): 45 item(s).
  [review_only] background_run (background_run_history): 120 item(s).  → workflow-dataset background history (review); no auto-archival.
  [review_only] automation_inbox (automation_inbox_decisions): 45 item(s).  → workflow-dataset automation-inbox list (review); decisions kept for audit.
```

JSON (structure):

```json
{
  "generated_at_utc": "2025-03-17T20:00:00.000000Z",
  "profile_id": "balanced",
  "profile_label": "Balanced maintenance",
  "archival_targets": [
    {
      "subsystem_id": "background_run",
      "scope": "background_run_history",
      "path_or_location": "data/local/background_run/history.json",
      "item_count": 120,
      "oldest_utc": "2025-02-15T10:00:00Z",
      "retain_days_recommended": 30
    }
  ],
  "recommendations": [
    {
      "recommendation_id": "rec_...",
      "subsystem_id": "background_run",
      "scope": "background_run_history",
      "operator_summary": "background_run (background_run_history): 120 item(s).",
      "action_kind": "review_only",
      "item_count": 120,
      "suggested_command": "workflow-dataset background history (review); no auto-archival.",
      "safe_to_apply": true
    }
  ],
  "operator_summary_lines": ["background_run (background_run_history): 120 item(s)."]
}
```

## Tests run

```bash
pytest tests/test_state_durability.py -v
```

M37L.1 tests added:

- test_list_maintenance_profiles
- test_get_maintenance_profile_balanced
- test_build_compaction_recommendations_empty
- test_build_compaction_recommendations_with_profile_flag

## Next recommended step for this pane

- **Optional: persist active profile** — Store selected profile_id in `data/local/state_durability/active_maintenance_profile.txt` and use it by default in `state compaction-recommendations` when `--profile` is not set.
- **Optional: surface in mission control** — Add a short “maintenance” line to the state_durability block (e.g. “compaction: N targets, profile=balanced”) and/or a dedicated “run compaction-recommendations” hint when targets exceed threshold.
- **Later: safe archival implementation** — If desired, add an explicit `workflow-dataset state archive --subsystem background_run --dry-run` that writes to an archive dir (e.g. `data/local/state_durability/archive/`) only with user confirmation or a flag; keep recommendations read-only by default.
