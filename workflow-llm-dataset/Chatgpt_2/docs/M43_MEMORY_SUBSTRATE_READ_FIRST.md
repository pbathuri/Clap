# M43A–M43D Memory Substrate — READ FIRST

## 1. What memory-like behavior already exists in the current repo

- **learning_lab**: Experiments with `local_slice` (evidence_ids, correction_ids, `memory_slice_id`); store in `data/local/learning_lab/experiments.jsonl`; `memory_slices.py` delegates to `memory_substrate` for `list_memory_slices` / `get_memory_slice_refs`.
- **memory_substrate**: `MemorySliceSummary`, `MemoryBackedRef`, `list_memory_slices` (from learning_lab, candidate_model_studio, corrections), `get_memory_slice_refs`, `build_cursor_bridge_report`. No durable “memory item” storage or retrieval at substrate level.
- **session**: `Session` model; storage under `data/local/session/*.json`; save/load/list/archive; current session pointer.
- **personal/graph_store**: SQLite-backed nodes/edges/suggestions/graph_review for the work graph (observation-derived).
- **context/snapshot**: WorkState snapshots (latest.json, timestamped).
- **observe/state**: `observation_state.yaml` (enabled sources).
- **live_context / continuity / personal**: `memory-explain`, `memory-context`, `memory-links` via `memory_fusion` (links, snippets); no shared “memory item” table.

So: **slices and refs are logical aggregations over existing stores; there is no dedicated memory backbone (items + compression + hybrid retrieval) in the product.**

---

## 2. What SimpleMem contributes that is genuinely useful

- **MemoryEntry**: Self-contained unit with `lossless_restatement`, `keywords`, `timestamp`, `location`, `persons`, `entities`, `topic` — multi-view (semantic, lexical, symbolic). Good shape for a compressed unit.
- **MemoryBuilder**: Sliding-window compression and synthesis pattern; we can adopt the *pattern* (bounded ingest → compress → store) without the LLM pipeline.
- **HybridRetriever**: Semantic + keyword + structured retrieval; we adopt the *interface* (multi-view) and implement locally without LLM planning.
- **Cross**: SQLite (sessions, events, observations, summaries) + LanceDB vectors; session linkage and token-budgeted context. We adopt storage/session-link *concepts*, not the full orchestrator.
- **storage_sqlite / storage_lancedb**: Schema and embedding patterns; we mirror minimal schema and optional vector backend behind our own interface.

---

## 3. What should be adopted

- **Product-native models**: MemoryItem (raw), CompressedMemoryUnit (restatement + keywords + metadata), MemorySource, MemorySessionLink, Provenance/Evidence, MemoryStorageBackend (protocol), RetrievalIntent, MemoryRetentionState.
- **Local storage**: SQLite (or JSONL) for metadata/items under `data/local/memory_substrate/`; optional simple vector index later.
- **Compression pattern**: Rule-based synthesis (merge by session, dedupe by keywords); no LLM in first draft.
- **Hybrid retrieval**: Keyword + structured filter by session/source; optional semantic when a vector backend exists.
- **Session linkage**: Link memory items to existing `session_id` (session model unchanged).
- **CLI**: `memory status`, `memory backends`, `memory ingest`, `memory retrieve`, `memory explain`.

---

## 4. What should be rejected

- Full SimpleMem pipeline (MemoryBuilder + LLM, HybridRetriever planning/reflection) as-is — too coupled to their config/LLM.
- Vendoring entire `cross/` (session_manager, collectors, orchestrator).
- Any cloud or MCP client dependency for the core substrate.
- Replacing `session/storage` or `personal/graph_store` with SimpleMem storage.

---

## 5. Exact file plan

| Action | Path |
|--------|------|
| Extend | `memory_substrate/models.py` — add MemoryItem, CompressedMemoryUnit, MemorySource, MemorySessionLink, Provenance, MemoryStorageBackend, RetrievalIntent, MemoryRetentionState |
| New | `memory_substrate/backends.py` — InMemoryBackend, SQLiteBackend (implement backend protocol) |
| New | `memory_substrate/compression.py` — rule-based compress/synthesize |
| New | `memory_substrate/retrieval.py` — hybrid retrieve (keyword + structured) |
| New | `memory_substrate/store.py` — ingest(), store(), retrieve(), list_sessions(), status(), backends() |
| New | `memory_substrate/simplemem_bridge.py` — optional adapters to SimpleMem-like shapes (local reference only) |
| Update | `memory_substrate/__init__.py` — export new types and store API |
| Update | `cli.py` — memory_group: status, backends, ingest, retrieve, explain |

---

## 6. Safety/risk note

- All new storage under `data/local/memory_substrate/`. No cloud. Existing session/learning_lab/personal unchanged. Substrate is additive; learning_lab.memory_slices continues to use existing slice sources. Optional later: substrate-backed slices.

---

## 7. What this block will NOT do

- Will not run SimpleMem’s LLM pipeline (memory_builder or retriever planning).
- Will not replace session/storage or personal/graph_store.
- Will not add cloud or MCP client dependency.
- Will not implement LanceDB/full vector indexing in first draft (backend interface ready for later).
