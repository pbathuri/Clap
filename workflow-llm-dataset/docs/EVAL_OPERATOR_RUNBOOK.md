# M21X Evaluation Harness + Benchmark Board — Operator Runbook

## Purpose

- Run ops/reporting workflows on a **repeatable set of evaluation cases**.
- **Score** outputs with transparent heuristics and optional operator ratings.
- **Compare runs** and see regressions/improvements.
- **Benchmark board** for promote / hold / refine / revert decisions.
- All local; no auto-apply; operator decides what to adopt.

## Paths

- `data/local/eval/` — eval root
  - `cases/` — case JSON files
  - `suites/` — suite JSON (list of case_ids) or suite directories
  - `runs/<run_id>/` — per-run outputs and manifests

## Commands

### Cases and suites

```bash
# Seed default ops_reporting_core cases (4 cases + suite)
workflow-dataset eval seed-defaults

# E2: Seed expanded case library (12 cases, 4 workflows) and suite ops_reporting_expanded
workflow-dataset eval seed-expanded

# Add a case
workflow-dataset eval add-case my_case --workflow weekly_status --task-context "Project X: shipped Y; blocked on Z."
```

### Run suite or single case

```bash
# Run full suite (requires LLM config with base_model)
workflow-dataset eval run-suite ops_reporting_core
workflow-dataset eval run-suite ops_reporting_core --llm-config configs/llm_training.yaml

# Run a single case by id
workflow-dataset eval run-case weekly_status_project_delivery
workflow-dataset eval run-case weekly_status_project_delivery --llm-config configs/llm_training.yaml
```

Outputs go to `data/local/eval/runs/<run_id>/` with one dir per case and artifact `.md` files.

### Scoring and operator rating (E3: separated scores)

Scores are clearly separated in run manifests and reconciliation:

- **heuristic_score** — from `score-run`; 0–1 per dimension, aggregated.
- **operator_score** — from `operator-rating` per case; overall 1–5 normalized to 0–1.
- **model_judge_score** — optional; only when model-judge is enabled in config.

```bash
# Compute heuristic scores for a run (writes to run_manifest.json per case)
workflow-dataset eval score-run <run_id>
workflow-dataset eval score-run <run_id> --eval-root data/local/eval

# Save operator rating for a case (writes operator_rating.json in case dir)
workflow-dataset eval operator-rating <run_id> <case_id> --rating '{"overall": 4, "notes": "good"}'
workflow-dataset eval operator-rating <run_id> <case_id> -r '{"overall": 5, "notes": "ship it"}'
```

After rating one or more cases, re-score or run reconcile to combine with heuristic (and optional model-judge).

### Reconciliation (E3: why promote / hold / refine / revert)

```bash
# Single-run reconciliation (verdict from heuristic + operator only)
workflow-dataset eval reconcile <run_id>
workflow-dataset eval reconcile <run_id> --eval-root data/local/eval

# Compare with previous run and get verdict + reasons
workflow-dataset eval reconcile <run_id> --compare-with <previous_run_id>
workflow-dataset eval reconcile <run_id> -c <previous_run_id> -o reconciliation.json

# Write reconciliation to file (.json or .md)
workflow-dataset eval reconcile <run_id> --output data/local/eval/reconciliation.md
```

Reconciliation output includes: **verdict** (promote | hold | refine | revert), **heuristic_score**, **operator_score**, **model_judge_score**, and **reasons** (text explaining why).

#### Sample rated benchmark / reconciliation output

After running a suite, scoring, and optionally adding operator ratings:

```bash
workflow-dataset eval run-suite ops_reporting_core
workflow-dataset eval score-run <run_id>
workflow-dataset eval operator-rating <run_id> weekly_status_project_delivery -r '{"overall": 4, "notes": "good"}'
workflow-dataset eval reconcile <run_id> -o reconciliation.json
```

**Sample `reconciliation.json` (excerpt):**

```json
{
  "run_id": "run_abc123",
  "verdict": "promote",
  "reasons": [
    "Heuristic score: 0.72 (0–1).",
    "Operator score: 0.75 (0–1).",
    "Verdict: promote — improvements and no regressions; heuristic (and operator if set) support adoption."
  ],
  "heuristic_score": 0.72,
  "operator_score": 0.75,
  "model_judge_score": null,
  "per_case": [
    {
      "case_id": "weekly_status_project_delivery",
      "heuristic_score": 0.68,
      "operator_score": 0.75,
      "model_judge_score": null
    }
  ]
}
```

Manifest score separation (per case in `run_manifest.json` after `score-run` and operator-rating):

- **scores.artifacts** — heuristic dimensions (e.g. relevance, completeness, blocker_quality) 0–1 per artifact.
- **scores.operator_rating** — e.g. `{"overall": 4, "notes": "good"}` when set.
- **scores.model_judge** — present only when model-judge is enabled; keys = artifact names, values = judge scores.

### Compare runs and board (E2: latest vs best, thresholds)

```bash
# Compare two runs (baseline vs newer): deltas, regressions, improvements, thresholds, recommendation
workflow-dataset eval compare-runs <run_a_id> <run_b_id>
workflow-dataset eval compare-runs <run_a_id> <run_b_id> --eval-root data/local/eval

# E2: Compare latest run vs previous best (by total score); regressions and wins clearly shown
workflow-dataset eval compare-latest
workflow-dataset eval compare-latest --suite ops_reporting_expanded --limit 20
workflow-dataset eval compare-latest -o data/local/eval/compare_latest.md

# Benchmark board (latest, best, thresholds, recommendation; comparison is latest vs best when different)
workflow-dataset eval board
workflow-dataset eval board --suite ops_reporting_core --limit 10

# Write board report to file (includes E3 reconciliation and E2 thresholds_passed)
workflow-dataset eval board --output data/local/eval/benchmark_board.json
workflow-dataset eval board --output data/local/eval/benchmark_board.md
```

### E4: Benchmark trend view

Trend over recent runs, best/worst workflows (latest run), top regression risk, and top improvement opportunity (from latest vs previous comparison). Inspectable and operator-friendly.

```bash
# Trend summary (suite filter, limit runs)
workflow-dataset eval trend
workflow-dataset eval trend --suite ops_reporting_core --limit 10
workflow-dataset eval trend -s ops_reporting_core -n 20

# Write trend report to file
workflow-dataset eval trend --output data/local/eval/trend_report.json
workflow-dataset eval trend -o data/local/eval/trend_report.md --eval-root data/local/eval
```

Output includes: **trend_over_runs** (improving | declining | stable), **run_scores** (mean score per run, newest first), **best_workflows** / **worst_workflows** (from latest run), **top_regression_risk** (dimension with largest drop vs previous run), **top_improvement_opportunity** (dimension with largest gain).

#### Sample trend board output

```bash
workflow-dataset eval trend --limit 5
```

```
Trend: improving
  Latest: run_abc123  2026-01-15T14:00:00Z
Best workflows (latest run):
  weekly_status  0.72
  status_action_bundle  0.68
  stakeholder_update_bundle  0.61
Worst workflows (latest run):
  ops_reporting_workspace  0.48
Top regression risk: blocker_quality  delta=-0.08
Top improvement opportunity: relevance  delta=0.12
```

**Sample `trend_report.json` (excerpt):**

```json
{
  "suite": "ops_reporting_core",
  "trend_over_runs": "improving",
  "recent_run_ids": ["run_abc123", "run_prev456"],
  "run_scores": [
    { "run_id": "run_abc123", "timestamp": "2026-01-15T14:00:00Z", "mean_score": 0.65 },
    { "run_id": "run_prev456", "timestamp": "2026-01-14T10:00:00Z", "mean_score": 0.58 }
  ],
  "best_workflows": [
    { "workflow": "weekly_status", "mean_score": 0.72, "run_id": "run_abc123" }
  ],
  "worst_workflows": [
    { "workflow": "ops_reporting_workspace", "mean_score": 0.48, "run_id": "run_abc123" }
  ],
  "top_regression_risk": {
    "type": "dimension",
    "name": "blocker_quality",
    "delta": -0.08,
    "run_a": "run_prev456",
    "run_b": "run_abc123"
  },
  "top_improvement_opportunity": {
    "type": "dimension",
    "name": "relevance",
    "delta": 0.12,
    "run_a": "run_prev456",
    "run_b": "run_abc123"
  },
  "latest_run_id": "run_abc123",
  "latest_timestamp": "2026-01-15T14:00:00Z"
}
```

## Case format (JSON)

- `case_id` — unique id
- `workflow` — weekly_status | status_action_bundle | stakeholder_update_bundle | meeting_brief_bundle | ops_reporting_workspace
- `task_context` — text context for the run
- `context_file` — optional path to a file with more context
- `retrieval` — optional use retrieval
- `expected_artifact_types` — e.g. ["weekly_status.md"]
- `rubric_hints` — optional scoring hints

## Scoring (M21X)

- **Heuristic** (automatic): relevance, completeness, blocker_quality, risk_quality, next_step_specificity, stakeholder_readability, action_register_usefulness, decision_request_usefulness, honesty, output_clarity. Rules are in `eval/scoring.py`.
- **Operator rating**: stored per case in `operator_rating.json` (e.g. overall 1–5, notes).
- **Model-judge**: only when explicitly configured (`model_judge_enabled`); off by default. See `eval/scoring.model_judge_score_artifact`.

## Regression thresholds (E2)

Per-workflow floors (relevance, completeness, specificity, stakeholder_readability) are in `eval/thresholds.py`. A run must pass all thresholds for its workflows to get **promote**. If thresholds fail: **hold** (or **revert** if there are also regressions). Scoring remains heuristic-only unless model-judge is explicitly enabled.

## Recommendation (E2: threshold-aware)

- **promote** — thresholds passed; improvements, no regressions
- **hold** — no clear change, or thresholds not passed
- **refine** — mixed (some regressions, some improvements)
- **revert** — regressions only, or thresholds failed with regressions

## Safety

- No auto-apply; no writes outside `data/local/eval/`.
- All artifacts and scores are local and inspectable.
