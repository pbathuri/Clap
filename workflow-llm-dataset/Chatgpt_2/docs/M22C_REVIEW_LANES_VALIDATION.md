# M22C — Team Pilot Workspace + Role-Based Review Lanes — Validation

## Summary

- **Local-first, file-based:** Lanes are stored in `data/local/review/<workflow>/<run_id>.json` (workspace lane) and in `package_manifest.json` (package lane). No cloud or shared DB.
- **Role lanes:** `operator`, `reviewer`, `stakeholder-prep`, `approver`.
- **Safety preserved:** Same sandbox/package/apply-preview flow; lane metadata is additive and inspectable.

## Files Modified / Added

| Action | Path |
|--------|------|
| Modified | `src/workflow_dataset/release/review_state.py` — LANES, load/save lane, set_workspace_lane |
| Added | `src/workflow_dataset/release/lane_views.py` — lane summary, list by lane, set_package_lane |
| Modified | `src/workflow_dataset/release/package_builder.py` — write workspace lane into package_manifest |
| Modified | `src/workflow_dataset/cli.py` — review lane-status, assign-lane, list-lane; package-status shows lane |
| Added | `tests/test_review_lanes.py` |
| Added | `docs/M22C_REVIEW_LANES_VALIDATION.md` |

If your repo was missing supporting modules, these may also have been added so tests and CLI run:

- `src/workflow_dataset/release/reporting_workspaces.py` — workspace inventory/list
- `src/workflow_dataset/utils/dates.py` — utc_now_iso
- `src/workflow_dataset/utils/hashes.py` — stable_id

## Lane-Aware CLI Usage

```bash
# Lane summary: workspaces and packages per lane, pending and needs-revision counts
workflow-dataset review lane-status
workflow-dataset review lane-status --repo-root /path/to/repo

# Assign lane to a workspace
workflow-dataset review assign-lane --workspace weekly_status/2025-03-15_abc --lane reviewer
workflow-dataset review assign-lane -w /path/to/workspace -l approver

# Assign lane to a package (updates package_manifest.json)
workflow-dataset review assign-lane --package 2025-03-15_1200_xyz --lane stakeholder-prep
workflow-dataset review assign-lane -p /path/to/package/dir -l approver

# List workspaces in a lane
workflow-dataset review list-lane --lane approver
workflow-dataset review list-lane -l reviewer -n 20

# List packages in a lane
workflow-dataset review list-lane --lane stakeholder-prep --packages
```

## Sample lane-status Output

```
Review lanes (local)
  operator: workspaces=2  packages=0  pending=1  needs_revision=1
  reviewer: workspaces=1  packages=1  pending=0  needs_revision=0
  stakeholder-prep: workspaces=0  packages=2  pending=0  needs_revision=0
  approver: workspaces=0  packages=0  pending=0  needs_revision=0
  no lane: workspaces=3  packages=1  pending=2
Assign lane: workflow-dataset review assign-lane --workspace <path> --lane <operator|reviewer|stakeholder-prep|approver>
```

## Sample Lane-Aware Workspace/Package Metadata

**Review state file** (`data/local/review/<workflow>/<run_id>.json`):

```json
{
  "workspace_path": "/repo/data/local/workspaces/weekly_status/2025-03-15_1432_abc",
  "artifacts": { "weekly_status.md": { "state": "approved", "note": "", "reviewed_at": "2025-03-15T14:35:00+00:00" } },
  "last_package_path": "/repo/data/local/packages/2025-03-15_1436_xyz",
  "updated_at": "2025-03-15T14:36:00+00:00",
  "lane": "reviewer"
}
```

**Package manifest** (`data/local/packages/<ts_id>/package_manifest.json`):

```json
{
  "package_type": "ops_reporting",
  "source_workspace": "/repo/data/local/workspaces/weekly_status/2025-03-15_1432_abc",
  "workflow": "weekly_status",
  "lane": "reviewer",
  "approved_artifacts": ["weekly_status.md"],
  "artifact_count": 1,
  "created_utc": "2025-03-15T14:36:00+00:00"
}
```

## Tests Run

```bash
cd workflow-llm-dataset
PYTHONPATH=src python3 -m pytest tests/test_review_lanes.py -v
# 9 passed
```

## Local-First and Operator-Controlled

- All lane data is under `data/local/review` and `data/local/packages`; no network.
- assign-lane and build-package are explicit operator actions; no auto-routing.
- Provenance and review notes remain in existing review state and package manifest.

---

## Recommendation for Next Team Pilot Batch

1. **Default lane for new workspaces:** Optionally set a default lane (e.g. `operator`) when a workspace is first created or when it first gets review state, so new runs land in a known lane without an extra assign step.
2. **Lane in dashboard:** If the command center/dashboard shows recent workspaces or packages, add a lane column and filter by lane (e.g. “show only approver”).
3. **Promotion flow:** Document the intended flow (e.g. operator → reviewer → stakeholder-prep → approver) in the pilot operator guide and optionally add a “move to next lane” helper that suggests the next lane from the current one.
4. **Stakeholder-ready report:** Use `list-lane --lane stakeholder-prep --packages` (or a small script) to produce a “stakeholder-ready” list for handoff without adding new domains or cloud.
