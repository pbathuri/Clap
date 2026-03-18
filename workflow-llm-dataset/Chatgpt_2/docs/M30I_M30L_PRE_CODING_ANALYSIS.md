# M30I–M30L — User Release Readiness + Supportability Pack — Pre-coding analysis

## 1. What release/support/handoff behavior already exists

- **rollout/readiness.py** — `build_rollout_readiness_report()`: demo_ready, first_user_ready, blocks, operator_actions, experimental. Uses rollout tracker, package_readiness, acceptance, trust cockpit, env health. `format_rollout_readiness_report()` for text output.
- **rollout/support_bundle.py** — `build_support_bundle()`: writes env health, runtime mesh, starter kits, trust, acceptance, rollout state to data/local/rollout/support_bundle_<timestamp>. `build_support_bundle_summary_only()` for in-memory summary.
- **rollout/runbooks.py** — Runbooks under docs/rollout (OPERATOR_RUNBOOKS.md, RECOVERY_ESCALATION.md); list_runbooks, get_runbook_path, get_runbook_content.
- **rollout/issues.py** — `format_issues_report(bundle_summary)`: support/issue summary template (environment, runtime, acceptance, rollout, trust, steps to reproduce).
- **release/handoff_profiles.py** — internal_team, stakeholder, operator_archive; filter_artifacts_for_profile; build_approved_summary_lines for package handoff.
- **release/** — package_builder, dashboard_data, staging_board, report; CLI release verify, run, demo, package, report.
- **package_readiness/summary.py** — `build_readiness_summary()`: current_machine_readiness, ready_for_first_real_user_install, not_ready_reasons, experimental.
- **onboarding/** — onboarding_flow, product_summary, approval_bootstrap, operator_summary.
- **operator_quickstart/** — first_value_flow, quick reference.
- **No dedicated**: release-readiness *model* (status enum, blocker/warning types), single “user release pack” artifact, structured triage with “safe to continue / needs operator / needs rollback”, or mission-control release-readiness visibility.

## 2. What is missing for a real first-user release pack

- **Explicit release readiness model** — ReleaseReadinessStatus (ready | blocked | degraded), ReleaseBlocker, ReleaseWarning, SupportedWorkflowScope, KnownLimitation, OperatorHandoffStatus, SupportabilityStatus as first-class types.
- **User release pack** — One coherent pack: install profile ref, first-run guide, quickstart path, supported workflows list, known limitations, trust/approval posture explanation, recovery/support guide refs, diagnostics bundle refs (all as structured data + optional generated doc).
- **Triage/supportability** — Structured issue triage template (reproducible state summary, health/readiness, recommended next support action, guidance: safe_to_continue | needs_operator | needs_rollback).
- **Operator handoff pack** — Explicit “handoff pack” build that lists artifacts + summary for operator handoff (distinct from support bundle; can reference support bundle).
- **CLI** — `release readiness`, `release pack`, `release supportability`, `release triage --latest`, `release handoff-pack`.
- **Mission control** — Section: current release readiness, highest-severity blockers, known limitations, supportability confidence, handoff pack freshness.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `release_readiness/__init__.py` |
| Create | `release_readiness/models.py` — ReleaseReadinessStatus, ReleaseBlocker, ReleaseWarning, SupportedWorkflowScope, KnownLimitation, OperatorHandoffStatus, SupportabilityStatus. |
| Create | `release_readiness/readiness.py` — build_release_readiness(repo_root) → status, blockers, warnings, supported_scope, limitations; uses rollout/readiness, package_readiness, env, acceptance. |
| Create | `release_readiness/pack.py` — build_user_release_pack(repo_root) → install_profile, first_run_guide, quickstart_path, supported_workflows, known_limitations, trust_explanation, recovery_refs, diagnostics_refs. |
| Create | `release_readiness/supportability.py` — triage template, build_reproducible_state_summary(), build_supportability_report() (readiness + recommended_next_support_action + guidance). |
| Create | `release_readiness/handoff_pack.py` — build_handoff_pack(repo_root) → artifacts list, summary, generated_at. |
| Modify | `cli.py` — Under release_group: readiness, pack, supportability, triage --latest, handoff-pack. |
| Modify | `mission_control/state.py` — release_readiness section. |
| Modify | `mission_control/report.py` — [Release readiness] section. |
| Create | `tests/test_release_readiness.py` |
| Create | `docs/M30I_M30L_RELEASE_READINESS.md` |

## 4. Safety/risk note

- Readiness and supportability are advisory; no automatic gate that blocks installs or releases. Operators use reports to decide.
- Handoff pack and support bundle are local-only; no cloud or ticketing dependency.
- Known limitations and blockers are explicit so first users are not surprised.

## 5. What this block will NOT do

- No enterprise customer-success or SaaS help-desk tooling.
- No rebuild of onboarding/rollout/support; integrates with existing rollout readiness, support_bundle, runbooks, issues.
- No cloud/ticketing; all local-first.
- No automatic blocking of release; decision remains with operator.
