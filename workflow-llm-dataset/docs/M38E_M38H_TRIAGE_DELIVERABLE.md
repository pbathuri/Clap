# M38E–M38H — Cohort Evidence Capture + Issue Triage Loop (Deliverable)

Local-first cohort evidence and issue triage loop for first-user hardening. No rebuild of reliability, support, or review systems; additive CLI, mission-control visibility, and doc/samples.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added **triage_group**: `triage list`, `triage show --id`, `triage classify --id`, `triage reproduce --id`, `triage resolve`. Added **cohort_group**: `cohort health`. |
| `src/workflow_dataset/mission_control/state.py` | Added **triage** block: highest_severity_issue_id, highest_severity, repeated_issue_clusters, open_issue_count, unresolved_supported_surface_count, recommended_mitigation, recommended_downgrade. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Triage / Cohort health]** section: open_issues, highest_severity, top_issue, unresolved_supported_surface, recommended_downgrade, recommended_mitigation. |

## 2. Files created (this pass)

| File | Purpose |
|------|---------|
| `docs/samples/M38_sample_evidence_item.json` | Sample cohort evidence item (session_feedback). |
| `docs/samples/M38_sample_issue_classification.json` | Sample issue with classification, supportability, cohort_impact, reproducibility_note. |
| `docs/samples/M38_sample_cohort_health.json` | Sample cohort health summary output. |
| `docs/M38E_M38H_TRIAGE_DELIVERABLE.md` | This deliverable. |

**Existing (no change):**  
`triage/models.py`, `triage/store.py`, `triage/evidence.py`, `triage/classification.py`, `triage/loop.py`, `triage/health.py`, `triage/clusters.py`, `triage/playbooks.py`, `tests/test_triage.py`, `docs/M38E_M38H_COHORT_EVIDENCE_TRIAGE_BEFORE_CODING.md`.

## 3. Exact CLI usage

```bash
# List issues (optional filters)
workflow-dataset triage list [--repo PATH] [--cohort ID] [--status new|investigated|reproduced|mitigated|blocked|resolved] [--limit N] [--json]

# Show one issue
workflow-dataset triage show --id ISSUE_ID [--repo PATH] [--json]

# Classify an issue
workflow-dataset triage classify --id ISSUE_ID [--repo PATH] [--severity critical|high|medium|low] [--impact-scope cohort|project|user|subsystem] [--reproducibility yes|no|partial|unknown] [--supported-surface] [--experimental-surface] [--recovery-exists] [--trust-violation] [--session-count N]

# Mark as reproduced (with optional steps)
workflow-dataset triage reproduce --id ISSUE_ID [--repo PATH] [--steps "step1, step2"]

# Mark as resolved
workflow-dataset triage resolve --id ISSUE_ID [--repo PATH]

# Cohort health summary
workflow-dataset cohort health [--repo PATH] [--cohort ID] [--json]
```

## 4. Sample evidence item

See `docs/samples/M38_sample_evidence_item.json`. Example:

```json
{
  "evidence_id": "ev_a1b2c3d4e5f6",
  "cohort_id": "broader_ops_q1",
  "session_id": "pilot_sess_001",
  "project_id": "founder_case_alpha",
  "workflow_or_context": "ops_reporting",
  "trust_mode": "supervised_operator",
  "kind": "session_feedback",
  "source_ref": "pilot_sess_001",
  "summary": "Session pilot_sess_001: blocking=1 warnings=2 degraded=false disposition=fix",
  "created_at_utc": "2025-03-16T14:00:00.000000+00:00",
  "extra": { "blocking_count": 1, "warnings_count": 2, "disposition": "fix" }
}
```

## 5. Sample issue classification

See `docs/samples/M38_sample_issue_classification.json`. Includes severity, impact_scope, reproducibility, affected_subsystems, supportability (supported_surface_involved, recovery_exists, trust_boundary_violation), cohort_impact (should_pause_cohort, should_downgrade), triage_status, reproducibility_note, operator_notes, route_target.

## 6. Sample cohort health output

See `docs/samples/M38_sample_cohort_health.json`. Example:

```json
{
  "cohort_id": "(all)",
  "open_issue_count": 3,
  "total_issue_count": 5,
  "evidence_count": 12,
  "highest_severity": "high",
  "repeated_issue_clusters": [["issue_abc123", "issue_def456"]],
  "unresolved_supported_surface_count": 2,
  "recommended_mitigation": "Triage high-severity issues; consider pausing new sessions until investigated.",
  "recommended_downgrade": false,
  "clusters_by_subsystem": [...],
  "operator_do_now": "Check recovery guide for executor; run reliability to reproduce.",
  "link_support": "workflow-dataset release triage",
  "link_recovery": "workflow-dataset recovery suggest --subsystem executor",
  "link_readiness": "workflow-dataset release report"
}
```

## 7. Exact tests run

```bash
cd /Users/prady/Desktop/Clap/workflow-llm-dataset
python -m pytest tests/test_triage.py -v
```

**Result:** 17 passed. Covers: evidence item creation, create_evidence_from_session, issue save/load, issue classification, classify_severity, group_duplicates, triage state transitions (new → reproduced → resolved), create_issue_from_evidence, cohort_health no-issues and with-issue, surface_new_evidence, mark_reproduced, build_clusters_by_subsystem, build_clusters_by_cohort, get_playbook_for_subsystem, get_playbook_for_issue, health_includes_clusters_and_links.

## 8. Exact remaining gaps for later refinement

- **Evidence from pilot/reliability/readiness**: Evidence is created via `create_evidence_from_session`, `create_evidence_from_reliability`, `create_evidence_from_readiness_blocker`; not yet wired to run automatically at end of pilot session or after reliability run / release readiness. Call these from pilot session end or from release/triage flows to backfill evidence.
- **Create issue from evidence in CLI**: No `triage create` that takes evidence_ids and creates an issue; use loop.create_issue_from_evidence from code or add `triage create --evidence-ids ev_1,ev_2`.
- **Route command**: `triage route --id X --target supportability|reliability|product` not added; use loop.route_issue from code or add CLI.
- **Investigated / mitigated / blocked**: Only reproduce and resolve are in CLI; add `triage investigate --id`, `triage mitigate --id`, `triage block --id` if desired.
- **Cohort profile from Pane 1**: Cohort health and triage do not yet read cohort profiles (e.g. supported surfaces) from the cohort profile layer; integrate with cohort/surface_matrix for unresolved_supported_surface accuracy.
- **Pilot session → evidence**: When a pilot session ends, optionally call create_evidence_from_session(blocking_issues=..., cohort_id=...) and optionally create_issue_from_evidence for blocking issues so triage list and cohort health stay current.
