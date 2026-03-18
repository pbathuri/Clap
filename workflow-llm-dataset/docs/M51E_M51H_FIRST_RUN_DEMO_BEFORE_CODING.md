# M51E–M51H — First-Run Onboarding + Role/Memory Bootstrap: Before Coding

## 1. What onboarding and role-selection behavior already exists

| Area | What exists |
|------|-------------|
| **onboarding** | `run_onboarding_flow`, `get_onboarding_status`, `BootstrapProfile` (capabilities, approvals, job packs), `onboard bootstrap/approve/status`, approval bootstrap. |
| **first-run** | `local_deployment.run_first_run` (dirs, install-check, onboarding), `package first-run`. |
| **quickstart** | `first_value_flow` (ordered steps: profile, runtime, onboard, jobs, inbox, simulate job), `first_run_tour`. |
| **defaults / role** | `defaults apply` (first_user, calm_default, full), `day preset set` (founder_operator, analyst, developer, document_heavy, supervision_heavy). |
| **onboarding_defaults** | Calm home first command, safe surfaces, `recommended_next_after_home`. |
| **vertical / launch** | Vertical packs, launch kits, production-cut (CLI exists; not auto-run in demo flow). |
| **personal graph** | `ingest_file_events` / `graph_builder.ingest_events` from observation events + root_paths. |
| **memory substrate** | `MemoryItem` + `ingest()` with compression; local SQLite backend. |
| **continuity / workspace** | `workspace home`, continuity engine; not wired as a single “demo first run”. |

## 2. What can be reused for a demo-first onboarding path

- **Bootstrap profile** — optional follow-on after demo (`onboard bootstrap`); demo flow can suggest it.
- **Day preset + defaults** — bind role preset to `day preset set --id` and `defaults apply` commands (document only or run via subprocess optional; we document commands).
- **Memory ingest** — `memory_substrate.ingest([MemoryItem], synthesize=True)` for bounded demo snippets.
- **Personal graph** — build synthetic file events from scanned demo paths and call `ingest_events` with demo root as `root_paths` (bounded file list).
- **First-value flow** — reuse step ordering idea; demo flow is narrower (role → sample workspace → memory → ready).

## 3. What is missing for a clean “plug in → onboard → ready” flow

- **Demo-scoped session** — no persisted “demo onboarding session” with role, trust choice, bootstrap status.
- **Tight role presets for investor demo** — founder/operator as primary; document-review and analyst as secondary; each with vertical pack id, trust posture label, day preset, explanation text.
- **Bounded sample workspace** — shipped small folder + explicit scan limits (extensions, max files, max bytes).
- **Demo memory bootstrap** — single pipeline: scan → project hints / themes / priorities → memory items + optional graph ingest.
- **Ready-to-assist state** — one structured object + CLI output: role, pack, memory summary, inferred context, first-value command, explicit “ready” flag.
- **Dedicated CLI** — `demo onboarding *` commands without replacing `onboard`.

## 4. Exact file plan

| Path | Purpose |
|------|---------|
| `docs/M51E_M51H_FIRST_RUN_DEMO_BEFORE_CODING.md` | This document. |
| `src/workflow_dataset/demo_onboarding/__init__.py` | Public exports. |
| `src/workflow_dataset/demo_onboarding/models.py` | Demo session, role preset, workspace source, bootstrap plan, completion, ready-to-assist, trust posture, bootstrap confidence. |
| `src/workflow_dataset/demo_onboarding/presets.py` | Three role presets + default founder_operator_demo. |
| `src/workflow_dataset/demo_onboarding/store.py` | Persist/load session JSON under `data/local/demo_onboarding/`. |
| `src/workflow_dataset/demo_onboarding/memory_bootstrap.py` | Bounded scan, hints extraction, memory ingest, graph optional. |
| `src/workflow_dataset/demo_onboarding/flow.py` | start, select_role, bootstrap_memory, build_ready_state, sequence. |
| `docs/samples/demo_onboarding_workspace/**` | Small sample .md/.txt tree. |
| `src/workflow_dataset/cli.py` | `demo` group → `demo onboarding` subcommands. |
| `tests/test_demo_onboarding.py` | Session, role, bootstrap, ready-state, low-info, incomplete. |
| `docs/M51E_M51H_DELIVERABLE.md` | Final deliverable (samples, tests, gaps). |

## 5. Safety/risk note

- **No whole-disk scan** — only user-supplied path or bundled sample; hard caps on file count, depth, size.
- **No cloud / identity** — all local; trust posture is conservative by default (simulate-first messaging).
- **Honest “learning”** — summaries label inferred content as heuristic (filename + light text stats), not deep personalization.
- **Do not auto-grant approvals** — demo flow documents `onboard approve`; does not write approval registry.

## 6. Onboarding/bootstrap principles

- **Fast credible path** — few steps; primary role pre-highlighted.
- **Inspectable** — bootstrap writes summary JSON; memory source tagged `demo_onboarding`.
- **Bounded** — caps everywhere; empty/low-info workspace still completes with explicit low-confidence state.
- **Composable** — existing `onboard`, `defaults`, `day preset` remain the system of record for full setup.

## 7. What this block will NOT do

- Redesign production onboarding or support every role/vertical.
- Crawl laptop or arbitrary trees without limits.
- Add accounts, cloud identity, or SSO.
- Claim learning beyond bounded inference from a small sample set.
