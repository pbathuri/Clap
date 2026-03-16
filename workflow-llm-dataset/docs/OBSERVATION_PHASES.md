# Observation Phases

Observation is tiered by edge feasibility and privacy sensitivity. Higher tiers add more sources and/or richer semantics; they may require more compute or tighter privacy controls.

## Tier 1 — v1 edge-feasible

Suitable for Raspberry Pi 5 + AI module; minimal footprint and clear user value.

| Source | Description | Notes |
|--------|-------------|--------|
| **Files/folders metadata** | Paths, names, types, modification times; no content. | Avoid reading file bodies; metadata only. |
| **Document/spreadsheet access patterns** | Which files are opened/closed and when; app association. | No content; presence and timing only. |
| **App usage** | Foreground app, switch events, duration. | OS-level only; no in-app content. |
| **Browser tab/domain history** | Tab titles, URLs/domains, timing. | No page content or form data. |
| **Terminal history/commands** | Commands run in configured shells; optional redaction of secrets. | User can exclude paths or disable. |
| **Calendar metadata** | Event titles, times, attendees (if available); no body/content. | CalDAV or local calendar API. |
| **Manual user teaching** | User-provided labels, corrections, step-by-step instructions. | Explicit; highest trust. |

## Tier 2 — Richer semantics

Requires more integration and possibly more compute; defer until Tier 1 is stable.

| Source | Description |
|--------|-------------|
| Email metadata | From/to, subject, date; no body. |
| Communication metadata | Chat/app presence; no message content. |
| Clipboard patterns | Type and frequency; optional hashes for dedup; no raw content by default. |
| Richer app-level semantics | e.g. “spreadsheet cell range” or “document section” without content. |

## Tier 3 — Advanced

Not for v1; consider only after Tier 1–2 are proven and privacy controls are clear.

| Source | Description |
|--------|-------------|
| Microphone / voice-note transcripts | On-device STT only; no raw audio leave device. |
| Broader always-on contextual sensing | Environmental or cross-device signals. |
| Advanced cross-device observation | Multiple machines under same user control. |

## Implementation status

- **Tier 1**: Schema and module scaffolding only; no real OS integrations yet.
- **Tier 2–3**: Documented for roadmap; no implementation.

Config key: `observation_tier` (1 | 2 | 3); default `1`. When `observation_enabled` is false, no events are collected regardless of tier.
