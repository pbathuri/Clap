# M43A–M43D Memory Substrate — Final Output

## 1. Files modified

| File | Changes |
|------|---------|
| `src/workflow_dataset/memory_substrate/models.py` | Added MemoryItem, CompressedMemoryUnit, MemorySource, MemorySessionLink, Provenance, MemoryStorageBackend (Protocol), RetrievalIntent, MemoryRetentionState. Kept MemorySliceSummary, MemoryBackedRef. |
| `src/workflow_dataset/memory_substrate/__init__.py` | Exported new models and store API (ingest, store_unit, retrieve_units, list_sessions, get_status, get_backends). |
| `src/workflow_dataset/cli.py` | memory_group: added commands `status`, `backends`, `ingest`, `retrieve`, `explain`. Updated help text. |
| `tests/test_memory_substrate.py` | Added test_memory_ingest_and_retrieve, test_memory_backends_protocol, test_compression_keywords, test_simplemem_bridge_dict_roundtrip. |

## 2. Files created

| File | Purpose |
|------|---------|
| `docs/M43_MEMORY_SUBSTRATE_READ_FIRST.md` | Read-first: existing behavior, SimpleMem value, adopt/reject, file plan, safety, what we do not do. |
| `docs/M43_MEMORY_SUBSTRATE_FINAL_OUTPUT.md` | This file: final deliverable. |
| `src/workflow_dataset/memory_substrate/backends.py` | InMemoryBackend, SQLiteBackend (MemoryStorageBackend implementation). |
| `src/workflow_dataset/memory_substrate/compression.py` | compress_item(), synthesize_units() (rule-based, no LLM). |
| `src/workflow_dataset/memory_substrate/retrieval.py` | retrieve() — hybrid keyword + structured. |
| `src/workflow_dataset/memory_substrate/store.py` | ingest(), store_unit(), retrieve_units(), list_sessions(), get_status(), get_backends(). |
| `src/workflow_dataset/memory_substrate/simplemem_bridge.py` | unit_to_simplemem_entry_dict(), simplemem_entry_dict_to_unit() for optional SimpleMem compatibility. |

## 3. Adopted vs rejected SimpleMem pieces

| Adopted (concept/pattern only) | Rejected |
|--------------------------------|----------|
| **MemoryEntry shape**: lossless_restatement, keywords, timestamp, location, persons, entities, topic → our CompressedMemoryUnit. | Full MemoryBuilder + LLM pipeline. |
| **Storage pattern**: SQLite for metadata/units + session links; optional vector store later → SQLiteBackend + protocol. | Vendoring cross/session_manager, collectors, orchestrator. |
| **Hybrid retrieval**: keyword + structured (session/source) → retrieval.retrieve() + backend.search_keyword/search_structured. | HybridRetriever planning/reflection LLM. |
| **Session linkage**: link units to session_id → MemorySessionLink, stored with unit. | Replacing session/storage or personal/graph_store. |
| **SimpleMem dict bridge**: translate to/from SimpleMem-like dict for optional local cursor_mem use → simplemem_bridge.py. | Cloud MCP or any network dependency. |

## 4. Sample memory item

```python
from workflow_dataset.memory_substrate import MemoryItem, ingest

item = MemoryItem(
    content="User decided to use SQLite for the memory backend.",
    source="manual",
    session_id="s1",
    timestamp_utc="2025-03-16T12:00:00Z",
)
units = ingest([item], repo_root="/path/to/repo")
# units[0].unit_id: mu_<hash>
# units[0].lossless_restatement: "User decided to use SQLite for the memory backend."
# units[0].keywords: ["user", "decided", "sqlite", "memory", "backend", ...]
```

## 5. Sample retrieval output

```python
from workflow_dataset.memory_substrate import retrieve_units
from workflow_dataset.memory_substrate.models import RetrievalIntent

intent = RetrievalIntent(query="SQLite backend", top_k=5, session_id=None)
results = retrieve_units(intent, repo_root="/path/to/repo")
# Example:
# [CompressedMemoryUnit(unit_id="mu_8a7c7f59...", lossless_restatement="Memory substrate uses SQLite for durable storage", keywords=[...], session_id="s1", ...)]
```

CLI:

```bash
workflow-dataset memory retrieve --query "SQLite" -n 2
# Retrieved 1 unit(s)
#   mu_8a7c7f59...  Memory substrate uses SQLite for durable storage
```

## 6. Exact tests run

```bash
cd /Users/prady/Desktop/Clap/workflow-llm-dataset
python -m pytest tests/test_memory_substrate.py -v --tb=short
```

**Result:** 10 passed (6 existing + 4 new).

- `test_list_memory_slices_empty`
- `test_get_memory_slice_refs_corrections_recent`
- `test_get_memory_slice_refs_unknown_returns_none`
- `test_cursor_bridge_report`
- `test_create_experiment_from_memory_slice`
- `test_build_slice_from_memory_slice`
- **test_memory_ingest_and_retrieve** — ingest items, retrieve by query, list_sessions, get_status
- **test_memory_backends_protocol** — InMemoryBackend store/get/list/search_keyword/get_stats
- **test_compression_keywords** — compress_item extracts keywords
- **test_simplemem_bridge_dict_roundtrip** — unit ↔ SimpleMem-like dict

CLI (after `pip install -e .`):

- `workflow-dataset memory status`
- `workflow-dataset memory backends`
- `workflow-dataset memory ingest --content "..." --session s1`
- `workflow-dataset memory retrieve --query "..." -n 2`
- `workflow-dataset memory explain`

## 7. Remaining gaps

- **Vector/semantic backend**: RetrievalIntent.semantic exists but no vector backend yet; add a backend that implements optional semantic_search(query, top_k) when needed.
- **LanceDB adapter**: Optional adapter in backends or simplemem_bridge to write/read via cursor_mem’s LanceDB when running locally (no product dependency on cursor_mem).
- **Wiring to observe/session**: No automatic ingestion from observe events or session close yet; callers use `ingest([MemoryItem(...)])` or CLI `memory ingest`.
- **Retention/eviction**: MemoryRetentionState and retention_tier are modeled but not used; eviction/compaction can be added later.
- **Substrate-backed slices**: list_memory_slices still only from learning_lab/candidate_studio/corrections; optional later: slices backed by substrate units (e.g. by session or source).
