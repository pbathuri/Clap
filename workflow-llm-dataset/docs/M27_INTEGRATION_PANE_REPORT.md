# M27 Integration Pane Report — Project/Case, Supervised Loop, Progress/Replan

Integration of three M27 milestone blocks in specified merge order on the current branch. All three blocks were present in the same working tree; integration was performed as **verification in merge order** plus **full test slice**. No git merge conflicts; no file conflicts requiring resolution.

---

## 1. Merge steps executed

| Step | Block | Action |
|------|--------|--------|
| **1** | **Pane 1** — M27A–M27D (+ M27D.1) Project/Case Graph + Persistent Goal Stack | Verified as base: `project_case/models.py`, `store.py`, `goal_stack.py`, `graph.py`, `report.py`, `templates.py`; CLI `projects list|create|show|goals|add-goal|attach-session|attach-plan|attach-run|attach-artifact|report|set-current|archive`, `projects templates list|show`; mission_control `project_case` block (active_project_id, goal_stack_summary, project_blockers, recommended_next_project_action). |
| **2** | **Pane 2** — M27E–M27H (+ M27H.1) Supervised Agent Loop + Approval Queue | Verified builds on project/case: `supervised_loop/models.py`, `store.py`, `queue.py`, `next_action.py`, `handoff.py`, `summary.py`, `cli.py`; CLI `agent-loop status|next|queue|approve|reject|defer|list-deferred|revisit|approve-batch|policy|cycle-report`; mission_control `supervised_loop` block. Cycle uses `project_slug` (aligns with project_case project_id). No conflicts; additive. |
| **3** | **Pane 3** — M27I–M27L (+ M27L.1) Triggered Replanning + Impact/Progress Board | Verified builds on planner/outcomes: `progress/board.py`, `store.py`, `signals.py`, `recommendation.py`, `recovery.py`, `playbooks.py`; CLI `progress board|project|recovery|playbooks` and replan commands; mission_control `progress_replan` block. Progress board uses its own `list_projects` (prior_plans dir); project_case remains source of truth for persistent projects. No conflicts. |
| **4** | Validation | Ran full test slice: **54 passed** (project_case 14, supervised_loop 21, progress_replan 14, mission_control 9). |

---

## 2. Files with conflicts

**None.** No git merge conflicts and no overlapping command names or state keys.

- **cli.py**: Separate groups — `projects` (with `projects templates`), `agent-loop`, `progress`. No duplicate command names.
- **mission_control/state.py**: Distinct keys — `project_case`, `supervised_loop`, `progress_replan`. All populated in order.
- **mission_control/report.py**: Separate sections [Project / case], [Progress / Replan], [Supervised agent loop].
- **Naming**: `progress.store.list_projects` returns project ids from **progress** store (prior_plans); `project_case.list_projects` returns project metadata from **project_case** store. Different concepts; no name clash in public API (different modules).

---

## 3. How each conflict was resolved

N/A. No conflicts occurred. Consistency checks:

- **Project slug vs project_id**: Supervised loop uses `project_slug` (e.g. founder_case_alpha); operator can pass `--project` to `agent-loop next` or leave empty for cycle default. Optional future: default `agent-loop next` to `project_case.get_current_project_id()` when `--project` is not set.
- **Progress “projects”**: Progress board’s `list_projects` is from `data/local/progress/prior_plans/` (plan history by project id). Unifying with project_case (e.g. progress board showing only project_case projects) is a later refinement, not required for this integration.

---

## 4. Tests run after each merge

Single run after verifying all three blocks (no per-pane branches):

```bash
pytest tests/test_project_case_m27.py tests/test_supervised_loop.py tests/test_progress_replan.py tests/test_mission_control.py -v --tb=line
```

**Result: 54 passed** (14 + 21 + 14 + 9).

| Suite | Count | Coverage |
|-------|--------|----------|
| test_project_case_m27 | 14 | Create/load/list/archive, goal stack, status/blocked, attach, report, current id, summary, templates list/get, create from template, goal archetype output |
| test_supervised_loop | 21 | Cycle roundtrip, queue enqueue/list/approve/reject/defer, handoff, summary, policy, list_deferred/revisit, approve_batch |
| test_progress_replan | 14 | ReplanSignal, prior_plan, replan_signals, list_projects, compare_plans, explain_replan, format_plan_diff, build/format progress board, recommend_replan, playbooks, stalled recovery |
| test_mission_control | 9 | State structure, report format, next action, rollback, replay_task, incubator, environment, starter_kits |

---

## 5. Final integrated command surface

**Projects (M27A–M27D, M27D.1)**  
`projects list` [--state] [--repo-root]  
`projects create --id <id>` [--title] [--description] [--from-template <template_id>] [--repo-root]  
`projects show --id <id>` [--repo-root]  
`projects goals --id <id>` [--repo-root]  
`projects add-goal --id <id> --goal-id <gid>` [--title] [--order] [--repo-root]  
`projects attach-session --id <id> --session <session_id|latest>` [--repo-root]  
`projects attach-plan --id <id>` [--plan-id] [--plan-path] [--repo-root]  
`projects attach-run --id <id> --run <run_id>` [--repo-root]  
`projects attach-artifact --id <id> --artifact <path_or_label>` [--repo-root]  
`projects report --id <id>` [--repo-root]  
`projects set-current --id <id>` [--repo-root]  
`projects archive --id <id>` [--repo-root]  
`projects templates list` [--repo-root]  
`projects templates show --id <template_id>` [--repo-root]

**Agent loop (M27E–M27H)**  
`agent-loop status` [--repo-root]  
`agent-loop next` [--project <slug>] [--repo-root]  
`agent-loop queue` [--repo-root]  
`agent-loop approve --id <queue_id>` [--note] [--no-execute] [--repo-root]  
`agent-loop reject --id <queue_id>` [--note] [--repo-root]  
`agent-loop defer --id <queue_id>` [--note] [--reason] [--revisit-after] [--repo-root]  
`agent-loop list-deferred` [--repo-root]  
`agent-loop revisit --id <queue_id>` [--repo-root]  
`agent-loop approve-batch` [--max-risk low|medium] [--no-execute] [--repo-root]  
`agent-loop policy` [--repo-root]  
`agent-loop cycle-report` [--latest] [--repo-root]

**Progress / replan (M27I–M27L)**  
`progress board` [--repo-root]  
`progress project` [--id] [--repo-root]  
`progress recovery` [--repo-root]  
`progress playbooks` [--repo-root]  
*(Plus replan-related commands as implemented in progress_group.)*

**Mission control**  
`workflow-dataset mission-control` includes [Project / case], [Progress / Replan], [Supervised agent loop] in the report; state keys `project_case`, `supervised_loop`, `progress_replan` are populated.

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| **Two “project” notions** | Progress board uses `progress.store.list_projects` (prior_plans); project_case uses `project_case.list_projects` (persistent projects). Document; optional later: progress board can filter or key off project_case active projects. |
| **agent-loop next default project** | If `--project` is omitted, cycle uses existing or "default". Optional: default to `project_case.get_current_project_id()` when set. |
| **Report section order** | [Project / case], [Progress / Replan], [Supervised agent loop] order is fixed in report; state keys are independent. |
| **Env-dependent tests** | All suites require project deps. CI should use `pip install -e ".[dev]"` or project venv. |

---

## 7. Exact recommendation for the next batch

1. **Wire current project to agent-loop**: When `project_case.get_current_project_id()` is set and `agent-loop next` is run without `--project`, pass that project_id as the cycle’s project_slug so the loop runs in the context of the current project.
2. **Optional: Unify progress “projects” with project_case**: Have progress board optionally list active projects from project_case (e.g. `project_case.list_projects(state_filter="active")`) so replan-needed/stalled/advancing align with project_case projects; keep prior_plans as plan history keyed by project id.
3. **E2E test**: One test that creates a project from template → sets current → runs `agent-loop next` (or propose) → approves one item → runs progress board; assert no errors and expected keys in state.
4. **CI**: Add the full slice (project_case, supervised_loop, progress_replan, mission_control) to CI with project venv.
