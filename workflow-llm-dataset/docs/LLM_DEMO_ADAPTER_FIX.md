# LLM Demo Adapter-Loaded Mode Fix

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/llm/mlx_backend.py` | `run_inference`: only resolve `model_path` and `adapter_path` when they exist on disk, so HuggingFace repo ids (e.g. `mlx-community/Llama-3.2-3B-Instruct-4bit`) are passed as-is to `mlx_lm generate`. |
| `src/workflow_dataset/cli.py` | **Demo:** Resolve adapter vs base model explicitly. In adapter mode use `backend.run_inference(base_model, prompt, adapter_path=adapter_path_val)` so the adapter dir is never passed as `--model`. In base-model mode use `backend.run_inference(base_model, prompt)`. Print interpreter, mode, base model, adapter (or “(none)”). On inference error print “Inference failed.” plus a concise message (truncated to 400 chars), no raw traceback. Require base_model in config when in adapter mode. |
| `tests/test_llm_cli.py` | Added `test_llm_demo_base_model_mode_prints_base_and_adapter_none`, `test_llm_demo_adapter_mode_requires_base_model`, `test_llm_demo_adapter_mode_prints_base_and_adapter_path` (mock backend to assert adapter is passed as `adapter_path`, not as model), `test_llm_demo_inference_error_graceful`. Updated `test_llm_demo_reports_mode` to allow “base model” / “Inference failed”. |

## 2. Example demo output — base-model mode

```
interpreter: /path/to/.venv/bin/python3
mode: base_model
base model: mlx-community/Llama-3.2-3B-Instruct-4bit
adapter: (none)
Model output:
...
```

## 3. Example demo output — adapter-loaded mode

```
interpreter: /path/to/.venv/bin/python3
mode: adapter
base model: mlx-community/Llama-3.2-3B-Instruct-4bit
adapter: /path/to/data/local/llm/runs/smoke_20260315_162227/adapters
Model output:
...
```

## 4. Example graceful failure messages

- **No adapter and no base_model:**  
  `No adapter and no base_model. Run 'llm smoke-train' or set base_model in config.`  
  (Exit 1.)

- **Adapter mode but base_model missing in config:**  
  `base_model required in config for adapter inference.`  
  (Exit 1.)

- **Inference error (e.g. missing config):**  
  `Inference failed.`  
  `FileNotFoundError: ... config.json ...`  
  (Message truncated to 400 chars; no traceback.)

## 5. Test results

```
pytest tests/test_llm_cli.py tests/test_llm_run_summary.py -v
# 35 passed
```

New/updated demo tests:

- `test_llm_demo_reports_mode` — output includes mode / base model / interpreter or error.
- `test_llm_demo_base_model_mode_prints_base_and_adapter_none` — base-model mode prints base model and adapter (none).
- `test_llm_demo_adapter_mode_requires_base_model` — with `--adapter` but no base_model in config, exit 1 and clear message.
- `test_llm_demo_adapter_mode_prints_base_and_adapter_path` — with `--adapter`, backend is called with base model and `adapter_path` (adapter dir not passed as model).
- `test_llm_demo_inference_error_graceful` — on inference error, output has “Inference failed” and no raw traceback.
- `test_llm_demo_exits_nonzero_when_no_adapter_no_base_model` — unchanged; still checks exit 1 when neither adapter nor base_model.

## 6. Remaining limitations

- Demo still depends on `mlx_lm generate` (subprocess). If the env or CLI changes, inference can break.
- Base model must be set in config for adapter mode; there is no separate “adapter-only” inference path.
- Error truncation at 400 characters may hide part of long error messages; full stderr is not written to a log file by this path.
- Tests that invoke the real backend (e.g. default config with real base model) can be slow and require network/model access; new adapter-mode tests use a mocked backend.
