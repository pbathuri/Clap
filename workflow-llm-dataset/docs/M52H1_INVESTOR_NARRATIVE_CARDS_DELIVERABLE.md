# M52H.1 — Investor Narrative Cards + First-30-Seconds Optimization

Extends M52E–M52H without rebuilding the workspace layer.

## 1. Files modified
- `src/workflow_dataset/investor_mission_control/models.py` — `Hero30Surface`, `RolePreviewCard`, `RoleSwitchPreviewState`, `NextStepCard`; memory `narrative_intro` / `insight_lines`; first-value `subcopy_tight`, `next_step_*`; home aggregates + `narrative_flow_steps`.
- `src/workflow_dataset/investor_mission_control/build.py` — populates M52H.1 fields (fixed duplicate `FirstValueSurface` assignment).
- `src/workflow_dataset/investor_mission_control/render.py` — default layout is first-30s forward; added `format_investor_mission_control_home_classic`, `format_first_30_only`.
- `src/workflow_dataset/investor_mission_control/__init__.py` — exports classic + first30 formatters.
- `src/workflow_dataset/cli.py` — `demo mission-control-home --first30-only`, `--classic`.
- `tests/test_investor_mission_control.py` — fixture updated for new layout.

## 2. Files created
- `src/workflow_dataset/investor_mission_control/narrative_m52h1.py` — hero copy, memory story, role previews, next-step pairing, investor flow lines.
- `tests/test_investor_mission_control_m52h1.py`
- `docs/M52H1_INVESTOR_NARRATIVE_CARDS_DELIVERABLE.md`

## 3. First-30-seconds improvements
| Before | After |
|--------|--------|
| Generic operator header | **FIRST LOOK** + eyebrow (LOCAL · PRIVATE · READY/SETUP) |
| Device line first | **Hero headline** (“shell is live” vs “almost there”) + trust chip |
| Single CTA block | **YOUR NEXT MOVE** (tight subcopy) + **THEN** (ready-state command) |
| Role buried | **Other roles** with one-line hooks + exact switch commands |
| “Context signal:” bullets | **What it learned** narrative intro + prose insight lines |
| Long why paragraph | **subcopy_tight** (≤100 chars) in primary card |

## 4. Updated investor narrative flow
Printed as **Investor flow** section:
- **Ready:** glance hero → optional role switch → run first move → ready-state → trust note.
- **Not ready:** onboarding sequence → role + memory → return for hero + first move.

## 5. Exact tests run
```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_investor_mission_control.py tests/test_investor_mission_control_m52h1.py -v --tb=short
```

## 6. Next recommended step for the pane
Wire **Edge Operator Desktop** to render `hero_30` + `first_value` + `next_step_card` as three docked tiles; bind **--first30-only** output to presenter “confidence monitor” second display.
