# A3 — Workspace rerun/diff + provenance timeline

Rerun a workspace from the same inputs/config, compare two runs, and show a simple provenance timeline. Local-only; no mutation of existing workspaces.

---

## 1. Files modified / created

| Path | Change |
|------|--------|
| **New** `src/workflow_dataset/release/workspace_rerun_diff.py` | `infer_rerun_args(manifest)` — infer context_file, input_pack, retrieval, workflow from manifest. `diff_workspaces(path_a, path_b)` — inventory diff, manifest metadata diff, artifact deltas (unified diff). `workspace_timeline(root, workflow, limit)` — list runs newest first with timestamp, run_id, grounding, artifact_count. |
| `src/workflow_dataset/cli.py` | `release demo --rerun-from <path>` — load manifest from path, infer args, run demo with same inputs, save to new dir (original unchanged). `review diff-workspaces <path_a> <path_b>` — compare two runs. `review workspace-timeline [--workflow] [--limit]` — provenance timeline. |
| `tests/test_release.py` | `test_infer_rerun_args`, `test_diff_workspaces`, `test_workspace_timeline`. |
| `docs/A3_WORKSPACE_RERUN_DIFF_TIMELINE.md` | This file. |

---

## 2. Exact CLI usage

**Rerun from existing workspace (same inputs; new run dir):**
```bash
workflow-dataset release demo --rerun-from ops_reporting_workspace/2025-03-15_1432_abc
# or full path
workflow-dataset release demo --rerun-from /path/to/data/local/workspaces/ops_reporting_workspace/2025-03-15_1432_abc
```
Rerun uses manifest’s `input_sources_used`, `retrieval_used`, and `workflow`; writes to a new timestamped dir. Original workspace is never modified.

**Compare two workspace runs:**
```bash
workflow-dataset review diff-workspaces ops_reporting_workspace/run1 ops_reporting_workspace/run2
workflow-dataset review diff-workspaces /path/to/run_a /path/to/run_b --no-diffs
```
`--no-diffs`: skip artifact text diffs; show only inventory and manifest metadata diff.

**Provenance timeline:**
```bash
workflow-dataset review workspace-timeline
workflow-dataset review workspace-timeline --workflow ops_reporting_workspace --limit 20
```

---

## 3. Sample workspace diff output

```
Workspace diff
  A: /path/to/data/local/workspaces/ops_reporting_workspace/2025-03-15_1432_abc
  B: /path/to/data/local/workspaces/ops_reporting_workspace/2025-03-15_1501_def
Inventory
  only in A: []
  only in B: []
  common: ['source_snapshot.md', 'weekly_status.md', 'status_brief.md', 'action_register.md', 'stakeholder_update.md', 'decision_requests.md']
Manifest metadata diff
  timestamp: A=2025-03-15T14:32:00Z  B=2025-03-15T15:01:00Z
Artifact deltas
  weekly_status.md: 12 diff lines
    --- a/weekly_status.md
    +++ b/weekly_status.md
    @@ -1,4 +1,4 @@
    -**Summary:** Draft.
    +**Summary:** Updated after review.
    ...
```

---

## 4. Exact tests run

```bash
cd workflow-llm-dataset
python -m pytest tests/test_release.py -v --tb=short -k "infer_rerun or diff_workspaces or workspace_timeline"
```

Or run the three tests by name:
```bash
python -m pytest tests/test_release.py::test_infer_rerun_args tests/test_release.py::test_diff_workspaces tests/test_release.py::test_workspace_timeline -v --tb=short
```

(Requires project venv with dependencies e.g. pyyaml.)

---

## 5. Behavior and constraints

- **Local-only:** All reads/writes under repo; no network.
- **No mutation:** Rerun creates a new dir; diff and timeline are read-only.
- **Compare:** Inventory (only in A, only in B, common), manifest metadata (workflow, timestamp, grounding, retrieval_used, etc.), and per-artifact unified diff (with optional `--no-diffs`).
- **Timeline:** Newest first; filter by workflow; shows timestamp, run_id, grounding, artifact count.
