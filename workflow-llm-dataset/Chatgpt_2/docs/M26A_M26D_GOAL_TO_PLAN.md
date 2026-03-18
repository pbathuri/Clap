# M26A–M26D — Goal-to-Plan Compiler

First-draft planning core: accept a live goal or operator intent, use session/jobs/demos/macros/packs, compile into an explicit work graph with steps, dependencies, checkpoints, blocked conditions, and expected outputs. Step classification by trust/action type. No auto-execution; plans are inspectable and preview-only.

---

## 1. Files modified

| File | Change |
|------|--------|
| `cli.py` | Added to `planner_group`: `planner compile --goal`, `planner preview --latest`, `planner explain --latest`, `planner graph --latest`. |
| `mission_control/state.py` | New block `goal_plan`: active_goal, latest_plan_id, plan_step_count, blocked_step_count, next_checkpoint_index, expected_artifacts, next_action. |
| `mission_control/report.py` | New section [Goal / plan] with goal, plan_id, steps, blocked, next_checkpoint, expected_artifacts, next action. |

## 2. Files created

| File | Purpose |
|------|--------|
| `planner/__init__.py` | Exports schema, compile, explain, preview, store. |
| `planner/schema.py` | GoalRequest, Plan, PlanStep, DependencyEdge, Checkpoint, ExpectedArtifact, BlockedCondition, ProvenanceSource; step_class constants (reasoning_only, local_inspect, sandbox_write, trusted_real_candidate, human_required, blocked); Plan.to_dict/from_dict. |
| `planner/sources.py` | gather_planning_sources(repo_root) — session, session_board, work_state, job_recommendations, job_pack_ids, routines, macros, task_demos, pack_summary. |
| `planner/classify.py` | classify_plan_step(step, repo_root, mode) → step_class using job policy and macro step_classifier. |
| `planner/compile.py` | compile_goal_to_plan(goal, repo_root, mode) — keyword match to routines/jobs, build steps/edges/checkpoints/blocked, attach provenance, classify steps. |
| `planner/explain.py` | explain_plan(plan) → markdown: why chosen, sources, steps, checkpoints, blocked, expected outputs. |
| `planner/preview.py` | format_plan_preview(plan), format_plan_graph(plan). |
| `planner/store.py` | save_current_goal, load_current_goal, save_latest_plan, load_latest_plan (data/local/planner/). |
| `tests/test_goal_plan_compiler_m26.py` | Schema, roundtrip, tokenize/score_match, compile (no sources + with routine), blocked, explain, preview, graph, store, classify. |
| `docs/M26A_M26D_GOAL_TO_PLAN_ANALYSIS.md` | Pre-coding analysis. |
| `docs/M26A_M26D_GOAL_TO_PLAN.md` | This doc. |

---

## 3. Exact CLI usage

```bash
# Compile goal into plan (saves as current goal + latest plan)
workflow-dataset planner compile --goal "Prepare weekly stakeholder update from notes and open tasks" [--repo-root PATH] [--mode simulate|real]

# Preview latest compiled plan
workflow-dataset planner preview --latest [--repo-root PATH]

# Explain latest plan (why, sources, blocked, human approval, outputs)
workflow-dataset planner explain --latest [--repo-root PATH]

# Show dependency graph of latest plan
workflow-dataset planner graph --latest [--repo-root PATH]
```

---

## 4. Sample goal request

- **CLI:** `workflow-dataset planner compile --goal "Prepare weekly stakeholder update from notes and open tasks"`
- **Schema:** `GoalRequest(goal_text="Prepare weekly stakeholder update from notes and open tasks", context_session_id="", context_pack_id="")`

---

## 5. Sample compiled plan

```json
{
  "plan_id": "a1b2c3d4e5f6...",
  "goal_text": "Prepare weekly stakeholder update from notes and open tasks",
  "steps": [
    {
      "step_index": 0,
      "label": "Weekly report",
      "step_class": "sandbox_write",
      "trust_level": "experimental",
      "approval_required": false,
      "checkpoint_before": false,
      "expected_outputs": ["report.md"],
      "blocked_reason": "",
      "provenance": {"kind": "job", "ref": "weekly_report", "label": "weekly_report"}
    },
    {
      "step_index": 1,
      "label": "Review",
      "step_class": "human_required",
      "approval_required": true,
      "provenance": {"kind": "macro", "ref": "ops_flow", "label": "ops_flow"}
    }
  ],
  "edges": [{"source_index": 0, "target_index": 1, "edge_type": "sequence"}],
  "checkpoints": [{"step_index": 0, "label": "Review", "required_approval": "approval"}],
  "expected_artifacts": [{"label": "report.md", "path_or_type": "", "step_index": 0}],
  "blocked_conditions": [],
  "sources_used": ["routine:weekly_stakeholder_update", "job:weekly_report"],
  "created_at": "2024-03-16T12:00:00Z"
}
```

---

## 6. Sample plan explanation

```markdown
## Plan explanation

**Goal:** Prepare weekly stakeholder update from notes and open tasks

**Plan ID:** a1b2c3d4e5f6...

### Sources used
- routine:weekly_stakeholder_update
- job:weekly_report

### Steps
- 1. Weekly report  [sandbox_write]  (from job:weekly_report)
- 2. Review  [human_required]  (from macro:ops_flow)  — **Human approval required**

### Checkpoints (human approval required before proceeding)
- After step 2: Review

### Expected outputs
- report.md (step 1)
```

---

## 7. Sample graph / dependency output

```
=== Plan dependency graph ===

Plan ID: a1b2c3d4e5f6...

  node_0  [label="Weekly report..."]  class=sandbox_write
  node_1  [label="Review..."]  class=human_required
  node_0 -> node_1  [sequence]

Checkpoints:
  checkpoint after node_0: approval
```

---

## 8. Exact tests run

```bash
pytest tests/test_goal_plan_compiler_m26.py -v --tb=short
```

Covers: GoalRequest schema, PlanStep to_dict, Plan roundtrip, tokenize/score_match, compile (no sources, with routine), blocked condition, explain_plan, format_plan_preview, format_plan_graph, store goal/plan, classify_plan_step (blocked).

---

## 9. Exact remaining gaps for later refinement

- **Semantic goal matching** — Current match is keyword/tag overlap. No NLU or embedding-based goal parsing.
- **Task demos in compilation** — Task demo titles/ids are gathered but not yet used to add steps or influence ordering; coordination_graph from task is not yet wired into plan edges.
- **Branching plans** — Edges are sequential only; no parallel branches or conditional steps.
- **Execution hook** — No “run this plan” in this block; execution remains via existing copilot run / macro runner.
- **Plan versioning** — Only “latest” plan is stored; no history or named plans.
- **Product evolution planner** — Existing `planner recommend-next`, `shortlist`, `build-brief`, `build-rfc` depend on `planner.evidence`, `planner.candidates`, `planner.briefs`; if those modules are missing, those commands will fail at runtime. Goal-to-plan commands (compile, preview, explain, graph) do not depend on them.
