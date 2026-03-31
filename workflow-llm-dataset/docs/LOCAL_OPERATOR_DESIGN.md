# Local Operator Design

## 1. Purpose
Define the first real macOS Local Operator Draft built on the shared core + adapter surfaces architecture.

This design covers:
- setup and permissions
- approved-folder registry
- workflow discovery
- tool/app discovery
- action proposals
- supervised execution
- surface shaping into CLI / Local Operator Console / shell snapshot

It does not attempt universal all-app autonomy in this phase.

## 2. Goals
- Allow real local testing on macOS
- Preserve local-first, privacy-first, approval-gated semantics
- Build a shared operator core reused by all surfaces
- Learn workflow structure from approved folders
- Infer relevant tools/apps
- Propose supervised local actions
- Execute bounded approved actions safely

## 3. Non-Goals
- Full autonomy across all apps
- Full-disk default scanning
- Universal app automation
- Cloud-first orchestration
- Replacing the current backend architecture
- Rebuilding working demo/UI layers unnecessarily

## 4. Architectural Choice
Chosen architecture: Shared core + adapter surfaces.

A unified `local_operator` core owns:
- setup and permission readiness
- approved folder registry and scope policy
- workflow ingestion and workflow-tree generation
- tool/app discovery
- action proposals
- supervised execution
- audit / rollback metadata

Surfaces consume shaped state through adapters:
- CLI
- Local Operator Console
- shell snapshot / browser desktop

## 5. Core State Model
Rich core state is stored under `data/local/operator/` and exposed as shaped summaries.

### 5.1 Session Trust
Time-boxed trusted session state controlling what execution may occur in the active session.

### 5.2 Capability Trust
Per-capability readiness, such as:
- Accessibility
- Automation
- Files/Folders
- Full Disk Access
- optional Screen Recording later

Capability trust gates whether adapters may execute.

### 5.3 Machine Readiness
Whether the machine has the capabilities required for a chosen operator action set.

### 5.4 Operator Readiness
Whether the operator has enough approved scope and discovered structure to be useful:
- approved folders exist
- workflow discovery ran
- relevant tools identified
- at least one action proposal available

## 6. Approved Folder Registry
Each entry stores:
- path
- allowed_operations
- recursive
- inherit_mode
- sensitivity_tag
- approval_source
- revocation_state
- approved_at
- reviewed_at
- expires_at

Registry behavior:
- only approved folders may be ingested
- revoked folders are skipped and surfaced explicitly
- inheritance rules must be visible and testable

## 7. Workflow Discovery
Workflow discovery must emit a formal workflow-tree / task-tree representation.

Each node should include:
- id
- parent id
- type
- title
- inferred tools
- inferred data dependencies
- evidence_refs
- evidence_summary
- confidence
- confidence_reason
- missing_evidence
- suggested next actions
- execution eligibility

Summary views are derived from the formal structure.

## 8. Tool/App Discovery
The tool registry must distinguish:
- installed
- inferred_from_evidence
- actively_relevant
- adapter_supported
- permission_ready
- adapter_mode

`adapter_mode` values:
- none
- simulated
- propose_only
- supervised_live
- session_trusted_live

Priority tool families:
- Finder
- Terminal
- Browser
- Excel / spreadsheets
- Tableau
- PowerPoint / Keynote
- VS Code / Cursor
- Figma
- Illustrator
- Photoshop
- Notion / notes apps
- SQL clients
- Python notebooks

## 9. Action Proposal Model
Each proposal must include:
- action_id
- title
- rationale
- evidence_refs
- risk_tier
- destructive_flag
- reversible_flag
- approval_requirement
- execution_scope
- scope_origin
- required_adapter
- required_permissions
- rollback_feasible
- rollback_method
- rollback_limitations

`scope_origin` values:
- approved_folder
- approved_app
- session_trust
- policy_default
- explicit_one_time_approval

## 10. Execution Model
Execution path:
- propose
- approve
- execute

Execution rules:
- no execution without explicit approval or pre-authorized session trust
- capability trust must be satisfied
- execution remains bounded by scope and adapter policy
- every execution emits audit metadata
- rollback feasibility is always recorded

## 11. Surface Shaping
Rich core state remains in `local_operator`.
Shaped summaries are exported to:
- CLI views
- Local Operator Console
- shell snapshot

No surface should invent state the core does not hold.

## 12. Error Handling Principles
- capability-specific errors, not generic failures
- revoked/invalid scope surfaced clearly
- missing adapter surfaced before execution
- evidence gaps degrade confidence, not total system failure
- last-good summary cache may be used in shell surfaces without overwriting raw core state

## 13. Validation Gates
1. Setup readiness
2. Approved-folder scope
3. Workflow discovery
4. Tool registry
5. Action proposals
6. Execution boundary
7. Surface coherence

## 14. First Local Test Path
- setup status
- permission checklist
- approve folder
- ingest approved scope
- discover tools
- propose actions
- approve a bounded action
- verify execution log + rollback feasibility
- verify shell snapshot reflects operator state

## 15. Future Expansion
Later phases may expand toward:
- broader app adapters
- richer workflow learning
- cross-platform support
- dedicated hardware packaging
- stronger enterprise policy controls
