# M31 — Local Observation Runtime + Consent Boundaries

First-draft observation runtime: bounded local sources, normalized event stream, consent/boundary enforcement, CLI, and mission-control visibility.

## What it is

- **Local-first, consent-bounded** observation: file, app, browser, terminal, calendar, teaching.
- **Source model** per source: allowed scope, consent, collection mode, redaction, retention, trust (see `observe/sources.py`).
- **Normalized event stream**: event_id, source, timestamp, activity_type, bounded metadata, project_hint, session_hint, redaction_marker, provenance (`observe/local_events.py`).
- **Boundary enforcement**: enabled/disabled per source, allowed scopes, observe_only vs rich_metadata, retention, source health/blocked (`observe/boundaries.py`, `observe/state.py`).
- **CLI**: `observe sources`, `observe enable --source file`, `observe status`, `observe recent`, `observe boundaries`, `observe health`, `observe run`.
- **Mission control**: observation slice in state and report; next recommended action when no sources enabled.

## What it is not

- No hidden telemetry, no cloud collection, no raw content capture.
- App/browser/terminal/calendar/teaching collectors are stubs; only file has a real collector.

## CLI usage

```bash
workflow-dataset observe sources
workflow-dataset observe enable --source file
workflow-dataset observe disable --source file
workflow-dataset observe status --config configs/settings.yaml
workflow-dataset observe recent --limit 20 [--source file]
workflow-dataset observe boundaries
workflow-dataset observe health
workflow-dataset observe run   # run file scan (when file enabled and root_paths set)
```

## Sample observation source definition (file)

- **source_id**: file  
- **display_name**: File and folder metadata  
- **allowed_scope**: Paths under `file_observer.root_paths`; exclude_dirs applied. No content read.  
- **consent_required**: true  
- **default_collection_mode**: observe_only  
- **redaction_rules**: None; metadata only (path, name, size, mtime).  
- **retention_days**: 90  
- **trust_notes**: Metadata only; no file body. Safe for local work graph.  
- **implemented**: true  

## Sample normalized event

```json
{
  "event_id": "evt_abc123",
  "source": "file",
  "timestamp_utc": "2025-03-16T12:00:00Z",
  "activity_type": "file_snapshot",
  "payload": { "path": "/work/x.txt", "filename": "x.txt", "event_kind": "snapshot", "provenance": "file_scan" },
  "project_hint": null,
  "session_hint": null,
  "redaction_marker": null,
  "provenance": "file_scan"
}
```

## Sample boundaries/consent report

From `observe boundaries`:

- **observation_enabled**: true  
- **enabled_sources**: ["file"]  
- **blocked_sources**: [{"source": "app", "reason": "blocked_not_allowed", "detail": "..."}, ...]  
- **stub_sources**: ["app", "browser", "terminal", "calendar", "teaching"]  
- **file_root_paths_configured**: true  
- **retention_by_source**: {"file": 90, "app": 30, ...}  

## Tests run

- `tests/test_observe_m31.py`: source registration, enable/disable, boundary enforcement, event normalization, blocked source, effective config, state file.
- `tests/test_observe_m1.py`: file metadata-only, event log, graph, CLI gating (uses `observe run`).

Run: `pytest workflow-llm-dataset/tests/test_observe_m31.py workflow-llm-dataset/tests/test_observe_m1.py -v`

## Remaining gaps (later refinement)

- Real collectors for app, browser, terminal, calendar, teaching (currently stubs).
- Retention enforcement (e.g. rotate/delete events older than retention_days).
- Scope validation at write time (e.g. reject events outside allowed paths).
- Optional project/session hint inference from path or context.
- Redaction implementation for terminal/browser when those collectors exist.
