# M23N — First-Run Onboarding Analysis (pre-coding)

## 1. What onboarding/setup already exists

- **Setup pipeline** (`setup init`, `setup run`, `setup status`, `setup summary`): Creates a session, runs stages (bootstrap → inventory → parsing → interpretation → graph_enrichment → llm_prep → summary). Resumable, local-only. Produces session/progress and a markdown summary in `data/local/setup_reports/<session_id>_summary.md`.
- **Console** (`workflow-dataset console`): TUI with Home, Setup summary, Project explorer, Suggestions, Drafts, Materialize, Apply, Rollback, Chat. No dedicated "first-run" path.
- **Edge readiness**: `edge/report.py` generates edge readiness report, missing dependency report, tier matrix. No first-run wizard that uses it.
- **No single "onboard" entrypoint**: A first-run user must discover `setup init` → `setup run` and separately learn about approvals, capability discovery, job packs, and dashboard.

## 2. What capability discovery/approval surfaces already exist

- **Capability discovery** (`capability_discovery/`): `run_scan()` returns `CapabilityProfile` (adapters_available, approved_paths, approved_apps, action_scopes). `format_profile_report()` produces text. No CLI command exposes it directly.
- **Approval registry** (`data/local/capability_discovery/approvals.yaml`): `load_approval_registry`, `save_approval_registry`, `get_registry_path`. Used by `approval_check.check_execution_allowed()` to gate `run_execute`. No guided "approval bootstrap" flow.
- **Trusted actions** (`desktop_bench/trusted_actions.py`): `get_trusted_real_actions()` returns subset of actions that are (1) in TRUSTED_ADAPTER_ACTIONS and (2) when registry exists, in approved_action_scopes with executable=true. Report via `list_trusted_actions_report()`.
- **Work state** (`context/work_state.py`): `build_work_state()` aggregates approvals_file_exists, approved_paths_count, approved_action_scopes_count, adapter_ids from local sources. Used by mission_control and copilot.
- **Mission control** (`mission_control/state.py`): Aggregates product_state, evaluation_state, desktop_bridge (adapters, approvals path, counts), job_packs, copilot, work_context, corrections. No first-run summary.

## 3. What a first-run user would find confusing today

- No single "start here" path: they see many commands (setup, dashboard, console, packs, copilot, mission-control) with no clear order.
- Approvals are invisible until something fails: `approvals.yaml` is only created when the user (or docs) adds it; no guided "approve these paths/scopes" flow.
- Unclear what is "safe" vs "simulate-only": trusted real actions and capability profile are not surfaced in one place; job packs have trust_level but no unified "what can I do now" view.
- Machine/user identity is implicit: no local profile that says "this machine, these capabilities, this approval state."
- Recommended first job packs/routines are buried in copilot/recommendations and job_packs_report; no "recommended first workflow" in one screen.

## 4. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/onboarding/__init__.py` |
| Create | `src/workflow_dataset/onboarding/bootstrap_profile.py` — model, build, save, load bootstrap profile (machine_id, adapters, capabilities, approval summary, trusted subset, simulate_only, recommended_job_packs). Persist to `data/local/onboarding/bootstrap_profile.yaml`. |
| Create | `src/workflow_dataset/onboarding/onboarding_flow.py` — run_flow(): env readiness, capabilities, required approvals, next steps; status display. |
| Create | `src/workflow_dataset/onboarding/product_summary.py` — build_first_run_summary(): what can do safely, benchmarked/trusted, simulate-only, ready jobs/routines, recommended first workflow. |
| Create | `src/workflow_dataset/onboarding/approval_bootstrap.py` — batch review (pending requests), grouped scopes, explicit refuse, consequence text. No auto-grant. |
| Modify | `src/workflow_dataset/cli.py` — add `onboard_group` with `onboard`, `onboard status`, `onboard bootstrap`; optionally `onboard approve` (calls approval_bootstrap). |
| Create | `tests/test_onboarding.py` — bootstrap profile creation, onboarding status, approval bootstrap, refusal, first-run messaging. |
| Create | `docs/M23N_ONBOARDING.md` — usage, sample profile, sample summary, safety. |

## 5. Safety/risk note

- **No hidden scans**: Bootstrap profile and onboarding flow use existing capability_discovery `run_scan()` (adapters + approval registry only), edge checks, and job_packs/copilot reads. No new filesystem crawling beyond what setup already does when user runs `setup run`.
- **No auto-grant**: Approval bootstrap only presents requests and writes to `approvals.yaml` when the user explicitly approves; refusal paths do not add entries. Existing `check_execution_allowed` remains the gate.
- **Local-only**: All outputs under `data/local/onboarding/` and existing `data/local/capability_discovery/`. No cloud or telemetry.
- **Preserve gates**: We do not change `approval_check.check_execution_allowed` or bypass approval registry; we only make it easier to populate and review.
