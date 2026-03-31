# Repo Reality (Shot 1)

This repo is not a blank slate. The system already contains a broad local-first product substrate and an investor-facing desktop shell with live/cached/mock wiring.

## What is materially real (code-confirmed)
- **Local-first workflow engine** with session, packs, outcomes, and operator flows (`src/workflow_dataset/session`, `packs`, `outcomes`, `operator_mode`).
- **Approval/queue model** for supervised actions (`src/workflow_dataset/supervised_loop`).
- **Trust + governance + review domains** (`src/workflow_dataset/trust`, `governance`, `review_domains`, `sensitive_gates`).
- **Continuity + migration + stable‑v1 layers** (`continuity_*`, `migration_restore`, `stable_v1_gate`, `v1_contract`).
- **Investor demo CLI flow** (`src/workflow_dataset/investor_demo`, `investor_mission_control`, CLI commands in `cli.py`).
- **Demo USB bootstrap + readiness + env-report** (`src/workflow_dataset/demo_usb`).
- **Demo onboarding** (`src/workflow_dataset/demo_onboarding`).
- **Workspace home / day status / guidance / operator summary / inbox** (`workspace`, `workday`, `quality_guidance`, `review_studio`).
- **Edge Operator Desktop prototype** (UI, ambient, presenter overlay) in `investor-prototype/`.
- **Live adapter pipeline** with per-field provenance (`src/workflow_dataset/live_desktop_adapter`, `edge_desktop/fetchers.py`).
- **Dev server live API** for desktop snapshot in `investor-prototype/vite.config.ts`.
- **Packaging scripts + CI** (`investor-prototype/scripts/*`, `.github/workflows/investor-prototype-build.yml`).

## What is partial
- **Desktop “live” wiring is optional**: `EDGE_DESKTOP_USE_ADAPTER=1` enables adapter provenance; default path still uses `build_edge_desktop_snapshot`.
- **Boot readiness tiers are presentation-only** (explicitly marked mock in `investor-prototype/src/shell/models.ts`).
- **Workflow-tree formal model** is not represented as a first-class persisted tree; instead there are partial structures (workflow episodes, sessions, job packs, tasks).

## What is stale / duplicated
- **Parallel doc trees** exist (`docs/` and `Chatgpt_2/docs/`) that can drift.
- Multiple “deliverable” docs for the same areas (M52/M53 etc.) should not be treated as source of truth without code verification.

## What must not be rebuilt
- Core CLI and local-first runtime surfaces.
- Approval-gated trust model and auditability.
- Investor prototype UI shell and snapshot wiring.
- Existing demo flows (bootstrap/readiness/onboarding/workspace/day/guidance/inbox).

## Missing inputs from the prompt pack
- The Shot 1 prompt references `prompts/agent_os_pack/*`, but that directory does **not** exist in this repo. The equivalent prompt pack lives in `prompts/*.md` (00–13).
