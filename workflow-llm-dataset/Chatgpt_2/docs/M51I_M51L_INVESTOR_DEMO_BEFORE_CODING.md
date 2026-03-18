# M51I–M51L — Investor Demo Flow + Mission-Control Presentation Mode: Before Coding

## 1. What mission-control and guidance surfaces already exist

- **Mission control** (`mission_control/state.py`, `report.py`): Aggregates product_state, evaluation_state, continuity_engine_state, operator_mode_state, supervised_loop, supervisory_control, vertical_excellence_slice, trust cockpit, queue, deploy_bundle, stable_v1_gate_state, v1_ops, etc. `format_mission_control_report` prints a long multi-section report. `recommend_next_action` suggests build/benchmark/hold/etc.
- **Vertical excellence** (`vertical_excellence/`): `vertical_excellence_slice` — first-value stage, friction, `recommend_next_for_vertical`, chosen vertical. `assess_first_value_stage`, path progress from vertical_packs.
- **Guided value / launch** (`vertical_paths`, `launch-kit`, `value-packs`, `guided-value-path`): Curated paths and launch kits for vertical onboarding.
- **Day / workspace / queue**: Day presets, workspace shell, queue state in mission_control.
- **Continuity**: `continuity_engine_state` in mission_control (start_of_day, carry_forward, resume).
- **Action cards** (`action_cards/`): `ActionCard`, `build_preview` — simulate-only / approval flows, handoff targets; no fake execution.
- **Operator mode / supervised loop**: Mission-control slices for pending approvals, next proposed action.
- **Quality guidance** (`quality_guidance/`): Next action with signals.
- **Production cut / vertical**: Chosen vertical, scope freeze.

## 2. What can be reused for a presentation-safe demo mode

- **Mission control state** as read-only source for device/product/continuity/operator posture (subset only).
- **vertical_excellence_slice** + **assess_first_value_stage** for first-value narrative and evidence.
- **action_cards.preview.build_preview** on a deterministic demo card (SIMULATE_ONLY or PREFILL_COMMAND) for supervised demonstration.
- **Env health** (`validation.env_health.check_environment_health`) for startup readiness line.
- **Continuity carry_forward / resume** for “system remembers context” storytelling (grounded strings).
- **Supervised loop** `next_proposed_action_label` when present for “what would be next with approval.”

## 3. What is missing for a strong investor walkthrough

- **Single narrative spine**: No linear stage model (readiness → role → memory → value → supervised close) tailored for presenters.
- **Presentation-filtered mission control**: Full MC report is too broad; need a **demo panel** with 6–8 lines, not 50.
- **Deterministic first-value artifact for demo**: A small, explainable artifact (summary doc) derived from real state, not a random LLM output.
- **Explicit degraded-demo warnings**: Surfacing when env/readiness is degraded without hiding uncertainty.
- **CLI demo session**: Start/stage/first-value/supervised-action/mission-control in one flow.
- **Presenter guidance**: Talking points per stage, stored as data not ad hoc.

## 4. Exact file plan

| Path | Purpose |
|------|--------|
| `docs/M51I_M51L_INVESTOR_DEMO_BEFORE_CODING.md` | This document. |
| `src/workflow_dataset/investor_demo/models.py` | Session, stages, panel, supervised demo, degraded warning, presenter note, completion. |
| `src/workflow_dataset/investor_demo/narrative.py` | Stage order, presenter guidance per stage. |
| `src/workflow_dataset/investor_demo/session_store.py` | Start session, advance stage, persist `data/local/investor_demo/session.json`. |
| `src/workflow_dataset/investor_demo/presentation_mc.py` | Build demo mission-control panel from repo state. |
| `src/workflow_dataset/investor_demo/first_value.py` | First-value demo path + artifact text + rationale. |
| `src/workflow_dataset/investor_demo/supervised.py` | Demo supervised action card + preview + approval-next line. |
| `src/workflow_dataset/investor_demo/degraded.py` | Collect degraded warnings from env + optional slices. |
| `src/workflow_dataset/investor_demo/__init__.py` | Exports. |
| `src/workflow_dataset/cli.py` | `demo` Typer group: session start/stage/first-value/supervised-action/mission-control, `investor-sequence`. |
| `tests/test_investor_demo.py` | Session, stages, artifact, supervised, degraded, completion. |
| `docs/samples/M51_investor_demo_mission_control.txt` | Sample presentation output. |
| `docs/samples/M51_investor_demo_first_value_artifact.md` | Sample artifact. |
| `docs/samples/M51_investor_demo_supervised_action.json` | Sample supervised demo JSON. |
| `docs/M51I_M51L_INVESTOR_DEMO_REMAINING_GAPS.md` | Gaps before live demo. |

## 5. Safety/risk note

- Demo mode is **read-only** except session JSON under `data/local/investor_demo/`. No auto-execution; supervised action uses **simulate-only** or **prefill** preview.
- **Degraded state must be shown** explicitly (env failures, missing vertical, blocked first-value) — never imply “all green” when evidence says otherwise.
- Presenter is responsible for not overstating capabilities; copy emphasizes **local-first**, **supervised**, **approval**.

## 6. Demo-storytelling principles

- **Narrow path**: One vertical, one role pack id, one supervised story — no feature browser.
- **Grounded claims**: Every bullet traceable to mission-control or vertical_excellence data.
- **Progressive disclosure**: Stages unlock narrative; closing ties back to mission-control summary.
- **Credible investor arc**: Readiness → onboarding → memory/context → first value → safe assist → summary.

## 7. What this block will NOT do

- No marketing slide deck, no broad UI redesign, no fake staged outcomes disconnected from state.
- No exposure of every subsystem; no branching tree of demos.
- No removal of supervision/review posture for impressiveness.
- No LLM-generated investor copy as primary artifact (deterministic template + state snippets only).
