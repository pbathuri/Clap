# Local Operator Target Modules

## New or expanded package
`src/workflow_dataset/local_operator/`

Recommended modules:

### Core state / schemas
- `models.py`
  - setup state
  - trust state
  - readiness state
  - approved folder entry
  - workflow-tree node
  - tool registry item
  - action proposal
  - execution log

- `state_store.py`
  - load/save local operator state
  - file layout under `data/local/`

### Setup / permissions
- `setup.py`
  - setup status
  - capability trust checks
  - machine readiness
  - operator readiness

- `permissions.py`
  - macOS capability checks
  - permission-specific diagnostics

### Approved folders
- `approved_folders.py`
  - add
  - list
  - revoke
  - validate
  - scope policy handling

### Discovery
- `ingest.py`
  - approved-scope scan
  - file tree traversal

- `workflow_tree.py`
  - workflow-tree generation
  - task-tree generation
  - summary derivation

- `tool_discovery.py`
  - tool evidence parsing
  - installed/inferred/relevant/support classification

### Proposals and execution
- `action_proposals.py`
  - proposal generation
  - risk tiering
  - scope origin
  - adapter requirements

- `execution.py`
  - propose → approve → execute control
  - pre-execution checks
  - audit/rollback feasibility recording

### Adapters
- `adapters/finder.py`
- `adapters/terminal.py`
- `adapters/browser.py`
- `adapters/filesystem.py`

### Snapshot / shaping
- `summary.py`
  - shaped summary for CLI, console, and shell

- `validation.py`
  - surface coherence gate

## CLI integration
Likely touch:
- `src/workflow_dataset/cli.py`

Add or extend command groups such as:
- `workflow-dataset setup ...`
- `workflow-dataset local ...`

## Console integration
Likely touch existing Local Operator Console or related TUI module if present.

## Shell integration
Likely touch:
- edge desktop snapshot builder
- live adapter path
- investor/browser desktop shell view model or snapshot parser

## Persistence targets
Under `data/local/`, likely:
- `local_operator/state.json`
- `local_operator/approved_folders.*`
- `local_operator/workflow_tree.*`
- `local_operator/tool_registry.*`
- `local_operator/action_proposals.*`
- `agent/action_log.jsonl`

## Tests
Recommended:
- `tests/test_local_operator_ingest.py`
- `tests/test_local_operator_workflow_tree.py`
- `tests/test_local_operator_tool_discovery.py`
- `tests/test_local_operator_action_proposals.py`
- `tests/test_local_operator_execution.py`
- fixture-based ingestion tests
- surface coherence tests if existing test structure supports them
