# M23C-F1 — Desktop Action Adapter Contracts + Registry — Read First

## 1. Current state summary

- **Product:** Local-first, operator-controlled ops/reporting: templates, chain lab, intake, mission control, dashboard, review/package/staging, edge readiness. Build report confirms the system is not yet a general desktop operator.
- **README:** Long-term vision = plug-and-play personal edge AI / desktop work operator; observation and execution layers are largely scaffolding/interfaces today.
- **Execution:** `agent/execution_modes.py` — Observe, Simulate, Assist, Automate; default **Simulate**. `agent/sandbox_runner.py` — stub (not implemented). `agent/action_policy.py` — may_propose, may_execute_locally, check_boundary (not implemented).
- **Apply:** `apply/apply_executor.py` — copy from sandbox to target only after explicit confirmation; backups on overwrite.
- **Output adapters:** `output_adapters/adapter_registry.py` — for **output bundles** (spreadsheet, creative, design, ops handoff); not desktop actions.
- **Config:** `configs/settings.yaml` — `agent.execution_mode: simulate`, `sandbox_enabled: true`.

## 2. Exact reusable modules

| Module | Use for M23C-F1 |
|--------|------------------|
| `agent/execution_modes.py` | Align with ExecutionMode.SIMULATE; is_safe_default. |
| `agent/action_policy.py` | Future: gate real execution via may_execute_locally / check_boundary. |
| `output_adapters/adapter_registry.py` | Pattern only: register, list, get; we add a **new** package for desktop action adapters (no reuse of output adapter types). |
| `apply/apply_executor.py` | Pattern: explicit confirmation, no silent writes. |
| Config `agent.execution_mode` | Simulate-first; adapters respect it. |

## 3. Gap between current repo and desktop-operator goal

- **No typed desktop action adapter contracts** — file/folder, notes/document, browser/open-url, app-launch are not defined as adapters with capability, actions, approvals, simulate/real flags, inputs/outputs, failure modes.
- **No adapter registry for desktop actions** — only output bundle adapters exist.
- **No simulate/dry-run runner** for adapter actions — sandbox_runner is a stub; no “run this action in simulate mode” for a given adapter/action/params.
- **No CLI** for listing/inspecting/simulating desktop action adapters.

## 4. File plan

| Item | Path | Content |
|------|------|--------|
| Contract schema | `desktop_adapters/contracts.py` | AdapterContract dataclass; ActionSpec; built-in adapter definitions (file_ops, notes_document, browser_open, app_launch). |
| Registry | `desktop_adapters/registry.py` | register_adapter, list_adapters, get_adapter, check_availability. |
| Simulate runner | `desktop_adapters/simulate.py` | run_simulate(adapter_id, action, params) → SimulateResult (preview, success, message; no real execution). |
| Package init | `desktop_adapters/__init__.py` | Exports. |
| CLI | `cli.py` | New `adapters` Typer group: `adapters list`, `adapters show --id`, `adapters simulate --id --action --param`. |
| Tests | `tests/test_desktop_adapters.py` | Registry, list, show, simulate for built-in adapters; no real execution. |
| Doc | `docs/M23C_F1_DELIVERY.md` | Delivery: usage, samples, tests, weaknesses. |

## 5. Risk / safety note

- **No real execution in F1:** All adapter actions in this phase are simulate/dry-run only; `supports_real_execution` is false or optional; CLI simulate command never calls OS/file/browser.
- **Explicit contracts:** Each adapter declares required_approvals, failure_modes, expected_inputs/outputs; no hidden behavior.
- **Local-only:** No cloud APIs; no OS hooks or daemons; registry and state under project/repo.
- **Preserve existing safety:** Do not change execution_modes default, apply confirmation flow, or sandbox semantics.
