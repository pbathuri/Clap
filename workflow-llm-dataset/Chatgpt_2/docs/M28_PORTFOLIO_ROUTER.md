# M28 Portfolio Router + Project Scheduler

First-draft portfolio layer for multi-project routing and scheduling. Local, operator-readable, no auto-run.

## Objective

- Manage multiple active projects/cases.
- Rank which project deserves attention now.
- Route the agent loop toward highest-value or most urgent work.
- Account for blockers, deadlines, trust state, approvals, progress.
- Surface portfolio-wide health and priorities.
- Make the product feel like it can supervise real ongoing work across projects.

## What exists

### Phase A — Portfolio model

- **portfolio/models.py**: `Portfolio`, `PortfolioEntry`, `ProjectPriority`, `PortfolioHealth`, `UrgencyScore`, `ValueScore`, `BlockerSeverity`, `AttentionRecommendation`, `DeferRevisitState`.
- **portfolio/store.py**: Optional `portfolio_meta.json` under `data/local/portfolio/` for priority hints (high/medium/low per project) and defer/revisit state.

### Phase B — Project scheduler

- **portfolio/scheduler.py**:
  - `rank_active_projects(repo_root)` → list of `ProjectPriority` (sorted by composite score).
  - `get_next_recommended_project(repo_root)` → `AttentionRecommendation | None`.
  - `explain_priority(project_id, repo_root)` → human-readable explanation.
  - Uses: project_case (active projects, blockers), progress board (stalled, replan_needed), current project, priority hints, deferred set.

### Phase C — Portfolio reports

- **portfolio/reports.py**: `report_active_by_priority`, `report_stalled`, `report_blocked`, `report_best_next`, `report_needing_intervention`, `report_ready_for_execution`; `format_portfolio_status`, `format_portfolio_list`, `format_stalled_report`, `format_blocked_report`.

### Phase D — CLI + mission control

- **CLI**: `workflow-dataset portfolio list|status|rank|next|explain --project <id>|stalled|blocked`.
- **Mission control**: state key `portfolio_router` with `priority_stack`, `top_intervention_candidate`, `next_recommended_project`, `most_blocked_project`, `most_valuable_ready_project`, `health_total_active`, `health_labels`. Report section `[Portfolio]`.

### Phase E — Tests + docs

- **tests/test_portfolio_m28.py**: model roundtrip, rank empty/with projects, stalled/blocked detection, explain output, next-project recommendation, no-project / all-blocked edge cases, store hints/defer, mission_control includes portfolio_router.
- **docs/M28_BEFORE_CODING.md**, **docs/M28_PORTFOLIO_ROUTER.md** (this file).

## CLI usage

```bash
workflow-dataset portfolio list
workflow-dataset portfolio status
workflow-dataset portfolio rank
workflow-dataset portfolio next
workflow-dataset portfolio explain --project founder_case_alpha
workflow-dataset portfolio stalled
workflow-dataset portfolio blocked
```

## Sample portfolio record (single entry)

```json
{
  "project_id": "founder_case_alpha",
  "title": "Founder case alpha",
  "state": "active",
  "priority": {
    "project_id": "founder_case_alpha",
    "tier": "high",
    "urgency": {"score": 0.4, "reason": "Recently updated"},
    "value": {"score": 0.5, "operator_hint": "", "reason": "No hint"},
    "blocker": {"level": "unblocked", "blocked_goals_count": 0, "can_advance": true},
    "rank_index": 1,
    "composite_score": 0.9
  },
  "health_label": "active",
  "is_current": true,
  "is_stalled": false,
  "is_blocked": false,
  "is_ready_for_execution": true,
  "needs_intervention": false
}
```

## Sample ranked portfolio output (CLI `portfolio rank`)

```
  #1  founder_case_alpha  tier=high  score=0.90  blocker=unblocked
  #2  analyst_research    tier=medium  score=0.60  blocker=partial
```

## Sample priority explanation (CLI `portfolio explain --project founder_case_alpha`)

```
Project: founder_case_alpha
Rank: #1 of 2
Tier: high
Composite score: 0.90

Urgency:
  score=0.40  Recently updated

Value:
  score=0.50  No hint

Blocker:
  level=unblocked  can_advance=True
  blocked_goals=0
```

## Tests run

```bash
pytest tests/test_portfolio_m28.py -v --tb=short
```

## Remaining gaps (for later refinement)

- **Deadlines**: Project model has no `deadline_iso`; urgency uses placeholder. Add optional deadline on Project or portfolio_meta and use in scheduler.
- **Operator priority hints**: No CLI to set priority hint (e.g. `portfolio set-priority --project X --hint high`); only store API.
- **Defer/revisit at portfolio level**: Store supports it; no CLI to defer/revisit a project (e.g. `portfolio defer --project X --revisit-after 2025-02-01`).
- **Wire agent-loop next to portfolio**: When `agent-loop next` is run without `--project`, optionally use `portfolio next` recommended project as default.
- **Progress board alignment**: Progress board still uses prior_plans for “projects”; portfolio uses project_case active. Optional: filter progress board by project_case active list.
- **Trust/readiness**: Scheduler does not yet pull trust_cockpit or job_pack readiness per project; can add as value/blocker signal.
- **E2E test**: One test that creates two projects, sets one as current, runs portfolio rank/next/explain and mission-control, asserts keys and no errors.
