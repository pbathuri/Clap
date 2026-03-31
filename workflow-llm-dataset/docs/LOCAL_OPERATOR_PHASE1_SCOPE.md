# Local Operator Phase 1 Scope

## Goal
Deliver the smallest real macOS Local Operator Draft that can be tested on the user’s laptop.

## In scope
- core local_operator schemas and persistence
- setup/capability trust status
- session trust state
- approved-folder registry
- workflow discovery over approved scope
- tool discovery from evidence + environment hints
- action proposal generation
- one bounded execution path for safe local actions
- shell snapshot integration for operator summary
- CLI test path

## Bounded real execution target
At minimum, support one or more of:
- open approved folder in Finder
- open a relevant file/document
- open a browser URL
- open a safe workspace context
- perform a non-destructive file operation inside approved scope

## Out of scope for Phase 1
- full universal desktop automation
- Adobe deep automation
- Tableau deep automation
- spreadsheet editing autonomy
- unsupervised execution
- full-disk default ingestion
- cross-platform support
- broad enterprise deployment
- rich app-specific adapters beyond the first bounded set

## Repeatable runbook (Phase 1.5)

See **[LOCAL_OPERATOR_RUNBOOK.md](./LOCAL_OPERATOR_RUNBOOK.md)** for a clean end-to-end CLI path (approved-folders → ingest → propose → execute → summary).

## Success criteria
Phase 1 is successful if:
- setup readiness can be inspected
- approved folders can be registered
- workflow discovery emits a formal tree
- tools can be classified
- proposals can be generated
- at least one bounded safe action can be approved and executed
- shell/CLI can show the resulting operator state
