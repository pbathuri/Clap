# Architecture Overview

This document describes the layered architecture for the personal edge work-agent foundation. The system is **local-first and privacy-first**: raw user learning stays on-device unless the user explicitly authorizes sync.

## Layer summary

| Layer | Purpose | Status |
|-------|---------|--------|
| **A — Global Work Priors** | Occupational dataset: industries, occupations, tasks, DWAs, tools, workflow/KPI/automation priors. Used to interpret what the user is doing. | Implemented (dataset pipeline). |
| **B — Personal Observation** | Local-first capture of file, app, browser, terminal, calendar, and manual-teaching events. Phased by edge feasibility. | Schema + scaffolding only. |
| **C — Personal Work Graph** | Private graph: profile, projects, routines, workflows, preferences, approval boundaries, device-local memory. | Schema + scaffolding only. |
| **D — Agent Execution** | Modes: observe → simulate → assist → automate. Default is **simulate** (no changes to real system without approval). | Schema + scaffolding only. |
| **E — Device Runtime** | Edge device (e.g. Raspberry Pi 5 + AI module), local model routing, vector store, event log, privacy/sync boundaries, safe updates. | Design only. |

## Data flow (target state)

1. **Global priors** are built offline (current `build` pipeline) and loaded onto the device as read-only reference.
2. **Observation** produces event streams that never leave the device unless the user enables sync.
3. **Personal graph** is updated from observations and explicit teaching; stored only in the local structured/vector store.
4. **Agent** consumes priors + personal graph to propose actions; execution is gated by the active mode (observe/simulate/assist/automate).
5. **Runtime** hosts models, stores, and the execution sandbox; enforces privacy and sync boundaries.

## Principles

- **One device per user** in the primary deployment model.
- **Simulate first**: the agent proposes and demonstrates in a sandbox; real local changes require explicit user approval.
- **No cloud assumption** for learning or inference by default; optional sync is opt-in and bounded.
- **Strongest-first verticals**: logistics, operations, founder workflows, office admin; extensible later.

## References

- [Personal Agent Vision](PERSONAL_AGENT_VISION.md) — product vision and constraints.
- [Edge Device Plan](EDGE_DEVICE_PLAN.md) — hardware, model tiers, storage, updates.
- [Privacy and Local-First Model](PRIVACY_AND_LOCAL_FIRST_MODEL.md) — data residency and sync rules.
- [Observation Phases](OBSERVATION_PHASES.md) — tiered observation capabilities.
