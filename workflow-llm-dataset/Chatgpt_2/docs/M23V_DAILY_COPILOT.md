# M23V — Daily Copilot Surface + Macro Execution + Trust/Release Cockpit

## Overview

This phase adds the visible daily-use product shell: daily inbox/digest, macro composition and checkpointed runs, trust/evidence cockpit, and package/install readiness reporting. All operator-controlled; no autopilot or approval bypass.

## CLI usage

```bash
# Daily inbox / digest
workflow-dataset inbox
workflow-dataset inbox --output /path/to/inbox.txt
workflow-dataset inbox --repo-root /path/to/repo

# Macros (routines)
workflow-dataset macro list
workflow-dataset macro list --repo-root /path
workflow-dataset macro preview --id morning_ops
workflow-dataset macro preview --id morning_ops --mode simulate
workflow-dataset macro run --id morning_ops --mode simulate
workflow-dataset macro run --id morning_ops --mode real
workflow-dataset macro run --id morning_ops --mode simulate --continue-on-blocked

# Trust cockpit
workflow-dataset trust cockpit
workflow-dataset trust cockpit --output /path/to/trust.txt
workflow-dataset trust release-gates

# Package readiness
workflow-dataset package readiness-report
workflow-dataset package readiness-report --output /path/to/readiness.txt
```

## Sample inbox output

```
=== Daily Inbox (start here) ===

[Relevant work]
  Jobs: weekly_status, notes_summary, job_a
  Routines: morning_ops, evening_check

[Blocked]
  job daily_export: Real mode requires approval registry at data/local/capability_discovery/approvals.yaml.

[Reminders due]
  Morning check-in
  Evening sync

[Approvals needing refresh]
  daily_export, notes_summary

[Recent successful runs]
  cprun_abc123  simulate  2025-03-16T10:00:00Z
  weekly_status  real  2025-03-15T09:00:00Z

--- Recommended next action ---
  Review reminders and run a routine or job
  copilot reminders due

(Operator-controlled. No automatic changes.)
```

## Sample macro definition + preview

Macros are routines (YAML under `data/local/copilot/routines/`). Example `morning_ops.yaml`:

```yaml
routine_id: morning_ops
title: Morning operations
description: Daily morning check
job_pack_ids: [weekly_status, notes_summary]
stop_on_first_blocked: true
simulate_only: true
expected_outputs: []
```

Preview:

```
$ workflow-dataset macro preview --id morning_ops --mode simulate

=== Macro preview: morning_ops ===

Plan ID: abc123...
Mode: simulate
Jobs: weekly_status, notes_summary

[Step previews]
  1. weekly_status — simulate
  2. notes_summary — simulate

(No execution. Use: workflow-dataset macro run --id morning_ops --mode simulate)
```

## Sample trust cockpit output

```
=== Trust / evidence cockpit ===

[Benchmark trust]
  latest_run: run_001  outcome: pass  trust_status: usable_with_simulation_only
  simulate_only_coverage: 1.0  trusted_real_coverage: 0.0
  next: run desktop-bench run-suite --suite desktop_bridge_core --mode simulate

[Approval readiness]
  registry_exists: True  path: data/local/capability_discovery/approvals.yaml
  approved_paths: 2  approved_action_scopes: 3

[Job / macro trust state]
  total_jobs: 5  simulate_only: 2  trusted_for_real: 2  approval_blocked: 1
  recent_successful: 3  routines: 2

[Unresolved corrections]
  proposed_updates: 0
  review_recommended: 

[Release gate status]
  unreviewed: 0  package_pending: 0  staged: 0
  release_readiness_report_exists: True

(Operator-controlled. No automatic changes.)
```

## Sample readiness report

```
=== Package / install readiness report ===

[Current machine readiness]
  ready: True  passed: 12/12  failed_required: 0  optional_disabled: 1

[Current product readiness]
  release_readiness_report: present
  unreviewed workspaces: 0  package_pending: 0  staged: 0

--- First real-user install ---
  ready: True
  + Machine readiness checks passed.
  + Release readiness report present.

[What remains experimental]
  - Desktop benchmark: usable_with_simulation_only
  - Macros/routines: run in simulate first; real mode requires approvals.
  - Corrections and propose-updates: operator review required before apply.

(No installer changes. Report only.)
```

## Mission control integration

`workflow-dataset mission-control` now includes additive sections:

- **[Inbox]** — relevant_jobs_count, relevant_routines_count, blocked_count, reminders_due_count, recommended_next_action
- **[Trust cockpit]** — benchmark_trust_status, approval_registry_exists, release_gate_staged_count
- **[Package readiness]** — machine_ready, ready_for_first_install

## Safety

- No auto-run: inbox and macro run are explicit; reminders do not trigger execution.
- No approval bypass: real mode still requires approval registry and job policy.
- Local-only: all data under `data/local/`; no cloud or telemetry.
- Pane contracts: runtime/profile consumed via abstract interfaces only.

## Tests

```bash
PYTHONPATH=src python3 -m pytest tests/test_daily_inbox.py tests/test_macros.py tests/test_trust_cockpit.py tests/test_package_readiness.py -v
```

## Files created / modified

- **Created:** `src/workflow_dataset/daily/` (inbox, inbox_report), `macros/` (schema, runner, report), `trust/` (cockpit, report), `package_readiness/` (summary, report)
- **Modified:** `cli.py` (inbox, macro, trust, package commands), `mission_control/state.py` (daily_inbox, trust_cockpit, package_readiness blocks), `mission_control/report.py` (Inbox, Trust cockpit, Package readiness sections)
- **Tests:** `test_daily_inbox.py`, `test_macros.py`, `test_trust_cockpit.py`, `test_package_readiness.py`

## Next step for the pane

- **Pane 1 (runtime/backend/integration registry):** Provide backend_registry and integration_registry interfaces so mission_control and package_readiness can optionally show “missing runtime” or “recommended backend” from the registry without blocking.
- **Pane 2 (profile/domain pack/specialization recipe):** Provide domain-pack or specialization recipe interface so daily inbox can optionally include “domain-pack-aware suggestions” via the existing placeholder in `_get_domain_pack_suggestions()`.
