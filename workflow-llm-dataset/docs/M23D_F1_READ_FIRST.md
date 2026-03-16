# M23D-F1 — Capability Discovery + Approval Registry — Read First

## 1. Current adapter layer (post M23C-F1/F2/F3)

- **Adapters:** file_ops, notes_document, browser_open, app_launch (BUILTIN_ADAPTERS). Registry: list_adapters, get_adapter, check_availability → available, supports_simulate, supports_real_execution.
- **Per-action:** Each AdapterContract has supported_actions with ActionSpec(supports_simulate, supports_real). file_ops/notes_document have some actions executable (inspect_path, list_directory, snapshot_to_sandbox, read_text, summarize, propose_status); browser_open and app_launch are simulate-only.
- **Approved apps:** APPROVED_APP_NAMES in desktop_adapters/app_allowlist.py (hardcoded tuple). No user-editable approval store.
- **Paths:** get_sandbox_root(), DESKTOP_ADAPTERS_SANDBOX; config paths (paths.*, materialization_workspace_root, etc.). No explicit "approved paths" list for capability.
- **No capability profile or approval registry** that aggregates adapters + paths + apps + action scopes for reporting.

## 2. Reusable runtime/config pieces

| Piece | Use for M23D-F1 |
|-------|------------------|
| list_adapters(), check_availability(adapter_id) | Enumerate adapters and whether each supports simulate/real. |
| AdapterContract.supported_actions, ActionSpec.supports_simulate, supports_real | Derive action scopes (simulate-only vs executable) per adapter. |
| APPROVED_APP_NAMES (app_allowlist) | Seed or display approved apps; registry can extend/override. |
| config paths (settings.yaml): paths.*, materialization_workspace_root, setup_dir, etc. | Optional seed for "approved paths" (lightweight: config-only, no filesystem scan). |
| data/local/* pattern | Store approval registry under data/local/capability_discovery/ (e.g. approvals.yaml). |
| get_repo_root() / path_utils | Resolve repo root for registry path and config. |

## 3. File plan

| Item | Path | Content |
|------|------|--------|
| Pre-coding doc | docs/M23D_F1_READ_FIRST.md | This file. |
| Models | capability_discovery/models.py | CapabilityProfile (adapters_available, approved_paths, approved_apps, action_scopes), AdapterCapability, ActionScope. |
| Approval registry | capability_discovery/approval_registry.py | ApprovalRegistry (approved_paths, approved_apps, approved_action_scopes); load/save from data/local/capability_discovery/approvals.yaml; default empty. |
| Discovery | capability_discovery/discovery.py | run_scan(repo_root?, config_path?) → CapabilityProfile: list_adapters + check_availability, load approval registry, merge action scopes from contracts. |
| Report | capability_discovery/report.py | format_profile_report(profile) → str (text/markdown). |
| Package init | capability_discovery/__init__.py | Exports. |
| CLI | cli.py | capabilities_group: `capabilities scan`, `capabilities report`; `approvals list` (or under capabilities). |
| Tests | tests/test_capability_discovery.py | Discovery output shape, approval registry load/save, report contains adapters. |
| Delivery doc | docs/M23D_F1_DELIVERY.md | Files, sample report, sample registry, CLI, tests. |

## 4. Risk note

- **No hidden system scanning:** Scan uses only (1) adapter registry (in-memory), (2) optional config paths, (3) approval registry file if present. No deep filesystem crawl, no process enumeration, no network.
- **No cloud:** All data local; approval registry is a local file.
- **Explicit approvals:** approved_paths, approved_apps, approved_action_scopes are explicitly listed in the registry; no implicit approval by default beyond contract-level supports_real.
- **Lightweight:** Discovery is O(adapters) + file read; no heavy I/O.
