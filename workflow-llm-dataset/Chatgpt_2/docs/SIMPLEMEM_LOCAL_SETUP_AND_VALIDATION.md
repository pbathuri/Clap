# SimpleMem (cursor_mem) — Local-Only Setup and Validation

Standalone long-term memory service for Cursor usage. This document covers local-only installation, storage (SQLite + LanceDB), retrieval, and validation **without** changing the Clap/workflow-llm-dataset product architecture.

---

## 1. Files inspected

| Location | Purpose |
|----------|---------|
| **cursor_mem/SimpleMem/README.md** | Overview, Quick Start, Docker, MCP; mentions Cursor and local embedding |
| **cursor_mem/SimpleMem/config.py.example** | LLM/embedding/DB config; `OPENAI_BASE_URL` can be local (e.g. Ollama); `LANCEDB_PATH` local; `EMBEDDING_MODEL` local (SentenceTransformers) |
| **cursor_mem/SimpleMem/requirements.txt** | Full deps: lancedb, sentence-transformers, openai, fastapi, uvicorn, etc. |
| **cursor_mem/SimpleMem/.env.example** | MCP Docker env: JWT, encryption, LLM_PROVIDER=ollama, OLLAMA_BASE_URL |
| **cursor_mem/SimpleMem/main.py** | `SimpleMemSystem`: LLM client + embedding + LanceDB VectorStore; `add_dialogue` / `finalize` / `ask` |
| **cursor_mem/SimpleMem/database/vector_store.py** | LanceDB backend; local path or cloud (gs://, s3://); FTS (Tantivy local) |
| **cursor_mem/SimpleMem/utils/embedding.py** | `EmbeddingModel`: SentenceTransformers (Qwen3 or all-MiniLM-L6-v2 fallback); **no API key** |
| **cursor_mem/SimpleMem/utils/llm_client.py** | OpenAI-compatible client; `base_url` can be Ollama |
| **cursor_mem/SimpleMem/cross/README.md** | Cross-session: SQLite + LanceDB; default paths `~/.simplemem-cross/`; local-only possible |
| **cursor_mem/SimpleMem/cross/orchestrator.py** | `create_orchestrator(project=, db_path=, lancedb_path=)`; optional `simplemem` for full pipeline |
| **cursor_mem/SimpleMem/cross/storage_sqlite.py** | SQLite sessions/events/observations; path configurable |
| **cursor_mem/SimpleMem/cross/storage_lancedb.py** | LanceDB vector store; uses `EmbeddingModel()` (local) |
| **cursor_mem/SimpleMem/cross/api_http.py** | FastAPI router for REST |
| **cursor_mem/SimpleMem/cross/api_mcp.py** | MCP tool definitions (8 tools) |
| **cursor_mem/SimpleMem/MCP/README.md** | MCP server: cloud (mcp.simplemem.cloud) or self-host; Ollama supported |
| **cursor_mem/SimpleMem/MCP/run.py** | Starts uvicorn server (server.http_server:app) |
| **cursor_mem/SimpleMem/docs/PACKAGE_USAGE.md** | Pip package usage; config via env/constructor |
| **cursor_mem/SimpleMem/tests/test_vector_store.py** | VectorStore tests; needs embedding model (local) |
| **cursor_mem/SimpleMem/cross/tests/test_storage.py** | SQLite-only tests; no cloud |

---

## 2. Recommended local-only install path

- **Source of truth:** Use the extracted `cursor_mem/SimpleMem` tree (from the attached zip) under the Clap repo; do **not** rewrite the product around it.
- **Storage:** SQLite (cross-session metadata) + LanceDB (vectors). Both can live under a directory you control (e.g. `data/local/simplemem` or `~/.simplemem-cross`).
- **Embedding:** Local only — `EmbeddingModel` uses SentenceTransformers (`Qwen/Qwen3-Embedding-0.6B` or fallback `all-MiniLM-L6-v2`). No API key.
- **LLM (optional for full pipeline):** For memory *building* (compression/synthesis) and *ask()*, an OpenAI-compatible endpoint is used. Point `OPENAI_BASE_URL` to a **local** server (e.g. Ollama at `http://localhost:11434/v1`) and set a placeholder or dummy `OPENAI_API_KEY` if the local server does not require it.
- **MCP:** Run the MCP server **locally** (self-host) with `LLM_PROVIDER=ollama` and `OLLAMA_BASE_URL=http://localhost:11434/v1`; do **not** depend on hosted mcp.simplemem.cloud for local validation.
- **Cross-session:** Use `cross` with custom `db_path` and `lancedb_path` under your repo or a local dir; no cloud.

---

## 3. Exact setup commands

```bash
# 1. Ensure SimpleMem is extracted (e.g. at Clap/cursor_mem/SimpleMem)
cd /Users/prady/Desktop/Clap/cursor_mem/SimpleMem

# 2. Create a dedicated venv (recommended)
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies (local-only: no extra cloud deps)
pip install -r requirements.txt

# 4. Local config: copy example and set local paths + optional Ollama
cp config.py.example config.py
# Edit config.py (see below)
```

**Minimal `config.py` for local-only:**

```python
# --- Local-only: no cloud API required for embedding ---
OPENAI_API_KEY = "not-used-local"   # Or set for optional LLM (e.g. Ollama with no auth)
OPENAI_BASE_URL = "http://localhost:11434/v1"  # Ollama; set to None to skip LLM-dependent steps
LLM_MODEL = "llama3.2"   # Or any model name your local server exposes

# Local embedding (no API key)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Lighter than Qwen3; no GPU needed
EMBEDDING_DIMENSION = 384   # For all-MiniLM-L6-v2
EMBEDDING_CONTEXT_LENGTH = 512

# Local storage
LANCEDB_PATH = "./lancedb_data"   # Or absolute path, e.g. /path/to/Clap/data/local/simplemem/lancedb
MEMORY_TABLE_NAME = "memory_entries"

# Optional: reduce parallelism if needed
ENABLE_PARALLEL_PROCESSING = True
MAX_PARALLEL_WORKERS = 4
```

For **cross-session only** (no main SimpleMem LLM), you can run cross tests and the orchestrator with the same venv; cross uses its own defaults or you pass `db_path` and `lancedb_path` to `create_orchestrator()`.

---

## 4. Exact validation commands

```bash
cd /Users/prady/Desktop/Clap/cursor_mem/SimpleMem
source venv/bin/activate

# A. SQLite-only cross-session storage (no embedding, no LLM)
pytest cross/tests/test_storage.py -v --tb=short

# B. Cross-session tests that mock embedding/LLM (no network)
pytest cross/tests/test_consolidation.py cross/tests/test_context_injector.py cross/tests/test_types.py -v --tb=short

# C. Vector store tests: require a "store" fixture; tests/conftest.py was not present in the
#    inspected tree, so run only storage tests for reliable validation:
pytest cross/tests/test_storage.py -v --tb=short

# D. Optional: full cross e2e if you have Ollama running and config set
# pytest cross/tests/test_e2e.py -v --tb=short
```

**Validation outcomes (as run):**

| Command | Result |
|--------|--------|
| `./scripts/run_simplemem_local.sh validate` | OK — cross-session start → record_message → stop → end; stats printed. |
| `pytest cross/tests/test_storage.py` | 14 passed (run from SimpleMem root with venv; `pip install pytest pytest-asyncio` first). |
| `tests/test_vector_store.py` | Fixture `store` missing (no `tests/conftest.py` in repo); skip or add conftest. |

**Minimal “smoke” validation (storage + retrieval without LLM):**

```bash
cd /Users/prady/Desktop/Clap/cursor_mem/SimpleMem && source venv/bin/activate
export PYTHONPATH="${PWD}:${PYTHONPATH}"

python -c "
from cross.orchestrator import create_orchestrator
import asyncio
async def run():
    orch = create_orchestrator(project='clap-local', db_path='/tmp/simplemem_test.db', lancedb_path='/tmp/simplemem_test_lancedb')
    r = await orch.start_session(content_session_id='test-1', user_prompt='Test')
    print('start_session:', r.get('memory_session_id'))
    await orch.record_message(r['memory_session_id'], 'User said hello')
    await orch.stop_session(r['memory_session_id'])
    await orch.end_session(r['memory_session_id'])
    stats = orch.get_stats()
    print('stats:', stats)
    orch.close()
asyncio.run(run())
print('Local cross-session OK')
"
```

---

## 5. Whether Cursor can use it now locally

| Use case | Works locally? | Notes |
|----------|----------------|-------|
| **Cross-session store/retrieve (Python API)** | Yes | Use `create_orchestrator(project=..., db_path=..., lancedb_path=...)`; embedding is local; no cloud. |
| **SimpleMem core (add_dialogue / ask)** | Yes if LLM is local | Set `OPENAI_BASE_URL` to Ollama (or other local server); embedding is local. |
| **MCP server (Cursor as MCP client)** | Yes | Self-host MCP: run `MCP/run.py` (or Docker with `LLM_PROVIDER=ollama`); point Cursor MCP config to `http://localhost:8000/mcp` (or /mcp/sse) with a token if required. Cursor can then call SimpleMem MCP tools. |
| **Hosted mcp.simplemem.cloud** | No (avoid for local-only) | Do not use for this setup; use self-hosted only. |

So **yes**: Cursor can use SimpleMem locally (1) by running the MCP server locally and pointing Cursor at it, or (2) by calling the Python API (e.g. from a script or wrapper that your workflow invokes). No cloud dependency for storage, retrieval, or embedding.

---

## 6. What should be integrated later into the product core

- **Optional integration points** (only when you decide to tighten coupling):
  - **Learning lab / council:** “Recall relevant past decisions/experiments” by querying SimpleMem/cross from the product (e.g. pass a query string, get context back).
  - **Mission control or reporting:** Read-only stats (e.g. memory entry count, last session) from a known local SimpleMem/cross DB path.
  - **Unified “memory” CLI or pane:** A single command or pane that either launches the local MCP server or runs a small Python script that calls `create_orchestrator(...).search()` / `get_context_for_prompt()` and prints or returns JSON.
- **Data placement:** Use a path under the repo (e.g. `data/local/simplemem/`) or a fixed local path (e.g. `~/.simplemem-cross/`) so the product knows where to read/write if you integrate later.
- **No mandatory integration:** The product can remain unchanged; SimpleMem stays a standalone utility until you choose to wire it in.

---

## 7. What should NOT be integrated

- **Do not** vendor the entire SimpleMem repo into the core of workflow-llm-dataset (e.g. do not move all of `cursor_mem/SimpleMem` into `src/workflow_dataset/`).
- **Do not** depend on hosted MCP (mcp.simplemem.cloud) or any other cloud service for local validation or default usage.
- **Do not** replace or rewrite existing product subsystems (e.g. learning lab, council, runtime_mesh, benchmark board) with SimpleMem; any use should be additive and optional.
- **Do not** add cloud-only code paths to the product for SimpleMem; keep all usage local (self-hosted MCP or in-process Python API).
- **Do not** require an external API key for local-only storage/retrieval; only the optional LLM path may need a local server (Ollama).

---

## 8. Optional: wrapper script from Clap repo root

A small script at the Clap repo root can run validation or start the local MCP server without entangling the product:

- **Script:** `scripts/run_simplemem_local.sh` (or `.py`) that sets `PYTHONPATH` to `cursor_mem/SimpleMem` and either:
  - runs the minimal smoke validation above, or
  - runs `python -m MCP.run` (or `uvicorn` for MCP) from `cursor_mem/SimpleMem` with env `LLM_PROVIDER=ollama` and `OLLAMA_BASE_URL=http://localhost:11434/v1`.
- **Contract:** The script assumes SimpleMem lives at `Clap/cursor_mem/SimpleMem` and does not modify workflow-llm-dataset source or config.
- Such a script is provided below so you can run “local memory” from the repo root without changing the product.

---

## 9. Wrapper script (run from Clap root)

**Path:** `scripts/run_simplemem_local.sh`

| Command | Action |
|---------|--------|
| `./scripts/run_simplemem_local.sh validate` | Smoke test: cross-session start → record_message → stop → end; prints stats. |
| `./scripts/run_simplemem_local.sh pytest` | Run `cross/tests/test_storage.py` (install pytest first: `pip install pytest pytest-asyncio`). |
| `./scripts/run_simplemem_local.sh mcp` | Start MCP server (from `cursor_mem/SimpleMem/MCP`); set `LLM_PROVIDER=ollama` and `OLLAMA_BASE_URL` for local LLM. |

Ensure `cursor_mem/SimpleMem/venv` exists and is activated by the script, or activate it before running. For `validate` and `pytest`, a local `config.py` is only required for tests that use the main SimpleMem pipeline (e.g. vector_store uses embedding model).
