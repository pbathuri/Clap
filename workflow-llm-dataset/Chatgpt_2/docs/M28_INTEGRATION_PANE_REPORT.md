# M28 Integration Pane Report — Portfolio, Lanes, Human Policy

Integration of three M28 blocks in specified merge order. All three blocks were present in the same working tree; integration was performed as **merge-order alignment** (mission_control state/report order), **conflict check**, and **full test slice**. No file conflicts requiring resolution; one intentional reorder applied.

---

## 1. Merge steps executed

| Step | Block | Action |
|------|--------|--------|
| **1** | **Pane 1** — M28A–M28D (+ M28D.1) Portfolio Router + Project Scheduler | Verified present: `portfolio/*` (models, store, scheduler, reports, attention, cli); CLI `portfolio list|status|rank|next|explain|stalled|blocked|attention|work-window|should-switch|start-window`; mission_control `portfolio_router` (priority_stack, next_recommended_project, health, etc.). No code merge; already in tree. |
| **2** | **Pane 3** — M28E–M28H (+ M28H.1) Bounded Worker Lanes + Delegated Subplans | Verified present: `lanes/*` (models, store, execution, bundles, review, subplan); CLI `lanes list|bundles|create|status|simulate|results|handoff|close`; mission_control `worker_lanes` (active_lanes, next_handoff_needed, etc.). No code merge; already in tree. |
| **3** | **Pane 2** — M28I–M28L (+ M28L.1) Human Policy Engine + Override Board | Verified present: `human_policy/*` (models, store, evaluate, board, presets, cli); CLI `policy show|evaluate|override|revoke|board|explain-blocked|explain-allowed|presets|apply-preset|trust-mode`; mission_control `human_policy` (active_restrictions_count, override_ids, etc.). No code merge; already in tree. |
| **4** | **Integration** | Reordered mission_control state aggregation and report output to match merge order: **Portfolio (Pane 1) → Lanes (Pane 3) → Human policy (Pane 2)**. Rationale: routing first, then delegation, then policy governing both. |
| **5** | **Validation** | Ran full test slice: **112 passed** (project_case 14, supervised_loop 21, progress_replan 14, portfolio 18, lanes 16, review_lanes 9, human_policy 14, mission_control 9). |

---

## 2. Files with conflicts

**None.** No git merge conflicts. No duplicate CLI command names; no overlapping state keys in mission_control.

- **cli.py**: Separate groups — `portfolio` (name="portfolio"), `lanes` (name="lanes"), `policy` (name="policy"). No name clash.
- **mission_control/state.py**: Distinct keys — `portfolio_router`, `worker_lanes`, `human_policy`. Order was changed to match merge order (see below).
- **mission_control/report.py**: Section order updated to [Portfolio] → [Worker lanes] → [Human policy].

---

## 3. How each conflict was resolved

- **State/report order**: The only change was **intentional reorder**. State aggregation and report sections were originally: human_policy → portfolio_router → worker_lanes. They were reordered to: **portfolio_router → worker_lanes → human_policy** so that (1) portfolio routing is computed first, (2) lanes (delegation) second, (3) human policy (governance) third. This reflects the merge rationale: routing and policy define context before delegation; display order is consistent with that.

- **No other conflicts**: No overlapping command names, no shared state keys, no incompatible imports. Lanes use `project_id` from project_case; human_policy uses `project_id` for scoped overrides; portfolio uses project_case `list_projects`. All additive.

---

## 4. Tests run after each merge

Single run after reorder (all three panes already in tree; no per-pane branches):

```bash
pytest tests/test_project_case_m27.py tests/test_supervised_loop.py tests/test_progress_replan.py \
  tests/test_portfolio_m28.py tests/test_lanes.py tests/test_review_lanes.py \
  tests/test_human_policy.py tests/test_mission_control.py -v --tb=line
```

**Result: 112 passed.**

| Suite | Count |
|-------|--------|
| test_project_case_m27 | 14 |
| test_supervised_loop | 21 |
| test_progress_replan | 14 |
| test_portfolio_m28 | 18 |
| test_lanes | 16 |
| test_review_lanes | 9 |
| test_human_policy | 14 |
| test_mission_control | 9 |

---

## 5. Final integrated command surface

**Portfolio (Pane 1)**  
`workflow-dataset portfolio list` [--repo-root]  
`workflow-dataset portfolio status` [--repo-root]  
`workflow-dataset portfolio rank` [--repo-root]  
`workflow-dataset portfolio next` [--repo-root]  
`workflow-dataset portfolio explain --project <id>` [--repo-root]  
`workflow-dataset portfolio stalled` [--repo-root]  
`workflow-dataset portfolio blocked` [--repo-root]  
`workflow-dataset portfolio attention` [--repo-root]  
`workflow-dataset portfolio work-window` [--project <id>] [--repo-root]  
`workflow-dataset portfolio should-switch` [--project <id>] [--repo-root]  
`workflow-dataset portfolio start-window` [--repo-root]

**Lanes (Pane 3)**  
`workflow-dataset lanes list` [--project] [--status] [--limit] [--repo-root]  
`workflow-dataset lanes bundles` [--repo-root]  
`workflow-dataset lanes create --project <id> --goal <id>` [--scope] [--repo-root]  
`workflow-dataset lanes status --id <lane_id>` [--repo-root]  
`workflow-dataset lanes simulate --id <lane_id>` [--repo-root]  
`workflow-dataset lanes results --id <lane_id>` [--repo-root]  
`workflow-dataset lanes handoff --id <lane_id>` [--repo-root]  
`workflow-dataset lanes close --id <lane_id>` [--repo-root]

**Human policy (Pane 2)**  
`workflow-dataset policy show` [--repo-root]  
`workflow-dataset policy evaluate --action <action_class>` [--project] [--pack] [--repo-root]  
`workflow-dataset policy override --scope <scope> --id <id> --rule <rule> --value <value>` [--reason] [--expires] [--repo-root]  
`workflow-dataset policy revoke --id <override_id>` [--repo-root]  
`workflow-dataset policy board` [--project] [--pack] [--repo-root]  
`workflow-dataset policy explain-blocked --action <action>` [--project] [--pack] [--repo-root]  
`workflow-dataset policy explain-allowed --action <action>` [--project] [--pack] [--repo-root]  
`workflow-dataset policy presets` [--repo-root]  
`workflow-dataset policy apply-preset --name <preset_id>` [--repo-root]  
`workflow-dataset policy trust-mode` [--preset] [--repo-root]

**Mission control**  
`workflow-dataset mission-control` includes, in order: [Portfolio], [Worker lanes], [Human policy]; state keys `portfolio_router`, `worker_lanes`, `human_policy` are populated in that order.

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| **Lane creation without portfolio next** | Lanes are created with explicit `--project` / `--goal`. Optional later: default `lanes create --project` to `portfolio next` when `--project` omitted. |
| **Policy and lanes** | Delegation (lanes) should respect human_policy (e.g. may_delegate, simulate_only). Ensure lane execution and handoff call policy evaluate where applicable; document expected usage. |
| **Two “project” notions** | Portfolio and progress board both use project ids; project_case is source of truth for projects. Already documented in M27/M28 docs. |
| **Report section order** | Fixed to Portfolio → Lanes → Policy; change only via this integration report. |

---

## 7. Exact recommendation for the next batch

1. **Wire portfolio next to agent-loop and lanes**: When `agent-loop next` or `lanes create` is run without `--project`, optionally use `portfolio next` recommended project so routing drives the loop and delegation.
2. **Policy–lane integration**: In lane execution/handoff, call human_policy evaluate for the delegated action (e.g. execute_trusted_real / lane_simulate) and block or warn when policy disallows; keep behavior explicit and operator-readable.
3. **E2E test**: One test that runs portfolio rank → portfolio next → (optional) agent-loop next or lanes create with that project → policy evaluate for the resulting action; assert no errors and expected keys in state.
4. **CI**: Add the full slice (project_case, supervised_loop, progress_replan, portfolio, lanes, review_lanes, human_policy, mission_control) to CI.
