# Local Operator Implementation Plan

## Objective
Implement the first macOS Local Operator Draft in a way that is:
- testable now
- bounded
- safe
- reusable by CLI, console, and shell

## Phase 1 — Core data structures and persistence
Implement:
- setup state model
- capability trust model
- session trust model
- machine readiness model
- operator readiness model
- approved-folder registry
- workflow-tree schema
- tool registry schema
- action proposal schema
- execution log schema

Persist under `data/local/`.

### Acceptance criteria
- data models exist
- persistence read/write works
- schemas support the locked design fields
- tests cover basic read/write and state transitions

## Phase 2 — Setup and approved-folder flows
Implement:
- setup status command/surface
- permission readiness evaluation
- approved-folder add/list/revoke commands
- registry validation
- allowed operations + inheritance handling

### Acceptance criteria
- user can register an approved folder
- registry stores metadata correctly
- revoked folders are surfaced and excluded from ingestion
- setup state is inspectable from CLI and/or console

## Phase 3 — Workflow discovery
Implement:
- approved-scope scan
- project-root inference
- workflow-tree / task-tree emission
- evidence refs + confidence reasoning
- summary derivation from formal tree

### Acceptance criteria
- running discovery produces a formal tree
- provenance fields are populated
- summary view can be derived
- mixed test fixture works

## Phase 4 — Tool discovery
Implement:
- environment + evidence-based tool discovery
- classification fields
- adapter mode tracking
- relevance scoring

### Acceptance criteria
- tool registry can represent installed/inferred/relevant/support/permission states
- discovery works on fixture evidence
- no tool is falsely marked installed or adapter-supported without evidence

## Phase 5 — Action proposals
Implement:
- proposal generation from workflow-tree + tool registry + approved scope
- risk tiering
- scope origin
- adapter and permission requirements
- rollback feasibility metadata

### Acceptance criteria
- proposal records are generated
- each proposal includes the required schema fields
- unsafe or unsupported proposals are blocked before execution

## Phase 6 — Bounded macOS execution adapters
Implement first-draft adapters for:
- Finder
- Terminal
- Browser
- safe file operations within approved scope

Use:
- osascript / AppleScript where appropriate
- explicit permission checks
- no uncontrolled background autonomy

### Acceptance criteria
- at least one bounded real local action can be executed safely
- execution logs are written
- rollback feasibility is recorded
- blocked executions fail clearly and safely

## Phase 7 — Surface integration
Expose operator state to:
- CLI
- Local Operator Console
- shell snapshot / browser desktop

### Acceptance criteria
- setup state is visible
- approved folders are visible
- workflow summary is visible
- tool inventory is visible
- action proposals are visible
- execution state is visible

## Phase 8 — Local runbook and validation
Create:
- local setup instructions
- local test runbook
- reset/retry steps
- failure mode guidance

### Acceptance criteria
- user can rerun the local experiment
- smallest next fix is obvious if something fails
