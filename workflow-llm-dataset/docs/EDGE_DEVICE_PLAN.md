# Edge Device Plan

## Target hardware

- **v1**: Raspberry Pi 5 + AI module (e.g. Hailo, Coral, or similar NPU/accelerator for local inference).
- **Later**: Stronger edge hardware (e.g. NUC, small-form-factor PC, or next-gen SBCs) for larger models and richer pipelines.

## Runtime components

| Component | Role |
|-----------|------|
| **Local model routing** | Route prompts to on-device model(s) by capability and hardware profile; fallback to smaller/faster model when resource-constrained. |
| **Model-size tiers** | Define small/medium/large profiles per hardware (e.g. Pi 5: small only; stronger edge: small + medium, optionally large). |
| **Structured local store** | SQLite or equivalent for personal work graph, approval rules, and audit log. |
| **Vector/embedding store** | Local embedding index for retrieval over tasks, documents, and workflow steps; no user data sent off-device for indexing by default. |
| **Event log storage** | Append-only or rotating log of observation events and agent actions for debugging and audit. |
| **Personal graph persistence** | Serialization of the personal work graph (projects, routines, preferences, workflows) to the structured store. |
| **Privacy boundaries** | Configurable: which observation sources are enabled; whether any data may leave the device; retention limits. |
| **Sync boundaries** | If sync is enabled: what is synced (e.g. graph only, no raw events); encrypted and user-controlled. |
| **Update mechanism** | Secure updates for device firmware and agent software; no user data in update payloads. |
| **Model/library download** | Pull models and workflow packs from a catalog over HTTPS; integrity checks; no user data in requests. |

## Constraints

- No assumption that the device has continuous internet access.
- Inference and learning run on-device; optional sync is explicit and bounded.
- All default configurations must keep user data on-device.
