# M23C-F1 — Desktop Action Adapter Contracts + Registry — Delivery

## 1. Files modified

| File | Change |
|------|--------|
| `workflow-llm-dataset/src/workflow_dataset/cli.py` | Added `adapters_group` Typer; registered with `app.add_typer(adapters_group, name="adapters")`. Added commands: `adapters list`, `adapters show`, `adapters simulate`. |

## 2. Files created

| File | Purpose |
|------|--------|
| `workflow-llm-dataset/src/workflow_dataset/desktop_adapters/__init__.py` | Package exports: AdapterContract, ActionSpec, BUILTIN_ADAPTERS, register_adapter, list_adapters, get_adapter, check_availability, run_simulate, SimulateResult. |
| `workflow-llm-dataset/src/workflow_dataset/desktop_adapters/contracts.py` | Adapter contract schema: ActionSpec, AdapterContract; BUILTIN_ADAPTERS (file_ops, notes_document, browser_open, app_launch). |
| `workflow-llm-dataset/src/workflow_dataset/desktop_adapters/registry.py` | Registry: register_adapter, list_adapters, get_adapter, check_availability; seeds builtins on first use. |
| `workflow-llm-dataset/src/workflow_dataset/desktop_adapters/simulate.py` | run_simulate(adapter_id, action_id, params) → SimulateResult; dry-run preview only; no real execution. |
| `workflow-llm-dataset/docs/M23C_F1_READ_FIRST.md` | Pre-coding: current state, reuse map, gap, file plan, risk/safety. |
| `workflow-llm-dataset/docs/M23C_F1_DELIVERY.md` | This file: delivery summary, CLI usage, samples, tests, weaknesses. |
| `workflow-llm-dataset/tests/test_desktop_adapters.py` | Tests for list_adapters, get_adapter, check_availability, run_simulate (success and failure cases). |

## 3. Exact CLI usage

From repo root (or with `workflow-dataset` on PATH):

```bash
# List all registered desktop action adapters
workflow-dataset adapters list

# Show full contract for an adapter
workflow-dataset adapters show --id file_ops
workflow-dataset adapters show --id browser_open

# Simulate an action (dry-run; no real execution)
workflow-dataset adapters simulate --id browser_open --action open_url --param url=https://example.com
workflow-dataset adapters simulate --id file_ops --action read_file --param path=/tmp/foo.txt
workflow-dataset adapters simulate -i app_launch -a launch_app -p app_name_or_path=Notes
```

## 4. Sample adapter definitions

Built-in adapters are defined in `desktop_adapters/contracts.py`. Example (browser_open) in code form:

```python
AdapterContract(
    adapter_id="browser_open",
    adapter_type="browser_open",
    capability_description="Open URL in browser. Simulate: preview URL only; no real execution in F1.",
    supported_actions=[
        ActionSpec("open_url", "Open URL in default browser",
                   [{"name": "url", "type": "string", "required": "true"}],
                   ["opened"], supports_simulate=True, supports_real=False),
    ],
    required_approvals=["user_confirm_before_open"],
    supports_simulate=True,
    supports_real_execution=False,
    failure_modes=["invalid_url", "browser_not_available"],
)
```

| Adapter ID | Type | Actions (examples) | Real execution (F1) |
|------------|------|--------------------|---------------------|
| file_ops | file_ops | read_file, list_dir, write_file | No |
| notes_document | notes_document | create_note, append_to_note | No |
| browser_open | browser_open | open_url | No |
| app_launch | app_launch | launch_app | No |

## 5. Sample simulate output

Example for:

```bash
workflow-dataset adapters simulate --id browser_open --action open_url --param url=https://example.com
```

Expected console output:

```
Simulate OK
[Simulate] adapter=browser_open action=open_url
  url=https://example.com
  Would open URL: https://example.com
  Real execution not implemented in F1.
Real execution not implemented for this adapter/action.
```

Example for unknown adapter (exit code 1):

```bash
workflow-dataset adapters simulate --id unknown --action open_url
# Output: Adapter not found: unknown
```

## 6. Exact tests run

```bash
cd workflow-llm-dataset
pytest tests/test_desktop_adapters.py -v
```

Tests included:

- `test_list_adapters_at_least_four` — list returns ≥4 adapters including file_ops, notes_document, browser_open, app_launch.
- `test_get_adapter_file_ops` — get_adapter("file_ops") returns contract with read_file action.
- `test_get_adapter_browser_open` — get_adapter("browser_open") returns contract with open_url.
- `test_get_adapter_unknown_returns_none` — get_adapter("unknown_xyz") returns None.
- `test_check_availability_file_ops` — check_availability("file_ops") returns available=True, supports_simulate=True, supports_real_execution=False.
- `test_check_availability_unknown` — check_availability("unknown_xyz") returns available=False.
- `test_run_simulate_browser_open_url_success` — run_simulate("browser_open", "open_url", {"url": "https://example.com"}) success, preview contains "Would open URL" or "Simulate", real_execution_supported=False.
- `test_run_simulate_file_ops_read_file` — run_simulate("file_ops", "read_file", {"path": "/tmp/foo.txt"}) success, preview contains "Target path" or "Simulate".
- `test_run_simulate_unknown_adapter_fails` — run_simulate("unknown_adapter", "open_url", {}) success=False, message contains "not found".
- `test_run_simulate_unknown_action_fails` — run_simulate("browser_open", "nonexistent_action", {}) success=False.

## 7. Remaining weaknesses (this phase only)

- **No real execution:** All adapters are simulate/dry-run only; no OS, file, or browser calls. Implementing real execution is out of scope for F1.
- **No approval gating in code:** required_approvals are declared on contracts but not enforced by the runner; a future phase would wire approval checks before any real execution.
- **No persistence of adapter state:** Registry is in-memory; builtins are seeded on first use. No loading of custom adapters from config/files yet.
- **CLI param parsing is simple:** `--param key=value` supports only string values; no JSON or typed params in CLI.
- **No integration with agent/sandbox:** The simulate runner is standalone; not yet called from agent loop or sandbox_runner.
- **Limited preview content:** Previews are fixed strings per adapter/action; no actual file path checks or URL validation in simulate mode.
