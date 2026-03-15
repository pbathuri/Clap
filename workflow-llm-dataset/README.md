# Workflow LLM Dataset & Personal Agent Foundation

This repository is the **foundational intelligence layer** for a **local-first personal edge AI agent**: a plug-and-play device that learns from one user’s work environment and acts as a Jarvis-like desktop/work operator.

## Product vision

We are building a **personal work agent** that:

- Runs on a **physical edge device** (initial target: Raspberry Pi 5 + AI module; later stronger hardware)
- Connects to **one user’s** laptop/tools/data/workflows
- **Learns privately** from observation and explicit teaching
- Builds a **personal work memory graph** and a **task/workflow execution graph**
- Operates as a **desktop/work operator** with **safe simulated execution by default**
- Makes **no changes to the user’s real system** unless the user explicitly approves

**Principles:** Local-first, private-first, one-device-per-user, simulate-first, approval-gated local actions. Strongest-first verticals: **logistics**, **operations**, **founder workflows**, **office admin**.

## What this repo contains

### 1. Global work priors (dataset pipeline)

The existing **dataset build** produces occupational knowledge used as a **global prior** by the agent:

- Industries (ISIC, NAICS), occupations (O*NET-SOC), industry–occupation mapping
- Tasks, detailed work activities, work context, tools & technology, skills/knowledge/abilities
- Labor market data (BLS)
- **Workflow priors** (inferred workflow steps from tasks/DWA)
- Placeholders for KPI, pain-point, and automation priors

This is **not** the end product; it is the prior knowledge base that helps the device interpret what the user is doing. Outputs: parquet, CSV, Excel, QA report.

### 2. Personal agent scaffolding

- **Observation layer** (Tier 1–3): schema and modules for file, app, browser, terminal, calendar, and manual-teaching events — on-device only; no real collectors yet.
- **Personal work graph**: schema and modules for profile, projects, routines, workflows, preferences, approval boundaries — on-device only.
- **Agent execution layer**: execution modes (observe → simulate → assist → automate), action policy, audit log, sandbox runner — interfaces only; default mode **simulate**.

See **docs/** for architecture, vision, edge device plan, privacy model, and observation phases; **docs/schemas/** for personal graph, observation events, action log, and execution modes.

## Quick start (dataset build)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python scripts/bootstrap_data_dirs.py
python -m workflow_dataset.cli build --config configs/settings.yaml
```

**Outputs:** `outputs/parquet/`, `outputs/csv/`, `outputs/excel/workflow_llm_primary_dataset_v1.xlsx`, `outputs/qa/build_report.md`.

## Config

- **configs/settings.yaml** — project paths, runtime, and **agent** section (observation, privacy, sync, execution mode, hardware/model profile, sandbox). Defaults: observation off, sync off, **execution_mode: simulate**.

## Architecture summary

| Layer | Role |
|-------|------|
| **A — Global work priors** | Dataset pipeline (current `build`): industries, occupations, tasks, DWAs, tools, workflow steps, labor market. |
| **B — Personal observation** | Local event capture (file, app, browser, terminal, calendar, teaching); phased by edge feasibility. |
| **C — Personal work graph** | Device-local graph: profile, projects, routines, workflows, preferences, approval boundaries. |
| **D — Agent execution** | Modes: observe, simulate, assist, automate. Default simulate; no local changes without approval. |
| **E — Device runtime** | Edge device, local model routing, vector store, event/graph persistence, privacy/sync boundaries, updates. |

## Roadmap

See **docs/ROADMAP_PERSONAL_AGENT.md** for:

- What exists today (dataset engine, scaffolding)
- Path from dataset → observation → personal graph → simulated assistant → approved-action agent → edge prototype
- Milestones: first local observer, first personal graph, first simulated suggestion loop, first approved action loop, first edge-device prototype

## Constraints

- **No cloud-first assumption** for learning or inference by default.
- **No agent autonomy on the real machine** by default; simulate first, approve then execute.
- The **dataset pipeline is preserved**; ingestion, normalization, mapping, exports, and QA are unchanged.
- Package name remains **workflow_dataset**; no broad rename.

## License and provenance

Primary-source-first; every row retains source_id. See methodology in the Excel README sheet and **docs/**.
