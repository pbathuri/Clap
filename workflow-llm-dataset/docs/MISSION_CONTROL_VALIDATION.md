# M22B Mission Control — Validation

## Summary

- **Read-heavy:** Mission control aggregates state from existing local sources; it does not write or execute changes.
- **Unified surface:** One command (`workflow-dataset mission-control`) shows product, evaluation, development, and incubator state plus a recommended next action.
- **Operator-controlled:** Recommendation is advisory; no automatic changes.

## Files

| Action | Path |
|--------|------|
| Added | `src/workflow_dataset/mission_control/__init__.py` |
| Added | `src/workflow_dataset/mission_control/state.py` |
| Added | `src/workflow_dataset/mission_control/next_action.py` |
| Added | `src/workflow_dataset/mission_control/report.py` |
| Added | `tests/test_mission_control.py` |
| Added | `docs/MISSION_CONTROL_VALIDATION.md` |
| Modified | `src/workflow_dataset/cli.py` (app.command("mission-control")) |

## Usage

- `workflow-dataset mission-control` — print dashboard to stdout
- `workflow-dataset mission-control --output path` — write report to file
- `workflow-dataset mission-control --repo-root /path` — override repo root for aggregation

## Aggregated sources

- **Product state:** `get_dashboard_data` (validated_workflows from REPORTING_WORKFLOWS, cohort, review_package, staging), `local_sources` (pilot_dir, workspaces_root).
- **Evaluation state:** `board_report`, `list_runs` (eval) — latest_run_id, recommendation, best_run_id, comparison regressions/improvements, workflows_tested.
- **Development state:** `get_queue_status` (devlab experiments), `proposal_queue_summary`, `list_proposals` — queued/running/done, pending/accepted/rejected proposals.
- **Incubator state:** `list_candidates` — candidates_by_stage, promoted_count, rejected_count, hold_count.

## Next-action logic

- **rollback:** eval recommendation == "revert"
- **build:** pending_proposals > 0 (review proposals) OR unreviewed workspaces > 0
- **promote:** incubator has candidates, none promoted yet (after build)
- **benchmark:** no runs or recommendation hold/refine
- **cohort_test:** cohort recommendation contains "expand" or "test"
- **hold:** default

## Tests

From the repo that has `workflow_dataset` installed (or from `workflow-llm-dataset` with `PYTHONPATH=src`):

```bash
cd workflow-llm-dataset
PYTHONPATH=src python3 -m pytest tests/test_mission_control.py -v
# 4 passed
```

## Sample mission-control output

```
=== Mission Control (local) ===

[Product]
  validated_workflows: weekly_status, status_action_bundle, stakeholder_update_bundle, ...
  cohort: expand_adjacent  sessions=13
  unreviewed: 5  package_pending: 0

[Evaluation]
  latest_run: _492e89368af  recommendation: hold
  best_run: _492e89368af  runs_count: 1

[Development]
  experiments: queued=0 running=0 done=1
  proposals: pending=1 accepted=0 rejected=0

[Incubator]
  candidates_by_stage: {'idea': 1}
  promoted: 0  rejected: 0  hold: 0

--- Recommended next action ---
  action: build
  rationale: Pending patch proposals need operator review; apply or reject.
  detail: Pending: 1. Use devlab show-proposal and review-proposal.

(Operator-controlled. No automatic changes.)
```

## Local-first and operator-controlled

- All data from local paths; no network.
- Report is read-only composition; no state changes.
- Recommended action is a suggestion; operator runs commands (devlab review-proposal, incubator promote, eval run-suite, etc.) explicitly.

---

## Recommendation for next product-evolution cycle

1. **Persist snapshot (optional):** Add `workflow-dataset mission-control --output path` to a nightly or pre-release script so the team has a timestamped report artifact (e.g. `mission_control_YYYYMMDD.txt`) for history.
2. **Dashboard section (optional):** If the repo has a web or TUI dashboard, add a "Mission Control" tab that calls `format_mission_control_report(repo_root)` and renders the same sections plus the recommended action.
3. **Planner shortlist:** Have the product evolution planner (or "recommend-next") consume `recommend_next_action(get_mission_control_state())` so its shortlist is aligned with the same evidence (e.g. "Next: build — 1 pending proposal").
4. **No change to scope:** Keep mission-control as an internal development control plane; do not expose it as an end-user orchestration surface or add cloud/auto-apply.
