# M32D.1 — Work Modes + Focus States

First-draft activity modes (writing, reviewing, planning, coding, coordination, admin) and focus-state inference with deeper “why” summaries. Extends M32 live-context; does not replace it.

## Activity modes

| Mode | Description | Typical signals |
|------|-------------|-----------------|
| writing | Docs, prose | .md, .txt, .docx, .rst, .tex |
| reviewing | Review/feedback | Mix of docs and plans, PDFs |
| planning | Plans, specs, spreadsheets | .xlsx, .csv, .md (plans) |
| coding | Source code | .py, .ts, .js, .go, .rs, etc. |
| coordination | Mixed comms/meetings | (Future: calendar, app) |
| admin | Config, ops | .yaml, .json, .toml, .env |

Inference is extension-based from recent file events; first match above threshold wins (coding ≥40%, writing ≥40%, planning ≥35%, admin ≥40%, else reviewing or unknown).

## Focus states

| State | Description | Typical signals |
|-------|-------------|-----------------|
| single_file | One or two files in one directory | distinct_files ≤2, distinct_dirs ≤1 |
| multi_file_same_dir | Multiple files in one directory | distinct_dirs == 1, multiple files |
| project_browse | Multiple dirs under one project | One project root, multiple dirs |
| scattered | Multiple projects or unrelated paths | Multiple project roots or many dirs |

## Sample work-mode output

From fused context (e.g. `live-context explain` or `live-context now`):

```
  activity_mode: coding
  activity_mode_reason: Recent files are mostly source code (12/15 events); extensions suggest coding.
```

Or for writing:

```
  activity_mode: writing
  activity_mode_reason: Recent files are mostly documents/prose (8/10 events); extensions suggest writing.
```

## Sample focus-state explanation

```
  focus_state: single_file
  focus_state_reason: Recent activity is concentrated on one or two files in the same directory; strong single-file or tight focus.
```

Or for scattered:

```
  focus_state: scattered
  focus_state_reason: Activity across multiple directories or projects; focus is scattered or switching.
```

## CLI

- `workflow-dataset live-context now` — includes activity_mode and focus_state in summary.
- `workflow-dataset live-context explain` — includes activity_mode, focus_state, activity_mode_reason, and focus_state_reason.

## Tests

Run: `pytest workflow-llm-dataset/tests/test_live_context.py -v`

New tests: test_activity_mode_coding, test_activity_mode_writing, test_focus_state_single_file, test_focus_state_scattered, test_activity_mode_and_focus_reason_present.

## Next recommended step

**Use activity_mode and focus_state in assist/copilot**: When generating suggestions or next actions, condition on `activity_mode` (e.g. coding → suggest run/test; writing → suggest outline or style) and `focus_state` (e.g. single_file → offer to expand scope; scattered → offer to narrow to one project). Wire these fields from persisted live context into the assist engine’s context payload.
