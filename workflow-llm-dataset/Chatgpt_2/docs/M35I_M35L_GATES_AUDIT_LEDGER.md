# M35I–M35L Commit/Send/Apply Gates + Audit Ledger

First-draft high-trust gate-and-ledger system for the most sensitive operator actions (commit, send, apply). Local-first; no cloud audit; strengthens safety for personal operator mode.

## Purpose

- **Define explicit commit/send/apply review gates** — Stage a candidate, then approve/reject/defer with rationale.
- **Require stronger review for sensitive actions** — Sign-off requirement and optional authority tier / contract ref.
- **Durable audit ledger** — Append-only ledger linking actions to project, routine, contract, outcome; sign-off; execution result; rollback/recovery note.
- **Operator sign-off and rationale** — Every decision (approve/reject/defer) is recorded with rationale and optional operator_id.
- **Link to projects, routines, contracts, outcomes** — Ledger entries carry project_id, routine_id, contract_id, outcome_id, run_id, plan_ref.
- **Safe enough for higher-trust operator mode** — Visibility in mission control (pending gates, next sign-off, rejected/deferred, audit anomalies).

## Data

- **Location**: `data/local/sensitive_gates/`
- **Files**: `gates.json` (list of gates), `ledger.jsonl` (append-only audit entries).

## Models (summary)

- **SensitiveActionGate**: gate_id, action_kind (commit|send|apply), candidate (dict), status (pending|approved|rejected|deferred), review_rationale, created_utc, updated_utc.
- **Candidates**: CommitCandidate, SendCandidate, ApplyCandidate — each with label, target_ref, plan_ref, run_id, sign_off_requirement, blocked_reason, verification_requirement, project_id, routine_id, contract_id.
- **SignOffRequirement**, **ReviewRationale**, **BlockedGateReason**, **PostActionVerificationRequirement**.
- **AuditLedgerEntry**: entry_id, gate_id, action_kind, linked (LinkedProjectRoutineAction), authority_tier, approval_chain, sign_off, execution_result, rollback_recovery, verification, created_utc, label.

## CLI

```bash
# Gates
workflow-dataset gates list [--status pending|approved|rejected|deferred] [--json]
workflow-dataset gates show --id gate_123 [--json]
workflow-dataset gates stage --kind commit --label "Commit docs" [--target main] [--project founder_case_alpha]
workflow-dataset gates approve --id gate_123 [--rationale "LGTM"]
workflow-dataset gates reject --id gate_123 [--rationale "Not ready"]
workflow-dataset gates defer --id gate_123 [--rationale "After review"]

# Audit
workflow-dataset audit history [--limit 50] [--json]
workflow-dataset audit project --id founder_case_alpha [--limit 50] [--json]
```

## Mission control

- **State**: `sensitive_gates` — pending_gate_ids, pending_count, latest_signed_off_gate_ids, rejected_deferred_gate_ids, recent_audit_anomaly_entry_ids, next_required_signoff_gate_id, next_action.
- **Report**: `[Gates] pending=N next_signoff=… rejected_deferred=… audit_anomalies=… next: …`

## Flows

1. **Stage candidate**: `stage_candidate(action_kind, label, target_ref=..., project_id=..., ...)` → creates pending gate.
2. **Review**: `review_candidate(gate_id, "approved"|"rejected"|"deferred", rationale=..., append_to_ledger=True)` → updates gate and appends ledger entry.
3. **Record execution**: `record_execution_result(gate_id, outcome, outcome_detail=..., artifact_refs=...)` → append ledger entry with execution result.
4. **Record rollback**: `record_rollback_recovery(gate_id, note, recovery_action="rollback")` → append ledger entry with rollback note.
5. **Query**: `query_ledger_history(project_id=..., gate_id=..., limit=...)` → list ledger entries.

## What this does NOT do

- Enterprise compliance / SOC2 / attestation exports.
- Hidden logging or cloud auditing.
- Bypass trust/review boundaries.
- Execute commit/send/apply (only stages, records decisions, appends ledger).

## Remaining gaps for later refinement

- Wire executor/background_run to stage a gate when a commit/send/apply action is about to run (so every such action goes through the gate).
- Optional: verification workflow (post-action verification requirement → record VerificationOutcome).
- Optional: richer anomaly detection (e.g. pattern over ledger for repeated failures).
