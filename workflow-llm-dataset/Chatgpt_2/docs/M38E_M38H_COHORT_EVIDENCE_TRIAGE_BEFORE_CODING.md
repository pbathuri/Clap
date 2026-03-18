# M38E–M38H — Cohort Evidence Capture + Issue Triage Loop

## BEFORE CODING

### 1. What evidence/support/triage-like behavior already exists

| Area | Existing behavior |
|------|-------------------|
| **Pilot** | `PilotSessionRecord`: blocking_issues, warnings, degraded_mode, disposition (continue/fix/pause), operator_notes, user_feedback_summary; extra can hold cohort_id. Sessions stored locally; aggregate has evidence_quality, recurring_blockers. No first-class evidence or issue records. |
| **Reliability** | `ReliabilityRunResult`: outcome (pass/degraded/blocked/fail), failure_step_index, subsystem, reasons; `RecoveryCase` playbooks. No issue or evidence linkage. |
| **Release readiness** | `build_release_readiness()`: blockers, warnings, supportability (confidence, guidance); `build_triage_output()` / TRIAGE_TEMPLATE: reproducible_state_summary, recommended_next_support_action, steps_to_reproduce. No persisted issue or cohort-scoped evidence. |
| **Supportability** | Supportability report and triage template; support bundle (env, mesh, trust). No issue store or triage state machine. |
| **Review studio** | Intervention inbox (approval, blocked, replan, skills, policy, stalled); entity_refs for traceability. No issue/evidence link. |
| **Timeline** | review_studio/timeline: events with entity_refs, plan_ref; activity log only, no issue_id. |
| **Mission control** | product_state has cohort_recommendation, cohort_sessions_count from dashboard_data; [Release readiness] and reliability blocks. No cohort health or triage subsection. |

### 2. What is missing for a true first-cohort triage loop

- **Cohort-scoped evidence items**: First-class records (session_id, cohort_id, kind, summary, source_ref, timestamp) that can be linked to issues and filtered by cohort/project/workflow.
- **User-observed issue records**: Explicit issue (or triage item) with severity, reproducibility, affected subsystem, supportability impact, triage status (new / investigated / reproduced / mitigated / blocked / resolved), link to evidence_ids.
- **Degraded-mode and reproducibility**: Structured degraded-mode evidence and reproducibility notes (steps, recovery exists, trust-boundary violation) attached to issues.
- **Triage loop**: List → show → classify → reproduce → resolve with state transitions; optional grouping of duplicate/related issues; route to supportability / reliability / product review.
- **Cohort health summary**: Aggregate per cohort: open issue count, highest severity, repeated-issue clusters, supported-surface issue count, recommended mitigation or downgrade.
- **Mission control**: Visibility for highest-severity cohort issue, repeated cluster, cohort health, unresolved supported-surface count, recommended action.

### 3. Exact file plan

| Phase | Action | Path |
|-------|--------|------|
| A | Create | `src/workflow_dataset/triage/models.py` — CohortEvidenceItem, UserObservedIssue, DegradedModeEvidence, ReproducibilityNote, AffectedSubsystem, CohortImpact, SupportabilityImpact, TriageStatus (enum), OperatorNotes |
| A | Create | `src/workflow_dataset/triage/__init__.py` |
| B | Create | `src/workflow_dataset/triage/classification.py` — severity, impact_scope, reproducibility, supported_surface, trust_boundary_violation, recovery_exists, cohort_pause_downgrade |
| B | Create | `src/workflow_dataset/triage/evidence.py` — create_evidence_from_session/feedback/reliability, list_evidence (by cohort, project, limit) |
| C | Create | `src/workflow_dataset/triage/store.py` — save_issue, load_issue, list_issues, update_triage_status, group_duplicates_or_related |
| C | Create | `src/workflow_dataset/triage/loop.py` — surface_new_evidence, route_issue (supportability / reliability / product), state transitions |
| D | Create | `src/workflow_dataset/triage/health.py` — build_cohort_health_summary |
| D | Modify | `src/workflow_dataset/cli.py` — triage_group: list, show --id, classify --id, reproduce --id, resolve --id; cohort health |
| D | Modify | `src/workflow_dataset/mission_control/state.py` — triage_state: highest_severity_issue, repeated_cluster, cohort_health_summary, unresolved_supported_count, recommended_mitigation |
| D | Modify | `src/workflow_dataset/mission_control/report.py` — [Triage / Cohort health] section |
| E | Create | `tests/test_triage.py` — evidence creation, issue classification, duplicate grouping, triage transitions, cohort health, no-issue/overload states |
| E | Create | `docs/M38E_M38H_TRIAGE_DELIVERABLE.md` |

### 4. Safety/risk note

**Pilot/feedback and support bundles can contain operator and user text.** The triage/evidence store will persist only what is already captured (session refs, summaries, severity, subsystem). Keep evidence and operator_notes local; do not log or export raw quotes to external systems. Document storage path (e.g. data/local/triage/) and that no automatic egress occurs.

### 5. Evidence-capture boundaries

- **Will capture**: Session_id, cohort_id, project_id, workflow/context tags; kind (session_feedback, reliability_failure, readiness_blocker, degraded_mode); short summary or ref (no unbounded freeform); severity, reproducibility, affected_subsystem; triage status and operator notes (reproduction hints, mitigation).
- **Won't capture**: Full freeform text in a searchable evidence DB; PII beyond what pilot/feedback already store; automated scraping of external systems; raw logs or stack traces in evidence store (file refs only); evidence from outside defined sources (pilot, reliability, release_readiness).

### 6. What this block will NOT do

- Replace or duplicate full support ticket systems; add remote telemetry or external SaaS; implement full issue lifecycle (assign, SLA, close); define formal support tiers/entitlement; rebuild reliability/support/review from scratch; collect uncontrolled personal data; hide issue severity or supported-surface involvement. It will add a local-first evidence and triage loop that consumes existing pilot, reliability, and release_readiness outputs and exposes cohort health and recommended actions.
