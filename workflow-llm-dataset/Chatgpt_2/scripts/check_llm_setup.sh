#!/usr/bin/env bash
# LLM setup check: run from workflow-llm-dataset directory (or pass its path as first arg).
# Example from repo root:  ./workflow-llm-dataset/scripts/check_llm_setup.sh workflow-llm-dataset

ROOT="${1:-.}"
if ! cd "$ROOT"; then
  echo "Failed to cd to '$ROOT'. Use: $0 [path/to/workflow-llm-dataset]"
  exit 1
fi

if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
else
  PY=python3
fi

echo "=== BASIC FILES ==="
test -f configs/llm_training.yaml && echo "OK: llm_training.yaml" || echo "MISSING: llm_training.yaml"
test -d src/workflow_dataset/llm && echo "OK: llm package" || echo "MISSING: llm package"

echo
echo "=== COMMANDS ==="
$PY -m workflow_dataset.cli llm train --help >/dev/null 2>&1 && echo "OK: llm train command" || echo "FAIL: llm train command"
$PY -m workflow_dataset.cli llm eval --help >/dev/null 2>&1 && echo "OK: llm eval command" || echo "FAIL: llm eval command"
$PY -m workflow_dataset.cli llm demo --help >/dev/null 2>&1 && echo "OK: llm demo command" || echo "FAIL: llm demo command"

echo
echo "=== TRAINING DATA FILES ==="
find data/local/llm -type f \( -name "*.jsonl" -o -name "*.json" -o -name "*.md" \) 2>/dev/null | sort | sed -n '1,120p' || true

echo
echo "=== RUN ARTIFACTS ==="
find data/local/llm/runs -type f 2>/dev/null | sort | sed -n '1,120p' || true

echo
echo "=== EVAL WIRING CHECK ==="
grep -R "dummy predictor\|reference as prediction\|predict_fn\|run_inference" -n src/workflow_dataset 2>/dev/null | sed -n '1,80p' || echo "(no matches)"

echo
echo "=== ENV CHECK ==="
$PY -m pip show mlx-lm 2>/dev/null || echo "mlx-lm not installed"
$PY -m pip show mlx 2>/dev/null || echo "mlx not installed"

echo
echo "Done."
