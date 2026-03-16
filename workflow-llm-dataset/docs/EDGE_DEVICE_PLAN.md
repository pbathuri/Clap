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

---

## M23B-F2: Edge tiers, support matrix, and compare

Local deployment profiles (not hardware products): **dev_full**, **local_standard**, **constrained_edge**, **minimal_eval**.

### Commands

- `workflow-dataset edge profile --tier local_standard` — Profile summary for a tier (runtime, paths, workflow availability).
- `workflow-dataset edge matrix` — Workflow support matrix (all tiers or `--tier X`); includes required/optional dependencies and degraded section.
- `workflow-dataset edge compare --tier local_standard --tier-b constrained_edge` — Compare two tiers: workflow status diff, degraded workflows, path/dependency differences.
- `workflow-dataset edge degraded-report [--tier X]` — Report why workflows are partially supported, what is missing, and what fallback is available.
- `workflow-dataset edge package-report [--tier X]` — Packaging/readiness metadata for a tier (required/optional components, supported/degraded workflows, path and config assumptions). For operator handoff to deployment or appliance.
- `workflow-dataset edge smoke-check --tier X [--workflow W]` — Lightweight smoke check: readiness plus optional workflow demo runs. Reports pass/fail/skipped and degraded or missing-dependency reasons. Use `--no-demo` for readiness-only.

### Workflow support by tier

| Tier               | Workflows       | LLM    |
|--------------------|-----------------|--------|
| dev_full           | All supported   | Required |
| local_standard     | All supported   | Required |
| constrained_edge   | Degraded        | Optional |
| minimal_eval       | Unavailable     | None   |

Degraded workflows: reason, missing functionality, and fallback are in the matrix and in `edge degraded-report`. All outputs are written under `data/local/edge/` (local and inspectable).

### Operator guide and sample profiles

- **[EDGE_OPERATOR_GUIDE.md](EDGE_OPERATOR_GUIDE.md)** — How to run each command, read degraded output, and interpret missing dependencies.
- **[docs/edge/sample_profiles](edge/sample_profiles)** — Sample profile documents per tier (dev_full, local_standard, constrained_edge, minimal_eval) with example commands and outcomes.
