# M35I–M35L Commit/Send/Apply Gates + Audit Ledger — Before Coding

## 1. What review/audit-like pieces already exist

| Area | What exists |
|------|-------------|
| **trust/** | **Authority tiers** (tiers.py): COMMIT_OR_SEND_CANDIDATE tier with `approval_required`, `audit_required`; allowed/forbidden action classes. **TrustedRoutineContract** (contracts.py): `required_approvals`, `required_review_gates`, `audit_required`. **Release gates** (release_gates.py): advisory checks (no_regressions, approval_registry_ready, etc.) — not per-action. **Cockpit schema** (schema.py): ApprovalReadiness, BenchmarkTrust. |
| **executor/** | **ActionEnvelope**: `approvals_required`, `checkpoint_required`, `blocked_reason`. **CheckpointDecision**: proceed / cancel / defer + note. **ExecutionRun**: `checkpoint_decisions`, `approval_required_before_step`. **BlockedStepRecovery**: retry/skip/substitute/record_correction. |
| **review_studio/** | **Timeline events**: EVENT_ACTION_QUEUED, EVENT_ACTION_APPROVED, EVENT_ACTION_REJECTED, EVENT_ACTION_DEFERRED, EVENT_EXECUTOR_*; **intervention items**: approval_queue, blocked_run, artifact_review, etc. **Store**: inbox snapshot, operator_notes. |
| **automation_inbox/** | **Flows**: accept, archive, dismiss, escalate, note; **store**: save_decision, get_latest_decision, operator_notes. **Digests/briefs**: morning, continuity, handoff. |
| **background_run/** | **GatingResult**: allowed, simulate_only, approval_required, degraded_fallback; **evaluate_background_policy** (job + work_state + human_policy). |
| **outcomes/** | **SessionOutcome**, **TaskOutcome**, **BlockedCause**; store: save_session_outcome, get_session_outcome, outcome_history. |
| **release_readiness/** | **RolloutGate**, **evaluate_gate** (env, acceptance, trust_approval_ready, etc.) — rollout/launch level. |
| **capability_discovery/** | **ApprovalRegistry**: approved_paths, approved_apps, approved_action_scopes (approvals.yaml). |
| **human_policy/** | **PolicyEvalResult**: simulate_only, blocked; action_class_policies, overrides. |
| **project_case/** | **Project**, list_projects, load_project; project_id used in digests/outcomes. |

So: tiers and contracts define *what* requires approval/audit; executor has checkpoints and blocked recovery; review_studio has timeline and inbox; automation_inbox has decisions and notes; outcomes persist session/task outcomes; approval registry and human_policy gate execution. There is no **explicit per-action gate object** for commit/send/apply and no **durable audit ledger** tying sensitive actions to sign-off, rationale, execution result, and rollback.

---

## 2. What is missing for true commit/send/apply gates and auditability

- **Explicit sensitive action gate**: A first-class record for a single commit/send/apply *candidate* that can be staged, then approved/rejected/deferred with a required rationale and optional verification.
- **Commit / send / apply candidate types**: Tiers reference COMMIT_OR_SEND_CANDIDATE but there is no staged “candidate” with action_kind (commit | send | apply), sign-off requirement, and blocked reason.
- **Sign-off requirement and review rationale**: CheckpointDecision has a note; no unified “sign-off + rationale” model for “I approved this commit because…” with optional authority_tier and contract_ref.
- **Blocked gate reason**: No structured BlockedGateReason (policy_denied, approval_missing, scope_mismatch, etc.) on the gate itself.
- **Post-action verification requirement**: Not modeled (e.g. “verify artifact exists after apply”).
- **Durable audit ledger**: No single append-only ledger that links: sensitive action → project_id, routine_id, contract_id, outcome_id; approval chain; operator sign-off; execution result; rollback/recovery note; verification outcome. Timeline and outcomes are event/outcome oriented; they are not a unified audit trail for high-trust operations.
- **Query by project/routine**: No “audit history for project X” or “ledger entries for routine Y” API.
- **Mission control visibility**: No aggregated “pending sensitive gates”, “latest signed-off actions”, “rejected/deferred”, “recent audit anomalies”, “next required human sign-off”.

---

## 3. Exact file plan

| Path | Purpose |
|------|--------|
| `src/workflow_dataset/sensitive_gates/__init__.py` | Package exports. |
| `src/workflow_dataset/sensitive_gates/models.py` | Phase A + B: SensitiveActionGate, CommitCandidate, SendCandidate, ApplyCandidate, SignOffRequirement, ReviewRationale, BlockedGateReason, PostActionVerificationRequirement; AuditLedgerEntry, LinkedProjectRoutineAction, ApprovalChainEntry, AuthorityTierRef, OperatorSignOff, ExecutionResult, RollbackRecoveryNote, VerificationOutcome. |
| `src/workflow_dataset/sensitive_gates/store.py` | Persist gates (list, get, save); append-only ledger (append_entry, list_entries, by_project, by_gate_id). |
| `src/workflow_dataset/sensitive_gates/flows.py` | stage_candidate, review_candidate (approve/reject/defer), record_execution_result, record_rollback_recovery, query_ledger_history. |
| `src/workflow_dataset/sensitive_gates/cli.py` | Typer group registration only; commands live in cli.py. |
| `src/workflow_dataset/cli.py` | Add `gates_group` (gates list, show, approve, reject, defer), `audit_group` (audit history, audit project). |
| `src/workflow_dataset/mission_control/state.py` | Add block: pending_sensitive_gates, latest_signed_off_actions, rejected_deferred_gates, recent_audit_anomalies, next_required_signoff. |
| `src/workflow_dataset/mission_control/report.py` | Add [Gates] / [Audit] lines when state present. |
| `tests/test_sensitive_gates.py` | Gate creation, sign-off/reject/defer flows, ledger entry creation, project/routine linkage, rollback note, blocked gate. |
| `docs/M35I_M35L_GATES_AUDIT_LEDGER.md` | First-draft spec and usage. |

Data: `data/local/sensitive_gates/` — `gates.json` (active/pending gates), `ledger.jsonl` or `ledger.json` (append-only entries).

---

## 4. Safety/risk note

- **Local-only**: All data under repo `data/local/sensitive_gates`. No cloud or remote audit.
- **No bypass**: Gates and ledger do not replace or bypass trust/tiers, approval registry, or human_policy; they add an explicit gate-and-ledger layer on top. Executor and background_run continue to use existing gating.
- **Visibility**: Pending gates and next required sign-off are visible in mission control so the operator is always aware of what is waiting.
- **Risk**: If callers bypass the gate layer and perform commit/send/apply without staging, those actions will not appear in the ledger until we add integration points (future work). This block defines the gate-and-ledger system; wiring every execution path to it is a later refinement.

---

## 5. What this block will NOT do

- **Enterprise compliance**: No SOC2/ISO-style controls, no attestation exports, no cloud audit pipeline.
- **Hidden logging**: All ledger and gate state is local, inspectable, and operator-facing.
- **Cloud auditing**: No upload or sync of audit data.
- **Bypassing trust/review**: Does not weaken approval_required or audit_required semantics in tiers/contracts.
- **Rebuilding review/timeline/outcomes**: Reuses project_case, outcomes, and existing IDs; does not replace review_studio or automation_inbox.
- **Auto-execution**: Does not execute commit/send/apply; only stages, records decisions, and appends to the ledger. Execution remains with executor/background_run and their existing gating.
