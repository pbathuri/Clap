# M26 Integration Pane Report — Goal-to-Plan, Executor, Teaching Studio

Integration of three milestone blocks in specified merge order on the current branch. All three blocks were present in the same working tree; integration was performed as **verification in merge order** plus **full test slice**. No git merge conflicts; no file conflicts requiring resolution.

---

## 1. Merge steps executed

| Step | Block | Action |
|------|--------|--------|
| **1** | **Pane 1** — M26A–M26D (+ M26D.1) Goal-to-Plan Compiler | Verified as base: `planner/schema.py`, `sources.py`, `classify.py`, `compile.py`, `explain.py`, `preview.py`, `store.py`; CLI `planner compile|preview|explain|graph`; mission_control `goal_plan` block. Plan/work-graph contract: Plan, PlanStep, DependencyEdge, Checkpoint, ExpectedArtifact, BlockedCondition, ProvenanceSource. |
| **2** | **Pane 3** — M26E–M26H (+ M26H.1) Safe Action Runtime + Checkpointed Executor | Verified builds on plan contract (executor uses copilot.PlanPreview for *execution*; planner.Plan is compile-only). `executor/models.py`, `mapping.py`, `runner.py`, `hub.py`; CLI `executor run|status|artifacts|resume`; mission_control `executor` block. No changes to planner; additive. |
| **3** | **Pane 2** — M26I–M26L (+ M26L.1) Agent Teaching Studio + Skill Capture | Verified builds on task_demos and corrections: `teaching/skill_models.py`, `skill_store.py`, `normalize.py`, `review.py`, `report.py`; CLI `skills list|draft-from-demo|draft-from-correction|review|accept|reject|attach|report|scorecard|coverage`; mission_control `teaching_skills` block. No overlap with planner or executor command names. |
| **4** | Validation | Ran full test slice: **58 passed** (13 goal-plan, 21 executor, 15 teaching, 10 mission_control). |

---

## 2. Files with conflicts

**None.** No git merge conflicts and no overlapping edits. The three blocks use separate packages (`planner/`, `executor/`, `teaching/`) and separate CLI groups (`planner`, `executor`, `skills`). Mission control state uses distinct keys: `goal_plan`, `executor`, `teaching_skills`.

---

## 3. How each conflict was resolved

N/A. No conflicts occurred. Consistency checks:

- **CLI:** No duplicate command names. `planner` has recommend-next, shortlist, build-brief, build-rfc, compile, preview, explain, graph. `executor` has run, status, artifacts, resume. `skills` has list, draft-from-demo, draft-from-correction, review, accept, reject, attach, report, scorecard, coverage.
- **Plan contract:** Executor runs via `PlanPreview` (copilot) keyed by routine_id or job_id; planner produces `Plan` (goal-compiled) and does not drive executor in this draft. Optional future: “executor run --from-planner” that converts planner.Plan → job_pack_ids and uses existing runner.
- **Teaching:** Uses `task_demos.store`, `corrections`; skill drafts are independent of planner Plan schema. Skills can later be referenced by planner or executor (e.g. “skills that match this goal”) without changing current interfaces.

---

## 4. Tests run after each merge

Single run after verifying all three blocks (no per-pane branches):

```bash
pytest tests/test_goal_plan_compiler_m26.py tests/test_executor.py tests/test_teaching_skills.py tests/test_mission_control.py -v --tb=short
```

**Result: 58 passed.**

| Suite | Count | Coverage |
|-------|--------|----------|
| test_goal_plan_compiler_m26 | 13 | Schema, compile, explain, preview, graph, store, classify |
| test_executor | 21 | ActionEnvelope, plan_preview_to_envelopes, ExecutionRun, hub save/load/artifacts, resolve_plan, run_with_checkpoints, resume, action bundles, recovery options, record_recovery_decision |
| test_teaching_skills | 15 | Skill model, store, demo/correction/manual drafts, accept/reject, attach, report, scorecard, pack goal coverage |
| test_mission_control | 10 | State structure, report format, next action, rollback, replay_task, incubator, environment, starter_kits |

---

## 5. Final integrated command surface

**Planner (goal-to-plan)**  
`planner compile --goal "..."` [--repo-root] [--mode simulate|real]  
`planner preview --latest` [--repo-root]  
`planner explain --latest` [--repo-root]  
`planner graph --latest` [--repo-root]  
*(Existing product-evolution: recommend-next, shortlist, build-brief, build-rfc.)*

**Executor (safe action runtime / checkpointed)**  
`executor run --plan-ref <routine_id|job_id>` [--mode simulate|real] [--run RUN_ID] [--stop-at-checkpoints]  
`executor status` [--run RUN_ID]  
`executor artifacts` [--run RUN_ID]  
`executor resume --run RUN_ID` [--approve|--reject]

**Skills (teaching studio)**  
`skills list` [--status draft|accepted|rejected] [--limit N]  
`skills draft-from-demo --id <task_id>` [--goal-family] [--task-family]  
`skills draft-from-correction --id <correction_id>` [--goal-family] [--task-family]  
`skills review --id <skill_id>`  
`skills accept --id <skill_id>` [--trusted-real] [--notes]  
`skills reject --id <skill_id>` [--notes]  
`skills attach --id <skill_id> --pack <pack_id>`  
`skills report`  
`skills scorecard` [--id]  
`skills coverage` [--id]

**Mission control**  
`workflow-dataset mission-control` includes [Goal / plan], [Executor], [Teaching / skills] in the report; state keys `goal_plan`, `executor`, `teaching_skills` are populated.

---

## 6. Remaining risks

| Risk | Mitigation |
|------|-------------|
| **Executor runs PlanPreview, not planner.Plan** | By design in this draft. To “run compiled goal plan,” operator can use a routine/job that matches the goal, or a future “executor run --from-planner” can map planner.Plan → job_pack_ids and call existing runner. |
| **Skills not yet consumed by planner** | Planner does not yet filter or rank by accepted skills; teaching is additive. Future: planner compilation can prefer steps backed by accepted skills. |
| **Product-evolution planner** | `planner recommend-next`, shortlist, build-brief, build-rfc depend on `planner.evidence`, `planner.candidates`, `planner.briefs`. If those modules are missing, only goal-to-plan commands (compile, preview, explain, graph) are guaranteed. |
| **Report section order** | [Teaching / skills] appears earlier in the report than [Goal / plan] and [Executor]; state keys are independent. |

---

## 7. Exact recommendation for the next batch

1. **Optional: executor run from planner** — Add `executor run --from-planner` that loads `planner.store.load_latest_plan()`, maps Plan.steps (with provenance job/macro) to job_pack_ids, and invokes `run_with_checkpoints` with a synthetic PlanPreview or a single routine that chains those jobs. Keeps execution path single (executor runner) and makes “compile then run” a first-class flow.
2. **Optional: planner uses skills** — When compiling a goal, consider accepted skills (e.g. by goal_family/task_family) to suggest or order steps. Requires a small skill lookup in planner.sources or compile.
3. **CI** — Run the same slice in CI: `tests/test_goal_plan_compiler_m26.py`, `tests/test_executor.py`, `tests/test_teaching_skills.py`, `tests/test_mission_control.py`.
4. **Docs** — Add a short “M26 stack overview” (plan → skills → execution) linking M26A–M26D, M26E–M26H, M26I–M26L for maintainers.
