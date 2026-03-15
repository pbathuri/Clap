# M15 — First Successful Personal LLM Fine-Tune + Real-Model Eval

## 1. Files modified

| Path | Change |
|------|--------|
| `src/workflow_dataset/llm/run_summary.py` | **New.** `write_run_summary()`, `is_successful_run()`, `find_latest_successful_adapter()`, `find_all_successful_adapters()`. |
| `src/workflow_dataset/cli.py` | smoke-train: interpreter/base_model/output run prints, run_summary.json on success/failure, adapter-artifacts line. train: run_summary.json on success/failure. `_find_latest_adapter()` uses `find_latest_successful_adapter()`. eval: auto-use latest successful adapter when `--adapter`/`--model` omitted; report model/adapter path. demo: interpreter + mode/path, backend.run_inference, exit 1 when no adapter and no base_model. New commands: `llm latest-run`, `llm latest-adapter`. |
| `src/workflow_dataset/llm/verify.py` | `_find_latest_adapter_run()` uses `find_all_successful_adapters` / `find_latest_successful_adapter` so only successful runs count as adapter sources. |
| `tests/test_llm_run_summary.py` | **New.** Tests for run_summary write/read, `is_successful_run`, `find_latest_successful_adapter`, `find_all_successful_adapters`. |
| `tests/test_llm_cli.py` | smoke-train test asserts run_summary.json; new tests: verify ignores failed runs, demo exit 1 when no adapter/base_model, latest-adapter/latest-run exit 1 when none. |

## 2. Example smoke-train output

```
interpreter:  /path/to/.venv/bin/python
base_model:   mlx-community/Llama-3.2-3B-Instruct-4bit
output run:   /path/to/workflow-llm-dataset/data/local/llm/runs/smoke_20250315_120000
smoke SFT data -> data/local/llm/smoke_sft
Loading pretrained model
...
smoke-train complete; adapter -> /path/to/.../runs/smoke_20250315_120000/adapters
adapter artifacts: created
```

On failure:

```
interpreter:  ...
base_model:   ...
output run:   ...
smoke SFT data -> ...
smoke-train failed: ...
```
(Exit code 1; run_summary.json still written with `"success": false` and `"error": "..."`.)

## 3. Example run_summary.json

**Successful run** (`data/local/llm/runs/smoke_YYYYMMDD_HHMMSS/run_summary.json`):

```json
{
  "success": true,
  "backend": "mlx",
  "base_model": "mlx-community/Llama-3.2-3B-Instruct-4bit",
  "llm_config_path": "/path/to/configs/llm_training.yaml",
  "start_time": "2025-03-15T12:00:00+00:00",
  "end_time": "2025-03-15T12:02:30+00:00",
  "adapter_path": "/path/to/data/local/llm/runs/smoke_20250315_120000/adapters",
  "error": ""
}
```

**Failed run:**

```json
{
  "success": false,
  "backend": "mlx",
  "base_model": "mlx-community/Llama-3.2-3B-Instruct-4bit",
  "llm_config_path": "/path/to/configs/llm_training.yaml",
  "start_time": "2025-03-15T12:00:00+00:00",
  "end_time": "2025-03-15T12:00:05+00:00",
  "adapter_path": "",
  "error": "mlx_lm.lora training failed: ..."
}
```

## 4. Example latest successful adapter detection

- **`workflow-dataset llm latest-adapter`** (when a successful run exists): prints the adapter dir path; exit 0.
- **`workflow-dataset llm latest-adapter`** (when none): prints "No successful adapter found. Run 'llm smoke-train' first."; exit 1.
- **`workflow-dataset llm latest-run`**: same idea for the run directory path.
- **`llm verify`**: "adapters: OK  latest=/path/to/runs/smoke_..." only if at least one run has `run_summary.json` with `success: true` and an existing adapter dir. Failed runs (or runs without run_summary) are ignored.

## 5. Example eval output (real-model mode)

With latest successful adapter auto-selected (no `--adapter`):

```
Using latest successful adapter: /path/to/data/local/llm/runs/smoke_20250315_120000/adapters
model/adapter: /path/to/.../adapters
eval done: 15 examples  mode=real_model -> data/local/llm/runs/eval_out/predictions.jsonl
  token_overlap: 0.0814
  explanation_completeness: 1.0000
  exact_match: 0.0000
```

With explicit `--adapter`:

```
model/adapter: /path/to/adapters
eval done: 15 examples  mode=real_model -> ...
```

Baseline (no adapter, no auto-adapter):

```
eval done: 15 examples  mode=baseline -> ...
```

## 6. Example demo output (adapter-loaded mode)

When a successful adapter exists and no `--adapter` is passed:

```
interpreter: /path/to/.venv/bin/python
mode: adapter  path: /path/to/data/local/llm/runs/smoke_20250315_120000/adapters
Model output:
...
```

When no adapter and no base_model:

```
No adapter and no base_model. Run 'llm smoke-train' or set base_model in config.
```
(Exit code 1.)

## 7. Test results

- **test_llm_run_summary.py**: 11 tests (write_run_summary success/failure, is_successful_run cases, find_latest_successful_adapter, find_all_successful_adapters). All pass.
- **test_llm_cli.py**: 20 tests including run_summary in smoke-train, verify ignores failed runs, demo/latest-adapter/latest-run exit behavior. All pass.

Full run:

```
pytest tests/test_llm_run_summary.py tests/test_llm_cli.py -v
# 31 passed
```

## 8. Remaining limitations

- **Smoke-train** still requires `datasets`, `mlx`, `mlx-lm` and a valid base model; failure to load data or model is reported via run_summary and stderr but not parsed into structured fields.
- **Real-model eval** runs inference per example (no batching); slow for large test sets.
- **Demo** uses backend `run_inference()` (subprocess to mlx_lm generate); path must be to a real adapter or base model.
- **Verify** “adapter_artifacts_present” and “latest_run_dir” count only runs with `run_summary.json` and `success: true`; legacy runs without run_summary are not considered successful.
- **latest-run / latest-adapter** are convenience helpers; scripts can instead parse `run_summary.json` under `runs_dir` or call the Python API `find_latest_successful_adapter(runs_dir)`.
