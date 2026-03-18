# M22D — Local Knowledge Intake Center — Validation

## Summary

- **Local-first:** All intake data lives under `data/local/intake/`. Snapshots copy files into the sandbox; originals are never mutated.
- **Operator-controlled:** No auto-ingest; no cloud sync. Add and report are explicit commands.
- **Workflow compatibility:** Named intake sets feed `release demo` task context via `--intake <label>`.

## Files Modified / Added

| Action | Path |
|--------|------|
| Added | `src/workflow_dataset/intake/__init__.py` |
| Added | `src/workflow_dataset/intake/registry.py` — add_intake, get_intake, list_intakes, snapshot copy |
| Added | `src/workflow_dataset/intake/load.py` — load_intake_content for demo |
| Added | `src/workflow_dataset/intake/report.py` — intake_report, format_intake_report_text |
| Modified | `src/workflow_dataset/cli.py` — intake add/list/report; release demo --intake; manifest intake_used/intake_name |
| Modified | `src/workflow_dataset/release/workspace_rerun_diff.py` — infer_rerun_args includes intake |
| Added | `tests/test_intake.py` |
| Added | `docs/M22D_INTAKE_VALIDATION.md` |

## Intake CLI Usage

```bash
# Register path(s) and snapshot into sandbox (never mutates originals)
workflow-dataset intake add --path ./notes --label sprint_notes
workflow-dataset intake add --path ./docs --label project_docs --type docs
workflow-dataset intake add -p /path/to/meetings -l meeting_fragments -t meeting_fragments

# List registered intake sets
workflow-dataset intake list
workflow-dataset intake list --repo-root /path/to/repo

# Report: file inventory, parse summary, suggested workflows
workflow-dataset intake report --label sprint_notes
workflow-dataset intake report -l sprint_notes -o intake_report.md
```

## Release Demo with Intake

```bash
# Run demo with named intake set; save workspace to sandbox
workflow-dataset release demo --workflow ops_reporting_workspace --intake sprint_notes --save-artifact

# With context and intake
workflow-dataset release demo -w weekly_status --context-file ./focus.md --intake sprint_notes --save-artifact
```

## Sample Intake Report

```
# Intake: sprint_notes

- **Input type:** notes
- **Created:** 2025-03-15T12:00:00+00:00
- **Snapshot:** sprint_notes/202503151200_abc12def

## Source paths
  - /path/to/repo/notes

## Parse summary
  - Total files: 5
  - Total chars: 12000
  - .md: 3
  - .txt: 2

## Suggested workflows
  - ops_reporting_workspace
  - weekly_status

## File inventory (sample)
  - daily.md
  - notes.txt
  - sprint.md
```

## Sample Workflow Run Using an Intake Set

1. Register and snapshot:
   ```bash
   workflow-dataset intake add --path ./my_notes --label sprint_notes
   workflow-dataset intake report --label sprint_notes
   ```

2. Run demo with intake and save workspace:
   ```bash
   workflow-dataset release demo --workflow ops_reporting_workspace --intake sprint_notes --save-artifact
   ```

3. Workspace is written to `data/local/workspaces/ops_reporting_workspace/<ts_id>/` with:
   - `workspace_manifest.json` including `"intake_used": true`, `"intake_name": "sprint_notes"`, and `input_sources_used` containing type `"intake"`.
   - Artifacts (e.g. weekly_status.md, source_snapshot.md) grounded by the intake content.

4. Rerun from that workspace (reuses intake):
   ```bash
   workflow-dataset release demo --rerun-from <ts_id>
   ```

## Tests Run

```bash
cd workflow-llm-dataset
PYTHONPATH=src python3 -m pytest tests/test_intake.py -v
# 7 passed
```

## Local-First and Operator-Controlled

- Intake add copies files into `data/local/intake/<label>/<ts_id>/`; originals are read-only from the tool’s perspective.
- No cloud or network; registry and snapshots are local files.
- No background watchers; intake add and report are explicit operator actions.

---

## Recommendation for Next Input-Driven Product Batch

1. **More input types:** Extend parsing for spreadsheets (e.g. CSV → table summary in report) and exported_repos (e.g. README + key files) so suggested_workflows and report are richer.
2. **Intake in dashboard:** Show “Recent intake sets” and “Suggested: run demo with intake X” in the command center.
3. **Multiple paths per add:** Support `intake add --path ./a --path ./b --label combined` to snapshot several paths into one set.
4. **Provenance in source_snapshot:** When artifact_schema is present, extend build_source_snapshot_md to include intake_name so source_snapshot.md clearly records intake-based runs.
