# M43I–M43L — Memory-Aware Learning, Evaluation, and Cursor Bridge: Before-Coding

## 1. What memory-aware eval/improvement support already exists

- **learning_lab**: `LocalLearningSlice` has evidence_ids, correction_ids, issue_ids, run_ids; experiments have local_slice and evidence_bundle. No `memory_slice_id` or “memory-backed” concept; slices are built ad hoc from cluster/correction/adaptation.
- **candidate_model_studio**: `DatasetSlice` has provenance_source, provenance_refs, included_evidence_ids, included_correction_ids. No link to a shared “memory substrate” or memory_slice_id.
- **benchmark_board**: `BenchmarkSlice` is eval-oriented (eval_suite, reliability_path_id). Scorecards have slice_ids from comparison_result. No memory-aware slice or memory-compare.
- **live_context/fusion**: Fuses observation + graph + session into ActiveWorkContext; not a persistent “memory store” for learning/benchmarks.
- **outcomes/store**: Session/task outcomes; no slice abstraction for learning or benchmarks.
- **corrections, triage, safe_adaptation**: Evidence and correction stores; no unified “memory slice” API.

So: **slices exist in learning_lab and candidate_model_studio as experiment- or candidate-scoped data; there is no shared memory substrate facade or memory-backed slice id that both can reference, and no Cursor-facing bridge.**

---

## 2. What is missing

- **Unified memory-slice abstraction**: A logical “memory slice” (memory_slice_id) that can be backed by evidence + corrections + outcomes so learning_lab and candidate_model_studio can use the same slice reference without duplicating data.
- **Memory-backed experiment slices**: learning_lab experiments that reference a memory_slice_id (optional field on LocalLearningSlice) and a CLI to list “memory slices” usable for experiments.
- **Memory-backed candidate model slices**: candidate_model_studio DatasetSlice creatable from a memory_slice_id (resolve via substrate).
- **Memory-aware benchmark scorecards**: Benchmark comparisons that can tag which slice(s) are memory-backed and a `benchmarks memory-compare` (or memory-compare report).
- **Cursor bridge**: Safe documentation and config surface for Cursor to use the same local memory paths (production-safe vs experimental), without writing to production memory from Cursor.

---

## 3. Exact file plan

| Area | Path | Purpose |
|------|------|--------|
| Doc | `docs/M43_MEMORY_AWARE_BEFORE_CODING.md` | This file. |
| Memory facade | `src/workflow_dataset/memory_substrate/__init__.py` | Package exports. |
| Memory facade | `src/workflow_dataset/memory_substrate/models.py` | MemorySliceSummary, MemoryBackedRef; production_safe vs experimental. |
| Memory facade | `src/workflow_dataset/memory_substrate/slices.py` | list_memory_slices(), get_memory_slice_refs(); resolve from learning_lab + candidate_model_studio + outcomes/corrections. |
| Cursor bridge | `src/workflow_dataset/memory_substrate/cursor_bridge.py` | build_cursor_bridge_report(): paths, env, production-safe vs experimental, usage notes. |
| Learning lab | `src/workflow_dataset/learning_lab/models.py` | Add optional memory_slice_id to LocalLearningSlice. |
| Learning lab | `src/workflow_dataset/learning_lab/memory_slices.py` | list_memory_slices_for_learning(), create_experiment_from_memory_slice() stub or implementation. |
| Learning lab | `src/workflow_dataset/learning_lab/report.py` or store | Persist/read memory_slice_id on experiment slice. |
| Candidate studio | `src/workflow_dataset/candidate_model_studio/dataset_slice.py` | build_slice_from_memory_slice(memory_slice_id, candidate_id). |
| Benchmark board | `src/workflow_dataset/benchmark_board/scorecard.py` or report | Add memory_slice_ids to scorecard; memory_compare report. |
| CLI | `src/workflow_dataset/cli.py` | learning-lab memory-slices; benchmarks memory-compare; memory cursor-bridge. |
| Tests | `tests/test_memory_substrate.py` | Slices list, resolve, cursor bridge report. |
| Doc | `docs/M43_MEMORY_AWARE_DELIVERABLE.md` | Files, samples, tests, gaps. |

---

## 4. Safety/risk note

- **Production-safe vs experimental**: Memory substrate and Cursor bridge will tag which paths/slices are production-safe vs experimental. Cursor must not write to production memory without explicit operator approval.
- **Read-only bridge**: Cursor bridge is notes/config and read-only paths; no automatic push of Cursor state into product memory.
- **Bounded slices**: Memory-backed slices remain bounded by provenance (evidence_ids, correction_ids); no “all data” slice.

---

## 5. What this block will NOT do

- Rebuild learning_lab, council, candidate_model_studio, benchmark_board, model registry, or workspace shell.
- Implement a full new “memory store” backend; we add a facade over existing stores.
- Allow Cursor to write into product memory without an explicit, reviewable path.
- Merge or replace existing slice types; we add optional memory_slice_id and memory-backed resolution.
