# M37I–M37L — Durable State Persistence + Startup/Resume Performance

First-draft durability and performance hardening layer: state health, startup readiness, resume target, partial-state recovery, and long-run maintenance. All local and inspectable.

## What it does

1. **Persistence boundaries** — Explicit registry of subsystems (workday, continuity, project_case, background_run, etc.) and their paths; health check per boundary (ok | missing | stale | corrupt).
2. **Startup readiness** — Aggregate health checks, hydration order, degraded-but-usable flag, recommended first action.
3. **Resume target** — Single best resume target (label, command, quality) from workday + continuity + project.
4. **Recoverable partial state** — Report what is ok, missing, corrupt, stale; whether resume is possible in degraded mode; recommended recovery actions.
5. **Maintenance** — Stale cleanup report, reconcile report (suggested actions only; no blind writes), startup readiness summary.
6. **Optional snapshot** — Save/load durable state snapshot for fast path (e.g. last_known_good).
7. **Mission control** — State durability block: state_health_ready, resume_target, stale/corrupt warnings, recommended_recovery_action.

## CLI usage

```bash
# State health (persistence boundaries)
workflow-dataset state health [--repo PATH] [--json]

# Durable state snapshot (optionally --save to data/local/state_durability)
workflow-dataset state snapshot [--repo PATH] [--save] [--json]

# Reconcile report (suggested actions; no writes)
workflow-dataset state reconcile [--repo PATH] [--json]

# Startup readiness
workflow-dataset state startup-readiness [--repo PATH] [--json]

# Resume target (best first action from workday + continuity + project)
workflow-dataset state resume-target [--repo PATH] [--json]
```

## Sample state health report

```
State health (persistence boundaries)
  ready=True  degraded_but_usable=False
  All critical state is present and readable.
  [ok] workday  data/local/workday/state.json
  [missing] continuity_shutdown  data/local/continuity_engine/last_shutdown.json  File not found
  ...
```

## Sample startup-readiness output

```json
{
  "ready": true,
  "generated_at_utc": "2025-03-17T19:00:00.000000Z",
  "degraded_but_usable": false,
  "summary_lines": ["All critical state is present and readable."],
  "recommended_first_action": "workflow-dataset continuity morning",
  "boundaries": [
    {"subsystem_id": "workday", "path": "data/local/workday/state.json", "status": "ok", "last_write_utc": "..."}
  ]
}
```

## Sample resume-target output

```
Resume target: Run morning flow  quality=medium
  command: workflow-dataset continuity morning
  Workday state: resume_pending.
  Continuity: Run morning flow
```

JSON:

```json
{
  "label": "Run morning flow",
  "command": "workflow-dataset continuity morning",
  "quality": "medium",
  "rationale": ["Workday is resume_pending; good candidate for morning flow.", "Continuity: Run morning flow"],
  "project_id": "",
  "day_id": "2025-03-17"
}
```

## Data locations

- **State durability (optional snapshot):** `data/local/state_durability/last_snapshot.json`
- **Boundaries checked:** workday (`data/local/workday/state.json`), continuity_engine (`last_shutdown.json`, `carry_forward.json`, `next_session.json`), project_case (`current_project_id.json`), background_run (`queue.json`), workday preset (`active_preset.txt`).

## Tests run

```bash
pytest tests/test_state_durability.py -v
```

- test_collect_boundaries_empty_repo
- test_startup_readiness_returns_readiness
- test_resume_target_returns_target
- test_recoverable_partial_state
- test_stale_markers_empty_repo
- test_corrupt_notes_empty_repo
- test_durable_snapshot_build
- test_snapshot_save_load
- test_reconcile_report
- test_stale_cleanup_report
- test_startup_readiness_summary

## Remaining gaps for later refinement

- **Hydration order execution:** Hydration order is defined but not executed as a single “startup hydrate” step; callers still load subsystems on demand.
- **Automatic stale cleanup:** Only report; no automatic compaction or cleanup; operator can run continuity shutdown to refresh.
- **Corrupt recovery:** No automatic repair; recommended_recovery_action points to state health and manual restore.
- **Queue/timeline summarization:** No old queue or timeline summarization in this block; can be added to maintenance later.
- **Background/result compaction:** Not implemented; boundary checks only.
- **Full snapshot load:** load_snapshot does not fully reconstruct readiness (nested boundaries/corrupt/stale); only top-level and resume_target restored for fast path.
