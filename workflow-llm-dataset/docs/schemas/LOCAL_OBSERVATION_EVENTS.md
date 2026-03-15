# Local Observation Events Schema

## Purpose

Observation events are immutable, device-local records of what was observed (files, apps, browser, terminal, calendar, manual teaching). They feed the personal work graph and the audit log. They are never sent off-device unless the user explicitly enables sync and then only within defined sync boundaries.

## Event envelope (common fields)

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Stable unique ID (e.g. `evt_*`). |
| `source` | string | One of: `file` \| `app` \| `browser` \| `terminal` \| `calendar` \| `teaching`. |
| `timestamp_utc` | string (ISO 8601) | When the event was observed. |
| `device_id` | string | Device that produced the event (for multi-device later). |
| `tier` | int | Observation tier (1, 2, or 3). |
| `payload` | object | Source-specific payload; see below. |

## Payloads by source (Tier 1)

### file

- `path`: string (path or hash if sensitive).
- `name`: string (basename).
- `kind`: `file` \| `directory`.
- `mtime_utc`: string (ISO 8601) or null.
- `action`: `created` \| `modified` \| `deleted` \| `opened` \| `closed`.
- No file content.

### app

- `app_id` or `bundle_id`: string.
- `app_name`: string.
- `action`: `foreground` \| `background` \| `quit`.
- `duration_seconds`: optional number.

### browser

- `tab_id`: string (opaque).
- `url`: string (optional; can be domain-only for privacy).
- `title`: string (optional).
- `action`: `opened` \| `closed` \| `activated`.
- No page body or form data.

### terminal

- `session_id`: string.
- `command`: string (user-configurable redaction).
- `cwd`: string (optional; can be redacted).
- `exit_code`: optional int.

### calendar

- `event_id`: string.
- `title`: string.
- `start_utc`, `end_utc`: string (ISO 8601).
- `attendees`: array of strings (optional).
- No body/description.

### teaching

- `instruction_type`: `demonstration` \| `correction` \| `label` \| `freeform`.
- `content`: string or structured (e.g. steps).
- `target_entity_id`: optional (e.g. workflow_step_id).

## Storage

- Append-only or rotating event log on device.
- Optional retention policy (e.g. keep 90 days of raw events; aggregate into graph and then drop).
- Indexing by source and time for graph builder and audit.

## v1 vs later

- v1: Schema and scaffolding only; no real event producers.
- Later: Real collectors per source; optional compression and aggregation.
