# M30I–M30L — User Release Readiness + Supportability Pack

## Purpose

Local-first release-readiness and supportability: decide whether the product is ready for a first-user release, package onboarding/runbooks/diagnostics/support artifacts, speed up issue triage, and define an operator handoff pack. No cloud or ticketing; all state from existing rollout, package_readiness, acceptance, env, mission_control.

## Concepts

- **Release readiness status** — `ready` | `blocked` | `degraded`, with blockers, warnings, supported scope, known limitations, supportability (confidence + guidance).
- **Release blocker** — Must resolve before first-user release; has source and remediation hint.
- **Release warning** — Does not block but operator should be aware.
- **Supported workflow scope** — Workflow IDs and description (e.g. from release reporting_workspaces).
- **Known limitations** — Documented limitations (e.g. manual approval, local-first).
- **Operator handoff status** — Freshness and path of handoff pack.
- **Supportability** — Confidence (high/medium/low), guidance (safe_to_continue | needs_operator | needs_rollback), recommended next support action.

## CLI

- `workflow-dataset release readiness` — Release readiness report (status, blockers, warnings, supportability).
- `workflow-dataset release pack` — User release pack summary (install profile, first-run, quickstart, supported workflows, limitations, trust, recovery/diagnostics refs).
- `workflow-dataset release supportability` — Supportability report (reproducible state, recommended action, guidance).
- `workflow-dataset release triage [--latest] [--json]` — Triage output for support (state summary, readiness, guidance).
- `workflow-dataset release handoff-pack [--output-dir DIR]` — Build operator handoff pack (writes handoff_pack.json and handoff_summary.md).

## Mission control

The mission-control report includes **[Release readiness]**: status, blocker_count, warning_count, supportability_confidence, guidance, highest_severity_blocker, handoff_pack_freshness. State key: `release_readiness`.

## Files

- `release_readiness/models.py` — ReleaseReadinessStatus, ReleaseBlocker, ReleaseWarning, SupportedWorkflowScope, KnownLimitation, OperatorHandoffStatus, SupportabilityStatus.
- `release_readiness/readiness.py` — build_release_readiness(), format_release_readiness_report(); uses rollout/readiness, package_readiness, env.
- `release_readiness/pack.py` — build_user_release_pack(), format_user_release_pack().
- `release_readiness/supportability.py` — build_reproducible_state_summary(), build_supportability_report(), build_triage_output(), TRIAGE_TEMPLATE.
- `release_readiness/handoff_pack.py` — build_handoff_pack(), get_handoff_pack_dir(), load_latest_handoff_pack().

## Remaining gaps

- Config-driven known limitations and supported scope (e.g. from release config or docs).
- Handoff pack diff vs previous (what changed since last handoff).
- Integration with Pane 2 reliability/recovery coverage (e.g. inject recovery playbooks into pack).
- Optional gate in install/upgrade flow that warns when release readiness is blocked (advisory only).
