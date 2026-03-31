# Supervised End-to-End Task Run Design (2026-03-18)

## Goal
Deliver a bounded, supervised task-run flow for the local operator:
- prompt intake
- plan generation
- approval
- execution through existing adapters
- artifact creation in approved scope
- persisted run summary and status

## Non-Goals
- no universal app automation
- no new cloud orchestration
- no redesign of local operator architecture
- no uncontrolled browser autonomy
- no new adapters beyond safe file write

## Existing Context
- local operator state + summary are already persisted
- approval registry gates execution
- file_ops and notes_document adapters have read-only real execution
- finder_open supports bounded real execution

## Proposed Approach (Option A)
Implement a minimal task plan/run pipeline inside `local_operator` using existing approval gates:
1. parse prompt into a bounded task plan
2. persist plan
3. require explicit approval
4. execute plan steps via `run_execute`
5. write a markdown artifact into the approved folder
6. persist run status + artifact path
7. expose a short latest-run summary in snapshot

## Data Model + Persistence
Store plans and runs under `data/local/operator/`:
- `task_plans/<plan-id>.json`
- `task_runs/<run-id>.json`

Operator state keeps only the latest pointers:
- `last_task_plan_id`
- `last_task_run_id`
- `last_task_run` summary (prompt, status, artifact path, timestamps)

## Planning (Prompt -> Plan)
Planner is heuristic and bounded:
- Select approved folder by matching prompt text to folder name/path.
- Fallback to the first active approved folder.
- If no approved folder exists, return `unsupported`.

Plan steps (minimum viable):
1. list directory (`file_ops.list_directory`)
2. optionally summarize README/notes (`notes_document.summarize_text_for_workflow`)
3. write markdown artifact (`file_ops.write_file`) to `<approved>/task-runs/<run-id>.md`

Unsupported prompts return a plan with status `unsupported` and no execution allowed.

## Approval + Execution
Execution is supervised:
- `run-task` requires explicit plan approval + `--approved` flag
- execution uses `run_execute` so approval registry gates apply
- execution stops if any step fails

## Artifact Content
Artifact is markdown and includes:
- original prompt
- source scope (approved folder path)
- summary/result
- suggested next steps
- provenance/evidence
- generation timestamp

## CLI Surface
Add new commands under `workflow-dataset local`:
- `plan-task --prompt "..."`
- `approve-task --plan-id <id>`
- `run-task --plan-id <id> --approved`
- `task-status [--run-id <id>]`

## Snapshot + Shell
If low-impact, expose latest task run in `local_operator_summary`:
- latest prompt
- run status
- artifact path
- success/failure

No new UI surfaces in this pass; only shaping if easy.

## Error Handling
- no approved folders -> plan unsupported
- unapproved run -> hard stop with clear message
- execution gate failures -> reported in run status
- artifact write failure -> run status `failed`, include reason

## Testing
Add tests for:
- prompt -> plan generation
- plan persistence
- no execution without approval
- approved scope enforcement
- artifact generation
- run summary persistence
- unsupported prompt handling
- snapshot summary inclusion (if integrated)
