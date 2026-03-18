# M33 Integration Pane Report — Three-Pane Safe Integration

Integration of:
1. **Pane 1 (M33A–M33D + M33D.1)** — Workflow Episode Tracker + Cross-App Context Bridge  
2. **Pane 2 (M33E–M33H + M33H.1)** — Supervised Real-Time Workflow Runner + Assist Escalation  
3. **Pane 3 (M33I–M33L + M33L.1)** — In-Flow Review Studio + Draft / Handoff Composer  

Merge order applied: **1 → 2 → 3** (episode contract first, then real-time assistance, then review/draft/handoff).

---

## 1. Merge steps executed

The codebase (branch `feat/ops-product-next-integration`) already contains all three panes in a single tree; no separate feature branches existed to merge. Integration was **verified and documented** as follows.

| Step | Action | Result |
|------|--------|--------|
| 1 | **Pane 1 block** | Verified present: `observe`, `live-context`, `workflow-episodes` (CLI); `workflow_episodes/`, `live_context/` packages; mission_control pulls workflow_episodes. |
| 2 | **Pane 2 block** | Verified present: `live-workflow` (now, steps, escalate, preview-next, bundles, stall, explain-escalation); `assist` (now, queue, explain-suggestion, accept, snooze, dismiss, policy-status, suggest, draft, explain, next-step, refine-draft, chat, materialize, apply-plan, apply, rollback, generate-*, bundle-*, list-bundles); mission_control pulls live_workflow_state and assist_engine. |
| 3 | **Pane 3 block** | Verified present: `drafts` (list, apply-bundle), `handoffs` (create, show, set-readiness, nav-links), `in-flow` (bundles, kits); mission_control pulls in_flow (drafts, handoffs, checkpoints). |

**Design choices preserved:** additive command groups, local-first data paths, no hidden execution or hidden content generation, trust/review boundaries unchanged.

---

## 2. Files with conflicts (hotspots)

No **git merge conflicts** were resolved (single-branch state). The following files are **conflict hotspots** if merging from separate branches in the future; current state is consistent.

| File | Hotspot reason | Current resolution |
|------|----------------|--------------------|
| `src/workflow_dataset/cli.py` | All three panes add typer groups and commands. | Additive: `observe` → `live-context` → `workflow-episodes` → `automations` → `live-workflow` → (workflow_episodes commands) → … → `assist` → `drafts` → `handoffs` → `in-flow`. No duplicate command names. |
| `src/workflow_dataset/mission_control/state.py` | Aggregates workflow_episodes, live_workflow, assist_engine, in_flow. | Imports and sections for each pane; `workflow_episodes`, `live_workflow_state`, `assist_engine`, `in_flow` keys in state; errors isolated per section. |
| `src/workflow_dataset/mission_control/report.py` | Formats state from all panes. | Reads `assist_engine`, `in_flow`, `workflow_episodes`, `live_workflow_state` from state dict; no overlap. |
| `observe/*`, `live_context/*`, `workflow_episodes/*` | Pane 1. | No cross-edits with Pane 2/3 in same files. |
| `live_workflow/*`, `assist_engine/*`, `action_cards/*` | Pane 2. | `action_cards/builder.py` imports assist_engine; live_workflow standalone. |
| `in_flow/*`, `review_studio/*` | Pane 3. | in_flow is self-contained; review_studio separate. |
| `trust/*`, `human_policy/*`, `approvals/*` | Policy/approval boundaries. | Not weakened; assist policy and approval flows remain gated. |

---

## 3. How each conflict was resolved

- **cli.py:** Additive only. New groups: `workflow_episodes_group`, `live_workflow_group`, `assist_group`, `drafts_group`, `handoffs_group`, `in_flow_group`. Commands use distinct names (e.g. `live-workflow bundles` vs `in-flow bundles`).
- **mission_control/state.py:** Each pane is a separate block in `get_mission_control_state()` with try/except; one pane’s failure does not remove others. `local_sources` and section keys are distinct (`workflow_episodes`, `live_workflow`, `assist_engine`, `in_flow`).
- **Naming:** “bundles” appears in two senses: **live-workflow** bundles (workflow templates) and **in-flow** bundles (review checklists). Kept both; CLI disambiguates by group (`live-workflow bundles`, `in-flow bundles`).

---

## 4. Tests run after each merge

**Environment note:** Full pane tests for workflow_episodes, live_context, live_workflow, assist_engine require a venv with project deps (e.g. `pydantic`). The following was run in a minimal env.

| Merge / validation | Tests run | Result |
|--------------------|-----------|--------|
| After Pane 1+2+3 (unified validation) | `tests/test_in_flow.py` (19) + `tests/test_mission_control.py` (9) | **28 passed** |
| Same | `tests/test_workflow_episodes.py`, `test_live_context.py`, `test_live_workflow.py`, `test_assist_engine.py`, `test_assist_engine_policy.py` | **Collection errors** without project venv (missing `pydantic`) |

**Exact command used for passing slice:**
```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_in_flow.py tests/test_mission_control.py -v --tb=short
```

**Recommended full slice (with venv):**
```bash
pip install -e ".[dev]"   # or: pip install pydantic pyyaml ...
pytest tests/test_workflow_episodes.py tests/test_live_context.py tests/test_live_workflow.py tests/test_in_flow.py tests/test_mission_control.py tests/test_assist_engine.py tests/test_assist_engine_policy.py -v
```

---

## 5. Final integrated command surface

| Group | Commands | Pane |
|-------|----------|------|
| **observe** | sources, enable, disable, status, recent, boundaries, health, profiles, retention-policy, run | Pre-M33 |
| **live-context** | now, explain, recent, session-state | Pane 1 |
| **workflow-episodes** | now, recent, explain, stage, transition-map | Pane 1 |
| **automations** | (group present) | Other |
| **live-workflow** | now, steps, escalate, preview-next, bundles, stall, explain-escalation | Pane 2 |
| **assist** | now, queue, explain-suggestion, accept, snooze, dismiss, policy-status, suggest, draft, explain, next-step, refine-draft, chat, materialize, preview, list-workspaces, apply-plan, apply, rollback, apply-preview, generate-plan, generate-preview, list-generations, generate-run, list-generation-backends, generate-review, generate-refine, generate-adopt, generate-compare, bundle-create, bundle-preview, bundle-adopt, list-bundles | Pane 2 |
| **drafts** | list, apply-bundle | Pane 3 |
| **handoffs** | create, show, set-readiness, nav-links | Pane 3 |
| **in-flow** | bundles, kits | Pane 3 |
| **mission-control** (app command) | mission-control | Aggregates all panes |

CLI registration order in code: observe → live-context → workflow-episodes → automations → live-workflow → (workflow-episodes commands) → … → assist → drafts → handoffs → in-flow.

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| **Two “bundles” concepts** (live-workflow vs in-flow) | Document and keep CLI group names distinct; avoid overloading “bundle” in one command. |
| **Tests require full deps** | Run integration tests in CI with `pip install -e ".[dev]"`; document in README/contrib. |
| **mission_control state size** | Many optional sections; consider lazy-loading or caching if state build becomes slow. |
| **Cross-pane handoff from live-workflow to in-flow** | Escalation/handoff from live_workflow can point to planner/executor; linking to in_flow handoffs (e.g. “create handoff from kit” from a stalled step) is not yet wired in CLI. |
| **yaml import at cli top-level** | `cli.py` does `import yaml` at top level; environments without pyyaml fail at import. Optional: lazy-import where yaml is used. |

---

## 7. Exact recommendation for the next batch

1. **CI:** Add a job that runs the full pane test slice with project deps installed (`pip install -e ".[dev]"`), including `test_workflow_episodes`, `test_live_context`, `test_live_workflow`, `test_in_flow`, `test_mission_control`, `test_assist_engine`, `test_assist_engine_policy`.
2. **Wire live-workflow → in-flow:** From `live-workflow escalate` or `stall`, add an option or follow-up to create an in-flow handoff (e.g. “handoff create --kit blocked_escalation”) and optionally set readiness.
3. **Docs:** Add a short “M33 stack” doc that lists: workflow-episodes (contract), live-workflow (supervised run + escalate), assist (suggestions + policy), in-flow (drafts/handoffs/readiness), and mission_control (aggregated state/report).
4. **Optional:** Lazy-import `yaml` in `cli.py` where used so CLI loads even when pyyaml is missing (with a clear error at first use of a command that needs it).
