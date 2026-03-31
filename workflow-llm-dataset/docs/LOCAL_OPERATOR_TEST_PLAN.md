# Local Operator Test Plan

## Unit tests
### Models / schema
- required fields present
- serialization/deserialization
- trust/readiness state transitions

### Approved-folder registry
- add folder
- revoke folder
- inheritance rules
- metadata persistence
- revoked folder exclusion

### Workflow discovery
- formal tree emitted
- provenance fields populated
- evidence refs stored
- confidence reasoning present
- summary derived from formal tree

### Tool discovery
- installed vs inferred distinction
- relevance classification
- adapter support classification
- permission-ready classification
- adapter_mode correctness

### Action proposals
- risk tier present
- approval requirement present
- scope origin present
- required adapter present
- rollback feasibility present

### Execution controller
- no execute without approval
- blocked on missing capability trust
- blocked on revoked scope
- execution logs written
- rollback feasibility recorded

## Integration tests
- approved folder → ingestion → workflow-tree path
- workflow-tree + tool registry → action proposals
- proposal + approval + adapter → bounded execution
- core state → shaped snapshot path
- CLI / shell summary coherence where applicable

## Fixture tests
Use mixed fixtures including:
- docs
- code
- spreadsheets
- decks
- notebooks
- tool evidence files such as:
  - `.code-workspace`
  - `.fig`
  - `.ipynb`
  - `.sql`

## Manual local validation
- setup readiness visible
- approved folder can be registered
- workflow discovery runs
- tool discovery runs
- at least one safe proposal appears
- at least one bounded safe action can be executed
