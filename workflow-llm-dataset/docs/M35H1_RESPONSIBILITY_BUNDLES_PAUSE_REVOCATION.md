# M35H.1 — Responsibility Bundles + Revocation / Safe Pause Flows

First-draft extension to personal operator mode: reusable responsibility bundles, emergency/safe pause, revocation flows, and clearer work-impact explanations (what will stop, continue, or require human takeover).

## 1. Files modified

- **`src/workflow_dataset/cli.py`** — Added `operator_mode_group` and commands: `operator-mode status`, `operator-mode bundles`, `operator-mode pause`, `operator-mode revoke`, `operator-mode explain-impact`, `operator-mode pause-revocation-report`.

## 2. Files created

- **`src/workflow_dataset/operator_mode/models.py`** — DelegatedResponsibility, OperatorModeProfile, SuspensionRevocationState, OperatorModeSummary; M35H.1: ResponsibilityBundle, PauseState (PauseKind: none/emergency/safe), RevocationRecord, WorkImpactExplanation, PauseRevocationReport.
- **`src/workflow_dataset/operator_mode/store.py`** — Persist profiles, responsibilities, bundles, pause_state.json, state.json (suspension/revocation), revocation_history.json.
- **`src/workflow_dataset/operator_mode/bundles.py`** — create_bundle, add_responsibility_to_bundle, remove_responsibility_from_bundle, resolve_bundle_responsibility_ids.
- **`src/workflow_dataset/operator_mode/pause_revocation.py`** — set_emergency_pause, set_safe_pause, clear_pause, revoke_responsibility, revoke_bundle, build_pause_revocation_report.
- **`src/workflow_dataset/operator_mode/explain.py`** — explain_work_impact(repo_root, responsibility_ids, bundle_ids) → WorkImpactExplanation (what_stops, what_continues, what_requires_human).
- **`src/workflow_dataset/operator_mode/__init__.py`** — Public API exports.
- **`data/local/operator_mode/bundles/founder_morning_ops.json`** — Sample responsibility bundle.
- **`data/local/operator_mode/responsibilities/founder_morning_digest.json`**, **founder_approval_sweep.json**, **founder_blocked_followup.json** — Sample responsibilities.
- **`data/local/operator_mode/sample_pause_revocation_report.json`** — Sample pause/revocation report (reference).
- **`tests/test_operator_mode.py`** — 13 tests: models, bundle create/add/resolve, emergency/safe pause, clear, revoke responsibility/bundle, explain_work_impact, build_pause_revocation_report.
- **`docs/M35H1_RESPONSIBILITY_BUNDLES_PAUSE_REVOCATION.md`** — This document.

## 3. Sample responsibility bundle

**`data/local/operator_mode/bundles/founder_morning_ops.json`**:

```json
{
  "bundle_id": "founder_morning_ops",
  "label": "Founder morning operations",
  "description": "Recurring morning responsibilities: digest, approval sweep, blocked-work follow-up.",
  "responsibility_ids": [
    "founder_morning_digest",
    "founder_approval_sweep",
    "founder_blocked_followup"
  ],
  "created_utc": "",
  "updated_utc": ""
}
```

## 4. Sample pause/revocation report

**`data/local/operator_mode/sample_pause_revocation_report.json`** (and output of `operator-mode pause-revocation-report --json`):

- **pause_state**: `kind: safe`, `reason: Safe pause — only digest continues; approval sweep and follow-up stopped until cleared.`, `safe_continue_responsibility_ids: ["founder_morning_digest"]`.
- **revocation_records**: One record revoking bundle `legacy_weekly_ops` with `revoked_responsibility_ids: ["legacy_weekly_digest", "legacy_approval_sweep"]`.
- **impact**: `what_stops`: ["Founder approval sweep", "Founder blocked follow-up"]; `what_continues`: ["Founder morning digest"]; `what_requires_human`: suspended items with “resume to continue”; `summary`: one-line operator-facing summary.

## 5. Exact tests run

```bash
pytest tests/test_operator_mode.py -v
```

**Result**: 13 passed (models, save/load bundle, create_bundle + add_responsibility, resolve_bundle_responsibility_ids, emergency_pause, safe_pause, clear_pause, revoke_responsibility, revoke_bundle, explain_work_impact no pause / with emergency pause, build_pause_revocation_report).

## 6. Next recommended step for the pane

- **Mission control integration**: Add an **operator_mode_state** slice in `mission_control/state.py` (pause kind, revoked/suspended counts, next recommended action) and a **[Operator mode]** section in `mission_control/report.py` so the dashboard shows pause status, revocation count, and a one-line work-impact summary (e.g. “Safe pause: 2 stop, 1 continue; 2 require human”).
- **Resume flow**: Implement `operator-mode resume --id <responsibility_id>` to clear suspension for a single responsibility (remove from suspended_ids in SuspensionRevocationState). M35H.1 only added revoke; resume was left for a follow-up.
- **Re-delegate after revoke**: Add `operator-mode delegate --id <responsibility_id>` (or “re-delegate”) to create or re-enable a responsibility and remove it from revoked_ids so it can run again under the cycle.
