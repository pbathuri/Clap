# M43I–M43L — Memory-Aware Learning, Evaluation, and Cursor Bridge: Deliverable

## 1. Files modified

| File | Changes |
|------|--------|
| `learning_lab/models.py` | Added `memory_slice_id` to `LocalLearningSlice`. |
| `learning_lab/store.py` | `_dict_to_experiment` reads `memory_slice_id` from local_slice dict. |
| `learning_lab/__init__.py` | Exported `list_memory_slices_for_learning`, `create_experiment_from_memory_slice`. |
| `candidate_model_studio/models.py` | Added `PROVENANCE_MEMORY_SLICE`, `memory_slice_id` on `DatasetSlice`. |
| `candidate_model_studio/store.py` | `load_slice` sets `memory_slice_id`. |
| `benchmark_board/models.py` | Added `memory_slice_ids` to `Scorecard`. |
| `benchmark_board/scorecard.py` | `build_scorecard` accepts and sets `memory_slice_ids`. |
| `benchmark_board/report.py` | Added `build_memory_compare_report()`. |
| `cli.py` | Added `learning-lab memory-slices`, `benchmarks memory-compare`, `memory cursor-bridge` (and `memory` group). |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M43_MEMORY_AWARE_BEFORE_CODING.md` | Before-coding: existing support, gaps, file plan, safety. |
| `memory_substrate/__init__.py` | Package exports. |
| `memory_substrate/models.py` | `MemorySliceSummary`, `MemoryBackedRef`; production_safe vs experimental. |
| `memory_substrate/slices.py` | `list_memory_slices()`, `get_memory_slice_refs()` from learning_lab, candidate studio, corrections. |
| `memory_substrate/cursor_bridge.py` | `build_cursor_bridge_report()`: paths, env, usage notes. |
| `learning_lab/memory_slices.py` | `list_memory_slices_for_learning()`, `create_experiment_from_memory_slice()`. |
| `candidate_model_studio/dataset_slice.py` | Added `build_slice_from_memory_slice(candidate_id, memory_slice_id, ...)`. |
| `tests/test_memory_substrate.py` | Tests for slices list/resolve, cursor bridge, create-from-memory-slice, build_slice_from_memory_slice. |
| `docs/M43_MEMORY_AWARE_DELIVERABLE.md` | This file. |

## 3. Sample memory-backed experiment

Creating an experiment from a memory slice:

```bash
workflow-dataset learning-lab memory-slices --create-from mem_corrections_recent --profile balanced
```

Or from code:

```python
from workflow_dataset.learning_lab.memory_slices import create_experiment_from_memory_slice
exp = create_experiment_from_memory_slice("mem_corrections_recent", repo_root=root)
# exp.source_type == "memory_slice", exp.source_ref == "mem_corrections_recent"
# exp.local_slice.memory_slice_id == "mem_corrections_recent"
```

Sample experiment dict (excerpt):

```json
{
  "experiment_id": "exp_...",
  "source_type": "memory_slice",
  "source_ref": "mem_corrections_recent",
  "label": "Experiment from memory slice mem_corrections_recent",
  "local_slice": {
    "slice_id": "slice_...",
    "description": "Memory-backed: mem_corrections_recent",
    "evidence_ids": [],
    "correction_ids": ["corr_1", "corr_2"],
    "memory_slice_id": "mem_corrections_recent"
  }
}
```

## 4. Sample memory-backed benchmark output

**List memory slices (learning-lab):**

```bash
workflow-dataset learning-lab memory-slices --json
```

**Memory-compare report:**

```bash
workflow-dataset benchmarks memory-compare --json
```

Sample output (excerpt):

```json
{
  "scorecards_with_memory_slices": [
    {
      "scorecard_id": "sc_...",
      "baseline_id": "run_prev",
      "candidate_id": "cand_123",
      "memory_slice_ids": ["mem_cand_slice_abc"],
      "recommendation": "hold"
    }
  ],
  "scorecards_with_memory_count": 1,
  "available_memory_slices": [
    {
      "memory_slice_id": "mem_exp_exp_xyz",
      "source_type": "learning_lab_experiment",
      "description": "Issue cluster cluster_123: 5 issues",
      "evidence_count": 10,
      "correction_count": 0,
      "scope": "experimental"
    }
  ],
  "usage_note": "Use memory_slice_ids in compare result or when building scorecard to tag memory-aware comparisons."
}
```

## 5. Sample Cursor bridge report

```bash
workflow-dataset memory cursor-bridge --json
```

Sample (excerpt):

```json
{
  "cursor_bridge_version": "1.0",
  "repo_root": "/path/to/workflow-llm-dataset",
  "data_local": "/path/to/workflow-llm-dataset/data/local",
  "production_safe_paths": [
    "/path/to/workflow-llm-dataset/data/local/outcomes",
    "/path/to/workflow-llm-dataset/data/local/corrections/events"
  ],
  "production_safe_note": "Read-only from Cursor recommended. Writes to production memory require explicit operator approval and review.",
  "experimental_paths": [
    ".../data/local/learning_lab",
    ".../data/local/candidate_model_studio",
    ".../data/local/safe_adaptation",
    ".../data/local/benchmark_board",
    ".../data/local/eval/runs"
  ],
  "experimental_note": "Learning lab, candidate model studio, benchmarks. Safe for Cursor to read; writes still reviewable.",
  "env_suggestions": {
    "WORKFLOW_DATASET_REPO_ROOT": "/path/to/workflow-llm-dataset",
    "WORKFLOW_MEMORY_DATA_LOCAL": "/path/to/workflow-llm-dataset/data/local"
  },
  "usage_notes": [
    "Use same repo root (WORKFLOW_DATASET_REPO_ROOT) so Cursor and workflow-dataset CLI see the same data/local.",
    "Memory-backed slices: learning-lab memory-slices, then use memory_slice_id in experiments or candidate creation.",
    "Do not write to production_safe paths from Cursor without explicit review; use experimental paths for learning/candidates."
  ],
  "cli_commands": [
    "workflow-dataset learning-lab memory-slices",
    "workflow-dataset benchmarks memory-compare",
    "workflow-dataset memory cursor-bridge"
  ]
}
```

## 6. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_memory_substrate.py -v
```

**6 tests:** list_memory_slices (empty), get_memory_slice_refs (mem_corrections_recent), get_memory_slice_refs (unknown → None), cursor_bridge_report, create_experiment_from_memory_slice, build_slice_from_memory_slice.

## 7. Remaining gaps

- **Pane 1 memory substrate**: This deliverable adds a facade over existing stores (learning_lab, candidate_model_studio, corrections). A full memory substrate (e.g. unified store or indexing) can be added in Pane 1 and wired behind `list_memory_slices` / `get_memory_slice_refs`.
- **Compare with memory_slice_ids**: `benchmarks compare` does not yet accept `--memory-slice-ids` to tag the resulting scorecard; callers can pass `memory_slice_ids` when building the scorecard from a comparison result.
- **Cursor integration**: The bridge is report/config only; no Cursor-specific plugin or auto-sync. Cursor can read the same paths using `WORKFLOW_DATASET_REPO_ROOT`.
- **Production-safe slice tagging**: Only `production_safe` provenance in candidate studio is mapped to `scope=production_safe` in memory summary; learning_lab experiments are currently all experimental.
