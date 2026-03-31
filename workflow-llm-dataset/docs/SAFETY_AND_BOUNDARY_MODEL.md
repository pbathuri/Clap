# Safety and Boundary Model (Repo-Grounded)

This system is **local-first**, **privacy-first**, and **approval-gated**. The safety model is enforced by explicit policy layers and a supervised execution pipeline.

## Core safety posture
- **Simulation-first** before live actions.
- **Explicit approvals** for sensitive or destructive operations.
- **Auditability** via queues, history, and trust presets.
- **Scope-bounded** access (approved folders, session trust).

## Enforcement layers (existing code)
- **Approval queue**: `src/workflow_dataset/supervised_loop/*`
- **Trust tiers & presets**: `src/workflow_dataset/trust/*`
- **Governance & review domains**: `src/workflow_dataset/governance/*`, `review_domains/*`
- **Sensitive gates**: `src/workflow_dataset/sensitive_gates/*`
- **Policy & operator controls**: `src/workflow_dataset/human_policy/*`, `supervisory_control/*`

## Execution tiers (applies today)
1. **Read-only inspection**
2. **Proposed actions**
3. **Supervised execution**
4. **Session-trusted supervised execution within approved scope**

## Desktop control boundaries (macOS-first)
- Explicit permission gating (Files & Folders, Full Disk, Accessibility, Automation as required).
- Folder access must be visible, revocable, and logged.
- No hidden autonomy; no silent self-modification.

## Investor demo safety alignment
- Investor prototype is **presenter-safe** (mock/cached/live are explicit).
- Live adapter pipeline exposes per-field provenance (`adapter_meta`) when enabled.
- UI copy avoids implying live when source is mock or stale.

## Known gaps
- Some safety semantics are present but not unified into a single workflow-tree node policy model.
- Boot readiness tiers in the UI are presentation-only and not wired to real readiness checks.
