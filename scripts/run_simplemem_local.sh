#!/usr/bin/env bash
# Run SimpleMem (cursor_mem) locally from Clap repo root.
# Does not modify workflow-llm-dataset; standalone memory utility only.
#
# Usage:
#   ./scripts/run_simplemem_local.sh validate   # smoke test (cross-session store/retrieve)
#   ./scripts/run_simplemem_local.sh pytest      # run cross + vector_store tests
#   ./scripts/run_simplemem_local.sh mcp        # start MCP server (requires venv + config)
set -e
CLAP_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIMPLEMEM_ROOT="${CLAP_ROOT}/cursor_mem/SimpleMem"
if [[ ! -d "$SIMPLEMEM_ROOT" ]]; then
  echo "SimpleMem not found at $SIMPLEMEM_ROOT"
  exit 1
fi
export PYTHONPATH="${SIMPLEMEM_ROOT}:${PYTHONPATH}"
cd "$SIMPLEMEM_ROOT"
VENV="${SIMPLEMEM_ROOT}/venv"
PY="${VENV}/bin/python"
if [[ -d "$VENV" ]]; then
  source "${VENV}/bin/activate"
else
  PY=python
fi
case "${1:-validate}" in
  validate)
    "$PY" -c "
import asyncio
from cross.orchestrator import create_orchestrator
async def run():
    orch = create_orchestrator(project='clap-local', db_path='/tmp/simplemem_test.db', lancedb_path='/tmp/simplemem_test_lancedb')
    r = await orch.start_session(content_session_id='test-1', user_prompt='Test')
    print('start_session:', r.get('memory_session_id'))
    await orch.record_message(r['memory_session_id'], 'User said hello')
    await orch.stop_session(r['memory_session_id'])
    await orch.end_session(r['memory_session_id'])
    print('stats:', orch.get_stats())
    orch.close()
asyncio.run(run())
print('Local cross-session OK')
"
    ;;
  pytest)
    "$PY" -m pytest cross/tests/test_storage.py -v --tb=short
    ;;
  mcp)
    export LLM_PROVIDER="${LLM_PROVIDER:-ollama}"
    export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434/v1}"
    (cd "${SIMPLEMEM_ROOT}/MCP" && export PYTHONPATH="${SIMPLEMEM_ROOT}:${PYTHONPATH}" && exec python run.py --host 0.0.0.0 --port 8000)
    ;;
  *)
    echo "Usage: $0 validate|pytest|mcp"
    exit 1
    ;;
esac
