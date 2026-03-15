# Agent Action Log Schema

## Purpose

The action log records every agent-proposed and agent-executed action for audit, debugging, and user review. It is stored only on-device and is never sent off-device unless the user explicitly exports or syncs it within defined boundaries.

## Record fields

| Field | Type | Description |
|-------|------|-------------|
| `log_id` | string | Stable unique ID (e.g. `log_*`). |
| `timestamp_utc` | string (ISO 8601) | When the action was proposed or executed. |
| `mode` | string | `observe` \| `simulate` \| `assist` \| `automate`. |
| `action_type` | string | e.g. `file_write`, `api_call`, `ui_action`, `suggestion_only`. |
| `intent` | string | Short human-readable description of what the agent intended. |
| `target` | string or object | Target of the action (path, app, etc.); structure depends on action_type. |
| `outcome` | string | `proposed` \| `approved` \| `rejected` \| `executed` \| `failed` \| `skipped`. |
| `details` | object | Optional; action-specific payload (e.g. diff summary, error message). |
| `approval_id` | string or null | If user approved, reference to approval record. |
| `user_override` | string or null | Optional user correction or note. |

## Lifecycle

1. **Proposed**: Agent suggests an action in `simulate` or `assist`; record with `outcome = proposed`.
2. **Approved/Rejected**: User approves or rejects; record updated or linked with `approval_id`.
3. **Executed/Failed**: Action runs (in assist/automate); record with `outcome = executed` or `failed`.
4. **Skipped**: User or policy skips the action; `outcome = skipped`.

## Retention and access

- Stored locally only; retention policy configurable (e.g. 1 year).
- User can export or delete; no automatic off-device transfer.

## v1

- Schema and scaffolding only; real logging when execution layer is implemented.
