# M23O — Daily Work Inbox + Context Digest

Daily “start here” view: work state summary, what changed, relevant jobs/routines, blocked items (with reason/trust/mode/blockers/outcome), reminders, top next action. Local-only; no autonomous execution.

## CLI usage

```bash
# Default: full inbox report (what changed, inbox items, blocked, reminders, top next)
workflow-dataset inbox
workflow-dataset inbox --repo-root /path/to/repo
workflow-dataset inbox --output report.txt

# Include per-item explanation in the main report
workflow-dataset inbox --explain

# Explain why each inbox item is shown now (reason, trust, mode, blockers, outcome)
workflow-dataset inbox explain

# Compare latest vs previous digest snapshot (newly appeared, dropped, escalated)
workflow-dataset inbox compare

# Persist current digest as snapshot (enables compare on next run)
workflow-dataset inbox snapshot
```

## Sample digest output

```
=== Daily Inbox (start here) ===
  2026-03-16T20:21:20+00:00

[What changed since last snapshot]
  Newly recommendable jobs: job_a
  Reminders count change: +1

[Relevant work]
  Jobs: weekly_status_from_notes, replay_cli_demo
  Routines: —

[Inbox items — reason, trust, mode, blockers, expected outcome]
  job weekly_status_from_notes
    reason: approval_blocked  trust: experimental  mode: simulate_only
    blockers: Real mode requires approval registry at data/local/capability_discovery/approvals.yaml.
    expected_outcome: Weekly status from notes
  job replay_cli_demo
    reason: simulate_only_available  trust: simulate_only  mode: simulate_only
    expected_outcome: Replay CLI demo task

[Blocked]
  job weekly_status_from_notes: Real mode requires approval registry at ...

--- Top next recommended action ---
  label: weekly_status_from_notes
  reason: Real mode requires approval registry at ...
  command: workflow-dataset onboard approve or workflow-dataset jobs run --id weekly_status_from_notes
--- Recommended next action ---
  Resolve blocked jobs (approvals or policy)
  copilot recommend then jobs run or approvals

(Operator-controlled. No automatic changes.)
```

## Sample explain-why-now output

```
=== Inbox: why these items now ===

  [job] weekly_status_from_notes
    reason: approval_blocked
    trust_level: experimental
    mode_available: simulate_only
    blockers: ['Real mode requires approval registry at ...']
    expected_outcome: Weekly status from notes

  [job] replay_cli_demo
    reason: simulate_only_available
    trust_level: simulate_only
    mode_available: simulate_only
    blockers: none
    expected_outcome: Replay CLI demo task

--- Top next ---
  weekly_status_from_notes: Real mode requires approval registry at ...
  command: workflow-dataset onboard approve or workflow-dataset jobs run --id weekly_status_from_notes
```

## Sample digest compare output

```
╭─────────────────────────────── Inbox compare ────────────────────────────────╮
│ # Digest compare (previous → latest)                                         │
│ ## Newly appeared                                                            │
│ job_b                                                                        │
│ ## Dropped                                                                   │
│ —                                                                            │
│ ## No longer blocked (escalated)                                             │
│ job_a                                                                        │
│ ## Summary                                                                   │
│ Newly appeared: job_b                                                        │
│ No longer blocked: job_a                                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Tests

```bash
pytest tests/test_daily_inbox.py tests/test_daily_inbox_m23o.py -v
```

Covers: digest structure (inbox_items, top_next_recommended), inbox item fields (reason, trust, mode, blockers, outcome), format_inbox_report sections, format_explain_why_now, blocked-state reporting, save/load digest snapshot, compare_digests (newly appeared, dropped, escalated), list_digest_snapshots, no-data behavior.

## Safety

- Read-only aggregation from existing local sources (job_packs, copilot, context, corrections, desktop_bench). No autonomous execution.
- Digest history under `data/local/context/digests/`. No cloud or telemetry.
- Ranking and reasons are explicit (reason, trust_level, mode_available, blockers, expected_outcome). No hidden scoring.
