# Roadmap: Personal Edge Agent

## 1. What already exists in the repo

### Dataset engine (global work priors)

- **Ingest**: Raw official (O*NET, ISIC, NAICS, SOC, BLS) and private examples → interim parquet; source register.
- **Normalize**: Taxonomies (industries, SOC), occupations (O*NET), enrichment (tasks, DWA, work context, tools, SKA), labor market (BLS Table 1.2).
- **Map**: Industry–occupation mapping from BLS matrix; O*NET-SOC to NEM crosswalk.
- **Infer**: Workflow steps from tasks/DWA (production); pain_points, kpis, automation are placeholders.
- **Validate**: QA issues (missing sources, provenance, duplicates, empty tables, unmapped codes).
- **Export**: Parquet, CSV, Excel (with Workflow_Steps and other sheets), QA report.

All of the above is **dataset-only**: it produces a prior knowledge base (industries, occupations, tasks, tools, workflow steps, labor market). It does not yet observe a user or run an agent.

### New scaffolding (no real behavior yet)

- **Observation**: `observe/` — event envelope, file/app/browser/terminal/calendar/teaching payloads and stubs; no OS integrations.
- **Personal**: `personal/` — work graph node types, profile builder, routine detector, preference model; no persistence.
- **Agent**: `agent/` — execution modes, action policy, audit log, sandbox runner; interfaces only.
- **Config**: `agent` section in settings (observation_enabled, execution_mode, etc.); new paths for event log, graph store, audit log.
- **Docs**: ARCHITECTURE_OVERVIEW, PERSONAL_AGENT_VISION, EDGE_DEVICE_PLAN, PRIVACY_AND_LOCAL_FIRST_MODEL, OBSERVATION_PHASES; schemas for personal graph, observation events, action log, execution modes.

---

## 2. What remains dataset-only

- Full KPI inference from workflow steps
- Full pain-point inference from task/workflow evidence
- Full automation candidacy classification
- Any ingestion beyond current O*NET/BLS/ISIC/NAICS/SOC
- Any export beyond current parquet/CSV/Excel/QA

These stay as future enhancements to the **global prior** pipeline; they do not require the personal agent to be running.

---

## 3. What is missing for the personal edge agent

- **Real observation collectors** for Tier 1 (file, app, browser, terminal, calendar, teaching) on at least one OS.
- **Event log persistence** and retention policy.
- **Personal work graph persistence** (e.g. SQLite) and graph builder from events + teaching.
- **Local model routing** and **vector store** for retrieval.
- **Simulated suggestion loop**: agent uses priors + graph to propose next steps; output to sandbox only.
- **User approval flow** for assist mode (per-action approve → execute on real system).
- **Automate mode** with approval boundaries (path/app allowlists).
- **Edge device deployment**: run on Raspberry Pi 5 + AI module; model-size tiers; secure updates and model/workflow-pack download without user-data leakage.

---

## 4. Path from dataset engine to edge prototype

```
[Dataset engine]  ← current: build produces workflow_steps + occupational priors
       ↓
[Observation Tier 1]  ← first local observer: file/app/browser/terminal/calendar/teaching collectors
       ↓
[Personal work graph]  ← persist events; build profile, projects, routines, workflows, preferences
       ↓
[Simulated suggestion loop]  ← agent (priors + graph) → proposals → sandbox only; no real changes
       ↓
[User-approved action loop]  ← assist mode: user approves → execute on real system within boundaries
       ↓
[Automate within boundaries]  ← automate mode: act within user-defined path/app/time rules
       ↓
[Edge device prototype]  ← Pi 5 + AI module; local model; vector store; updates; no user-data leak
```

---

## 5. Milestone plan

| Milestone | Description | Success criteria |
|-----------|-------------|-------------------|
| **M1 — First local observer** | At least one Tier 1 source (e.g. file metadata or app usage) producing events and writing to event log. | Events in local store; config toggles source on/off. |
| **M2 — First personal work graph** | Graph store (e.g. SQLite) with profile, projects, routines; updated from events + teaching. | Queryable graph; teaching updates profile or routines. |
| **M3 — First simulated suggestion loop** | Agent (using priors + graph) proposes next step; action runs in sandbox only; result shown to user. | No real system changes; user sees proposed action and sandbox result. |
| **M4 — First user-approved local action** | Assist mode: user approves one action → executed on real system; logged in audit log. | One real action (e.g. write file) after explicit approval; audit record. |
| **M5 — First edge-device prototype** | Run on Raspberry Pi 5 + AI module; local small model; vector store; workflow_steps/priors loaded; updates and model download without user data. | End-to-end on device; no cloud dependency for inference or learning. |

---

## 6. Out of scope for v1

- Cloud sync of user data
- Full KPI/pain-point/automation inference (remain as placeholders or later phases)
- Delegation mode
- Observation Tier 2–3 (email, clipboard, microphone) beyond schema/docs
- Cross-device or multi-user support
