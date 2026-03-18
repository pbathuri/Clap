# M30H.1 — Degraded Mode Profiles + Safe Fallback Matrix

## Overview

Extension to the reliability harness (M30E–M30H):

- **Degraded mode profiles**: When a subsystem is unavailable, a profile describes what is disabled and what still works, with an explicit operator explanation.
- **Safe fallback matrix**: For each subsystem, rules define which flows to disable and which capability to use instead (e.g. simulate_only, local_templates_only).

## Sample degraded-mode profile

Profile ID: `packs_unavailable`

```yaml
# Packs unavailable (packs_unavailable)

Pack registry or behavior resolution unavailable.

## Disabled subsystems
packs, runtime_mesh

## Still works
  • golden_first_run (if install passed)
  • inbox
  • trust
  • planner compile (no pack context)
  • recovery suggest

## Disabled flows
  ✗ pack_install_behavior_query
  ✗ behavior_resolution
  ✗ workspace_command_query

## Operator explanation
Packs or runtime mesh unavailable. First-run and inbox/trust/planner may still work. Pack install path and workspace command query are disabled. Use recovery guide: broken_pack_state or missing_runtime_capability.
```

## Sample fallback matrix output

Subsystem: `trust`

```
# Safe fallback matrix

## When 'trust' is unavailable
  Disable: real apply, approval_gated_execution, review_inbox_approve_progress
  Fallback: simulate_only
  → Real apply and approval-gated execution disabled. Simulate-only, inbox, planner, workspace still work. Run recovery guide blocked_approval_policy.
```

Full matrix (one row per subsystem): install, distribution, packs, runtime_mesh, trust, human_policy, workspace, planner, executor, onboarding, inbox, progress.

## CLI

- `workflow-dataset reliability degraded-profile --id packs_unavailable`
- `workflow-dataset reliability degraded-profile --current`  # infer from latest run
- `workflow-dataset reliability fallback-matrix`
- `workflow-dataset reliability fallback-matrix --subsystem trust`

## Tests

Run: `python3 -m pytest tests/test_reliability.py -v` (includes 9 tests for M30H.1).
