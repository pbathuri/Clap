# M24N–M24Q — Outcome Capture + Session Memory + Improvement Signals

## Objective

First-draft system that:

1. Captures what happened in a session
2. Records what was useful / blocked / incomplete
3. Stores session memory and outcome summaries
4. Generates improvement signals for jobs/routines/macros/packs
5. Supports next-run betterment without hidden autonomy
6. Connects outcome capture to trust and correction systems

**This is NOT:** hidden continual learning, automatic trust upgrades, opaque model mutation.

**This IS:** transparent session outcome intelligence.

---

## Components

### Phase A — Outcome model (`outcomes/models.py`)

- **BLOCKED_CAUSES** / **OUTCOME_KINDS** — taxonomies
- **BlockedCause**, **UsefulnessConfirmation**, **IncompleteWork**, **FollowUpRecommendation**
- **TaskOutcome**, **ArtifactOutcome**, **SessionOutcome** — with `to_dict()` / `from_dict()`

### Phase B — Session memory store (`outcomes/store.py`)

- Persistence under `data/local/outcomes/` (`sessions/*.json`, `outcome_history.json`)
- **save_session_outcome**, **get_session_outcome**, **list_session_outcomes**, **load_outcome_history**

### Phase C — Patterns (`outcomes/patterns.py`)

- **repeated_block_patterns** — cause_code + source_ref counts
- **repeated_success_patterns** — useful/success refs per pack
- **most_useful_per_pack** — top refs by usefulness score per pack

### Phase D — Improvement signals (`outcomes/signals.py`, `outcomes/bridge.py`)

- **generate_improvement_signals** — recurring_blocker, job_fails_repeatedly, macro_or_job_highly_useful, first_value_flow_weak
- **outcome_to_correction_suggestions** — advisory correction suggestions
- **pack_refinement_suggestions** — promote high-value, document blocker
- **next_run_recommendations** — run again, resolve before retry

### Phase E — CLI

- `workflow-dataset outcomes latest [--limit N]`
- `workflow-dataset outcomes session --id <session_id>`
- `workflow-dataset outcomes patterns`
- `workflow-dataset outcomes recommend-improvements`

### Phase F — Mission control

- State: **outcomes** — latest_session_outcomes_count, latest_session_ids, outcome_history_count, recurring_blockers, high_value_jobs_macros, next_recommended_improvement, first_value_flow_weak
- Report: **[Outcomes]** section in mission-control report

---

## Constraints

- Do **not** introduce hidden continual learning or auto-modify trust/approvals.
- Do make outcomes actionable; keep learning signals explicit and local.

---

## Remaining gaps (for later refinement)

- Live session layer integration: who calls **save_session_outcome** at session end (e.g. from session board or copilot).
- Operator UI for confirming usefulness (e.g. thumbs up on job run).
- Richer blocked-cause attribution (per-task source_ref in history if needed).
- Trust review bridge: explicit “suggest trust review” from outcomes (advisory only).
- Export of outcome history for external analytics (e.g. CSV/Parquet).

---

## M24Q.1 — Pack Scorecards + Improvement Backlog

Per-pack scorecards and operator-readable improvement backlog.

### CLI

- `workflow-dataset outcomes scorecard --pack-id <pack_id>` — e.g. `founder_ops_plus`, `analyst_research_plus`
- `workflow-dataset outcomes backlog` — global improvement backlog
- `workflow-dataset outcomes backlog --pack-id <pack_id>` — backlog filtered by pack

### Scorecard (`outcomes/scorecard.py`, `report.format_pack_scorecard`)

- **Usefulness** — total confirmations, high-value refs from outcomes
- **Blockers** — session block count, recurring causes (filtered by pack refs)
- **Readiness** — repo-level proxy (rollout demo_ready)
- **Trusted-real suitability** — count of pack’s recommended jobs that are trusted_for_real vs simulate_only
- **Session reuse strength** — sessions count, complete vs fix/pause, ratio
- **Improvement backlog** — pack-scoped refinement + next-run + correction suggestions

### Improvement backlog (`build_improvement_backlog`, `format_improvement_backlog`)

- Global signals + (when pack_id given) pack-scoped next_run and pack_refinement items
- Each item: pack_id, kind, title, priority, detail

### Sample pack scorecard (excerpt)

```
=== Pack scorecard: founder_ops_plus ===

[Usefulness]
  2 confirmations, 1 high-value refs
    high_value: weekly_status_from_notes

[Blockers]
  1 in sessions, 0 recurring patterns

[Readiness]
  not demo_ready

[Trusted-real suitability]
  1 trusted_for_real, 2 simulate_only

[Session reuse strength]
  3 sessions, 2 complete, 1 fix/pause

[Improvement backlog]  4 items
  1. [medium] promote_high_value: Score 5 from outcomes; consider highlighting in first-value flow.
  2. [high] resolve_before_retry: Resolve blocker: approval_missing
      source_ref=export_pdf; add approval or fix config then retry.
```

### Sample improvement backlog (excerpt)

```
=== Improvement backlog ===

  1. [high] recurring_blocker  pack=(global)
      Recurring block: approval_missing
      source_ref=export_pdf count=3
  2. [medium] next_run  pack=founder_ops_plus
      Run again: weekly_status_from_notes
      High value in pack founder_ops_plus; consider workflow-dataset jobs run --id ...
```
