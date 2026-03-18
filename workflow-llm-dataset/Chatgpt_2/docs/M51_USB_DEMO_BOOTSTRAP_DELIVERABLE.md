# M51A–M51D — USB Bootstrap Runtime + Environment Readiness

## BEFORE CODING (analysis)

### 1. Existing startup / install / bootstrap / readiness behavior

| Area | Behavior |
|------|----------|
| **`edge/`** | `run_readiness_checks`, `checks_summary`, `generate_edge_readiness_report` — Python version, config, sandbox paths, optional LLM config. |
| **`local_deployment/`** | `run_install_check` (wraps edge checks + product readiness), `run_first_run` (ensures dirs via `SANDBOX_PATHS`, install-check, onboarding optional, first-run summary). |
| **`package_readiness/`** | `build_readiness_summary` — machine + product readiness, first-user install flags. |
| **`install_upgrade/`** | Channels, version, upgrade plan — product upgrade, not USB-specific. |
| **`deploy_bundle/`** | Production deploy bundles, health, rollback — not investor USB path. |
| **`onboarding/`** | `bootstrap_profile`, `run_onboarding_flow` — post-install operator profile. |
| **CLI** | `workflow-dataset edge readiness`, `package install-check`, `package first-run`, `package local-deploy`. |

### 2. What can be reused for USB demo mode

- **Edge checks** as-is against bundle root (`run_readiness_checks(repo_root=bundle_root)`).
- **`run_first_run` / `_ensure_local_dirs`** after bundle is writable.
- **Threshold patterns** from `configs/demo_usb.yaml` (mirrors edge tier thinking).
- **Host-only manifest** pattern (similar to `data/local/deployment/` but under `~/.workflow-demo-host`).

### 3. What was missing for USB-hosted launch

- Explicit **demo bundle root** resolution (`WORKFLOW_DEMO_BUNDLE_ROOT`, `--bundle-root`, cwd).
- **Read-only USB** path: honest **BLOCKED** + “copy to writable disk” (no silent failure).
- **Capability tri-state**: full / degraded / blocked with **operator-facing copy**.
- **Reversible host state** separate from bundle (`.workflow-demo/last_bootstrap.json`).
- **Single demo command group** for investor runbook.

### 4. File plan (implemented)

| Path | Role |
|------|------|
| `src/workflow_dataset/demo_usb/models.py` | Phase A models |
| `demo_usb/bundle_root.py` | Bundle resolution |
| `demo_usb/config_load.py` | `configs/demo_usb.yaml` thresholds |
| `demo_usb/host_analysis.py` | Phase B host profile |
| `demo_usb/bootstrap.py` | Phase C flow + readiness classification |
| `demo_usb/reports.py` | Phase D text reports |
| `configs/demo_usb.yaml` | Bounded thresholds |
| `scripts/demo_usb_launch.sh` | Launcher |
| `cli.py` | `demo` Typer group |
| `tests/test_demo_usb.py` | Phase E |

### 5. Safety / risk note

- **Does not** elevate privileges or write outside bundle + declared host dir.
- **Read-only USB** → blocked until copy to disk (avoids half-broken demos).
- **Host manifest** is JSON under `~/.workflow-demo-host/<bundle_name>/.workflow-demo/` — user can delete folder to reset.
- **Chmod tests** Unix-only (skipped on Windows).

### 6. Demo-bootstrap principles

- Local-first, privacy-first, bounded, inspectable, fast to first value.
- Deterministic handoff: `demo launch` prints exact next commands.
- Degraded mode explained honestly (no LLM config, low RAM).

### 7. What this block does NOT do

- Cloud installer, enterprise agent, generic system management.
- Dedicated AI hardware / full packaging rewrite.
- Overlay `get_repo_root()` to split code vs data (would broaden core paths).
- Auto-copy bundle from read-only USB to disk.

---

## FINAL OUTPUT

### 1. Files modified

- `src/workflow_dataset/cli.py` — added `demo` command group.

### 2. Files created

- `src/workflow_dataset/demo_usb/__init__.py`
- `src/workflow_dataset/demo_usb/models.py`
- `src/workflow_dataset/demo_usb/bundle_root.py`
- `src/workflow_dataset/demo_usb/config_load.py`
- `src/workflow_dataset/demo_usb/host_analysis.py`
- `src/workflow_dataset/demo_usb/bootstrap.py`
- `src/workflow_dataset/demo_usb/reports.py`
- `configs/demo_usb.yaml`
- `scripts/demo_usb_launch.sh`
- `tests/test_demo_usb.py`
- `docs/M51_USB_DEMO_BOOTSTRAP_DELIVERABLE.md`

### 3. Launcher / CLI usage

```bash
cd workflow-llm-dataset
export PYTHONPATH=src   # if not pip install -e .
export WORKFLOW_DEMO_BUNDLE_ROOT=/path/to/usb/copy   # optional if cd there

workflow-dataset demo readiness
workflow-dataset demo env-report
workflow-dataset demo bootstrap
workflow-dataset demo bootstrap --skip-first-run
workflow-dataset demo launch
workflow-dataset demo degraded-report

# JSON
workflow-dataset demo readiness --json

# Shell launcher (from repo root)
./scripts/demo_usb_launch.sh bootstrap
./scripts/demo_usb_launch.sh readiness
```

### 4. Sample readiness report (text)

```
=== USB demo readiness ===
Capability: DEGRADED
Ready for onboarding: True

Degraded mode: reduced_model_path
No LLM training config — model-backed demos unavailable; CLI and local workflows OK.

Host:
  Python 3.13.x  ok=True
  Platform: Darwin
  Disk free (host area): ~50000 MB
  RAM: ~16384 MB
  Bundle writable: True
  Host workspace: /Users/you/.workflow-demo-host/workflow-llm-dataset

Next steps:
  • Run: workflow-dataset demo bootstrap (if not yet)
  • Run: workflow-dataset package first-run
  • Run: workflow-dataset onboard bootstrap
  • Investor path: workflow-dataset demo env-report — then operator quickstart.
```

(Blocked example: `Capability: BLOCKED`, `bundle_read_only_copy_required`, copy-to-disk instructions.)

### 5. Sample degraded-mode report

```
=== Degraded demo mode ===
No LLM training config — model-backed demos unavailable; CLI and local workflows OK.

Operational notes:
  • Prefer: package install-check, edge readiness, operator quickstart.
  • Avoid: large model loads or long-running training on this host.
```

### 6. Sample bootstrap flow output

```
=== Demo bootstrap run ===
run_id: demo_usb_2026-03-17T12...
host_workspace: /Users/you/.workflow-demo-host/workflow-llm-dataset
host_workspace_state: ready
first_run_invoked: True

  log: capability=full
  log: install_check_passed=True

Created / updated:
  data/local/workspaces
  ~/.workflow-demo-host/.../last_bootstrap.json
  data/local/demo_usb/bootstrap_state.yaml

=== USB demo readiness ===
...
```

### 7. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_demo_usb.py -v --tb=short
```

**Result:** 9 passed.

### 8. Remaining gaps before investor-demo readiness

1. **PyYAML / deps** on spare laptop — document `pip install -e ".[...]"` or minimal `pip install pyyaml typer rich` for CLI.
2. **One-command USB image** — zip/script to produce folder tree + README for investors (out of scope here).
3. **Optional**: copy-from-read-only-USB helper script (explicit user consent).
4. **Golden demo script** — 2–3 fixed commands after bootstrap (product-specific).
5. **Visual / deck alignment** — operator messaging, not code.
