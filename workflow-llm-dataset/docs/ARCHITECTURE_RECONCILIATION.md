# Architecture Reconciliation (Shot 1)

This report reconciles the prompt pack with actual repo state.

## What is real (code-grounded)
- **Local-first engine + supervised execution**: `supervised_loop`, `trust`, `governance`, `review_domains`.
- **Investor demo CLI**: `investor_demo/*` and CLI commands in `cli.py`.
- **Demo USB bootstrap & onboarding**: `demo_usb`, `demo_onboarding`.
- **Workspace/day/guidance/inbox**: `workspace`, `workday`, `quality_guidance`, `review_studio`.
- **Edge Operator Desktop UI**: `investor-prototype/src/components/*`, ambient UI and presenter overlay.
- **Edge Desktop snapshot + live adapter**: `edge_desktop/snapshot.py`, `edge_desktop/fetchers.py`, `live_desktop_adapter/*`.
- **Dev API wiring**: `investor-prototype/vite.config.ts` (now supports adapter mode).

## What is partial
- **Workflow-tree as a unified persisted tree** is not implemented; models are fragmented (sessions, workflow episodes, inferred steps, job packs).
- **Boot readiness tiers** are still presentation-only in the UI.
- **Production live API** is not present; deploy uses prebaked JSON.

## What is stale / duplicated
- `Chatgpt_2/*` duplicates docs and some code, increasing drift risk.
- Multiple deliverable docs cover the same milestones; code should remain the source of truth.
- The Shot 1 prompt refers to `prompts/agent_os_pack/*`, but only `prompts/*.md` exists.

## Mock vs live vs cached (truth)
- **Live**: adapter pipeline with per-field provenance when enabled.
- **Cached**: sessionStorage in UI, last_good_snapshot in adapter pipeline.
- **Fallback**: static JSON or mock payloads.

## Top risks
1. **Integration drift** between snapshot builder and live adapter pipeline.
2. **Deployment gap**: dev API is not productionized; static deploy requires prebaked JSON.
3. **Presenter latency** on cold live load.
4. **Architecture drift** from duplicated docs and milestone reports.
5. **Missing workflow-tree substrate** as a single persisted model.

## Highest‑leverage next build step
**Post‑build hardening pass** to validate Edge Desktop integration end‑to‑end and lock a deterministic validation path (CLI + dev API + packaging), without expanding scope.
