# M40L.1 — Production Review Cycles + Sustained-Use Checkpoints (Deliverable)

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/production_launch/models.py` | Added `PostDeploymentGuidance` enum (continue/narrow/rollback/repair), `ProductionReviewCycle` dataclass, `SustainedUseCheckpoint` dataclass. |
| `src/workflow_dataset/production_launch/__init__.py` | Exported M40L.1 modules: post_deployment_guidance, review_cycles, sustained_use, ongoing_summary. |
| `src/workflow_dataset/cli.py` | Added `production-runbook review-cycle` (show \| record), `production-runbook sustained-use` (checkpoint \| report) with `--kind` and `--record`, `production-runbook ongoing-summary`, `launch-decision guidance`. |
| `src/workflow_dataset/mission_control/state.py` | Extended `production_launch` with `post_deployment_guidance`, `post_deployment_reason`, `latest_review_cycle_at`, `latest_sustained_use_checkpoint_kind`, `ongoing_summary_one_liner`. |
| `src/workflow_dataset/mission_control/report.py` | Extended `[Production launch]` section with guidance, reason, latest_review, checkpoint_kind, ongoing one-liner. |
| `tests/test_production_launch.py` | Added 6 tests: post_deployment_guidance structure, review_cycle build, record_review_cycle, sustained_use checkpoint build, record_sustained_use_checkpoint, ongoing_production_summary. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/production_launch/post_deployment_guidance.py` | `build_post_deployment_guidance(repo_root)` → continue / narrow / rollback / repair from release readiness, triage health, reliability, supportability; returns reason and recommended_actions. |
| `src/workflow_dataset/production_launch/review_cycles.py` | `build_production_review_cycle`, `record_review_cycle`, `list_review_cycles`, `get_latest_review_cycle`. Persistence: `data/local/production_launch/review_cycles.json`. |
| `src/workflow_dataset/production_launch/sustained_use.py` | `build_sustained_use_checkpoint(repo_root, kind=auto|session_5|session_10|day_7)`, `record_sustained_use_checkpoint`, `list_sustained_use_checkpoints`. Persistence: `data/local/production_launch/sustained_use_checkpoints.json`. Criteria use cohort/outcomes session count and days estimate. |
| `src/workflow_dataset/production_launch/ongoing_summary.py` | `build_ongoing_production_summary(repo_root)`, `format_ongoing_summary_report(summary)`. Operator-facing: guidance, current review cycle, checkpoint, key metrics, one_liner. |
| `docs/M40L1_PRODUCTION_REVIEW_CYCLES_AND_SUSTAINED_USE.md` | This deliverable. |

## 3. Sample production review cycle

```json
{
  "cycle": {
    "cycle_id": "2025-03-16T14-30-00",
    "at_iso": "2025-03-16T14:30:00Z",
    "summary": "Guidance=continue. Blockers=0 Warnings=1 Failed gates=0.",
    "findings": ["Warnings: 1"],
    "guidance_snapshot": "continue",
    "recommended_actions": [
      "workflow-dataset production-runbook review-cycle show",
      "workflow-dataset production-runbook sustained-use checkpoint",
      "Schedule next review per runbook."
    ],
    "next_due_iso": "2025-03-23T00:00:00Z",
    "vertical_id": "founder_operator_core"
  },
  "launch_decision_summary": {
    "recommended_decision": "launch_narrowly",
    "blocker_count": 0,
    "warning_count": 1
  },
  "post_deployment_guidance": {
    "guidance": "continue",
    "reason": "No blockers; triage and reliability acceptable. Continue operating; run regular review cycles.",
    "recommended_actions": ["workflow-dataset production-runbook review-cycle show", "..."],
    "evidence": {
      "release_readiness_status": "degraded",
      "open_issue_count": 0,
      "highest_severity": "",
      "reliability_outcome": "pass"
    }
  }
}
```

## 4. Sample sustained-use checkpoint report

```json
{
  "checkpoint": {
    "checkpoint_id": "session_5_2025-03-16_1430",
    "kind": "session_5",
    "at_iso": "2025-03-16T14:30:00Z",
    "criteria_met": true,
    "report_summary": "Sessions=6 days_est=1 kind=session_5. Criteria_met=true. Guidance=continue.",
    "sessions_or_days_context": {
      "sessions_count": 6,
      "days_estimate": 1,
      "source": "dashboard"
    },
    "guidance": "continue",
    "recommended_actions": [
      "workflow-dataset production-runbook review-cycle show",
      "workflow-dataset production-runbook sustained-use checkpoint",
      "Schedule next review per runbook."
    ]
  },
  "post_deployment_guidance": {
    "guidance": "continue",
    "reason": "No blockers; triage and reliability acceptable. Continue operating; run regular review cycles.",
    "recommended_actions": ["..."]
  },
  "criteria_met": true,
  "next_recommended": "Run another checkpoint after more sessions or schedule day_7."
}
```

## 5. Exact tests run

```bash
python3 -m pytest tests/test_production_launch.py -v
```

**18 passed**, including:

- test_post_deployment_guidance_structure  
- test_production_review_cycle_build  
- test_record_review_cycle  
- test_sustained_use_checkpoint_build  
- test_record_sustained_use_checkpoint  
- test_ongoing_production_summary  

## 6. Next recommended step for the pane

- **Harden and schedule**: Add a simple “next review due” reminder (e.g. from `next_due_iso` in the latest review cycle) into mission control or daily inbox so operators are prompted to run `production-runbook review-cycle record` and `sustained-use checkpoint --record` on a cadence (e.g. weekly + at session milestones).
- **Narrow scope definition**: Make “narrow” guidance actionable by linking to a concrete narrow scope (e.g. single cohort id or workflow id) from cohort/vertical state when guidance is `narrow`.
- **Rollback runbook step**: Add an explicit “rollback” step to the production runbook (and optionally to recovery paths) when guidance is `rollback`, with a one-line command or ref to install/rollback flow.
