# Detailed Build Report — workflow-llm-dataset (Clap)

**Purpose:** Single detailed report of what was built so far, what was built concurrently across chats, what is achieved, and which prompts were used. This document is extensive and markdown-only.

---

## 1. Executive summary

The **workflow-llm-dataset** project inside the **Clap** repo is a **local-first, operator-controlled** product for ops/reporting workflows. It is not a general multi-agent or cloud platform. The following layers exist today:

| Layer | Scope | Status |
|-------|--------|--------|
| **Workflow suite** | weekly_status, status_action_bundle, stakeholder_update_bundle, meeting_brief_bundle, ops_reporting_workspace | Validated; artifacts saved to sandbox |
| **Pilot / cohort** | Narrow pilot, graduation, broader controlled cohort (M21O, M21P, M21Q) | Real; session/feedback aggregation, cohort reports |
| **Review / package / staging** | Operator review queue, approve artifacts, build package, staging board, apply-plan | Real; M21T, M21V |
| **Mission control (M22B)** | Unified internal control plane: product, evaluation, development, incubator state + next action | Built; read-heavy, operator-controlled |
| **Role-based review lanes (M22C)** | operator, reviewer, stakeholder-prep, approver; lane-status, assign-lane, list-lane | Built; file-based, no cloud |
| **Local knowledge intake (M22D)** | Intake add/list/report; snapshot into sandbox; release demo --intake | Built; user-owned inputs only |
| **Workflow composer / templates (M22E)** | Templates list/show; release demo --template; artifact set/order from template | Built; YAML/JSON under data/local/templates |
| **Internal chain lab (M23A)** | Chain list/run/status; step sequences via CLI; run outputs persisted | Built; operator-started, no uncontrolled loops |
| **Edge / hardware readiness (M23B)** | Edge profile, readiness checks, workflow matrix, missing-deps, package-report | Built; local deployment assumptions explicit |
| **Evaluation / planning** | Eval runbook, devlab runbook, proposal generator (D3), experiment queue | Present or planned; see runbooks |
| **Dashboard / command center** | dashboard, drill-downs (workspace, package, cohort, apply-plan), action macros (C4) | Real; M21U, C2, C4 |

All of the above stay **local-first**, **sandbox-only**, and **operator-controlled** (no auto-merge, no auto-apply to production, no hidden cloud).

---

## 2. What was built so far (by deliverable)

### 2.1 M22B — Local Agent Product Foundry / Mission Control

**Objective:** Unify internal development surfaces into one local mission-control layer: product state, benchmark state, pilot/cohort state, proposal/experiment state, incubator state, and a recommended next move.

**What was built:**

- **Mission control state aggregation** (`src/workflow_dataset/mission_control/state.py`): Reads from local sources only:
  - **Product state:** validated workflows (REPORTING_WORKFLOWS), cohort recommendation/sessions/avg usefulness, review_package (unreviewed, package_pending), staging, recent workspaces (from `release.dashboard_data.get_dashboard_data`).
  - **Evaluation state:** latest_run_id, recommendation, best_run_id, runs_count, comparison (regressions/improvements), workflows_tested (from eval board and list_runs).
  - **Development state:** experiment queue (queued/running/done), proposal queue (pending/accepted/rejected) from devlab.
  - **Incubator state:** candidates_by_stage, promoted_count, rejected_count, hold_count from incubator registry.
  - **local_sources:** repo_root and all paths used for provenance.
- **Next-action engine** (`mission_control/next_action.py`): Returns one of `build`, `benchmark`, `cohort_test`, `promote`, `hold`, `rollback` with rationale and detail. Logic: rollback if eval says revert; else build if pending proposals or unreviewed workspaces; else promote if incubator has candidates and none promoted; else benchmark if no runs or hold/refine; else cohort_test if cohort suggests expand/test; else hold.
- **Report formatter** (`mission_control/report.py`): `format_mission_control_report(state=None, repo_root=None)` produces a single text report with sections [Product], [Evaluation], [Development], [Incubator], recommended next action, and footer “Operator-controlled. No automatic changes.”
- **CLI:** `workflow-dataset mission-control [--repo-root PATH] [--output FILE]`.

**Files:** `mission_control/__init__.py`, `state.py`, `next_action.py`, `report.py`; `cli.py` (one command); `tests/test_mission_control.py`; `docs/MISSION_CONTROL_VALIDATION.md`.

**Tests:** `pytest tests/test_mission_control.py -v` (4 passed).

---

### 2.2 M22C — Team Pilot Workspace + Role-Based Review Lanes

**Objective:** Local-first team pilot workspace model with role-based review lanes (operator, reviewer, stakeholder-prep, approver) for routing artifacts and keeping review state inspectable.

**What was built:**

- **Lane metadata in review state** (`release/review_state.py`): `LANES`, load/save `lane` in review JSON, `set_workspace_lane(workspace_path, lane)`.
- **Lane views** (`release/lane_views.py`): `get_lane_summary`, `list_workspaces_in_lane`, `list_packages_in_lane`, `get_lane_status`, `set_package_lane`. Packages get lane from `package_manifest.json` (set at build or via assign-lane).
- **Package builder:** Writes workspace lane into `package_manifest.json` when building a package.
- **CLI:** `workflow-dataset review lane-status`; `review assign-lane --workspace PATH --lane LANE` or `--package PATH --lane LANE`; `review list-lane --lane LANE [--packages]`; `review package-status` shows lane.
- **Storage:** Workspace lane in `data/local/review/<workflow>/<run_id>.json`; package lane in `data/local/packages/<ts_id>/package_manifest.json`.

**Files:** `release/review_state.py`, `release/lane_views.py`, `release/package_builder.py`, `cli.py`, `tests/test_review_lanes.py`, `docs/M22C_REVIEW_LANES_VALIDATION.md`.

**Tests:** `pytest tests/test_review_lanes.py -v` (9 passed).

---

### 2.3 M22D — Local Knowledge Intake Center for User-Owned Inputs

**Objective:** Local input-ingestion layer: register paths, snapshot into sandbox, parse/extract structure, make intake sets available to workflows, preserve provenance.

**What was built:**

- **Intake registry** (`intake/registry.py`): `add_intake(label, paths, input_type)`, `get_intake`, `list_intakes`. Snapshots copy files (e.g. .md, .txt, .csv) into `data/local/intake/<label>/<ts_id>/`; originals never mutated. Registry in `data/local/intake/registry.json`.
- **Intake load** (`intake/load.py`): `load_intake_content(label)` returns (combined_content, source_descriptions) for use as task context in release demo.
- **Intake report** (`intake/report.py`): `intake_report(label)` returns file inventory, parse summary (by extension, total chars), suggested workflows; `format_intake_report_text`.
- **Release demo integration:** `release demo --intake <label>` loads intake content and merges into task context; manifest stores `intake_used`, `intake_name`, and intake entries in `input_sources_used`. `workspace_rerun_diff.infer_rerun_args` includes intake for rerun-from.
- **CLI:** `workflow-dataset intake add --path PATH --label LABEL [--type TYPE]`; `intake list`; `intake report --label LABEL [--output FILE]`.

**Files:** `intake/__init__.py`, `registry.py`, `load.py`, `report.py`; `cli.py`; `release/workspace_rerun_diff.py`; `tests/test_intake.py`; `docs/M22D_INTAKE_VALIDATION.md`.

**Tests:** `pytest tests/test_intake.py -v` (7 passed).

---

### 2.4 M22E — Workflow Composer + Template Studio

**Objective:** Local-first template/composer layer: define reusable workflow templates, control which artifacts are generated and in what order, stay within validated workflows.

**What was built:**

- **Template registry** (`templates/registry.py`): `load_template(id)`, `get_template`, `list_templates`, `template_artifact_order_and_filenames`. Templates are YAML/JSON under `data/local/templates/`. Each template: id, name, description, workflow_id (one of the five ops/reporting workflows), artifacts (ordered list of artifact keys), optional wording_hints. Artifacts validated per workflow.
- **Release demo --template:** When `--template <id>` is set, workflow is taken from template; when saving an ops_reporting_workspace, artifacts dict and artifact_list are built only from template’s artifacts in template order. Manifest includes `template_id`.
- **Sample templates:** `data/local/templates/ops_reporting_core.yaml` (status_brief, action_register, decision_requests); `weekly_plus_stakeholder.yaml` (weekly_status, stakeholder_update, decision_requests).
- **CLI:** `workflow-dataset templates list`; `templates show --id ID`; `workflow-dataset release demo --template ID --save-artifact`.

**Files:** `templates/__init__.py`, `templates/registry.py`; `data/local/templates/*.yaml`; `cli.py`; `tests/test_templates.py`; `docs/M22E_TEMPLATES_VALIDATION.md`. Additional concurrent docs: `M22E_WORKFLOW_COMPOSER_READ_FIRST.md`, `M22E_F2_DELIVERY.md`, `M22E_F2_TEMPLATE_VERSIONING_READ_FIRST.md`.

**Tests:** `pytest tests/test_templates.py -v` (9 passed).

---

### 2.5 M23A — Internal Agent Chain Lab (Operator-Controlled)

**Objective:** Local operator-controlled chain runner: define small step sequences, run them locally, persist intermediate artifacts, compare chain variants, remain operator-started and stoppable.

**What was built:**

- **Chain definition** (`chain/registry.py`): Chains are YAML/JSON under `data/local/chains/`. Each chain: id, name, steps (id, type, params or cmd), expected_artifacts, stop_conditions (e.g. on_step_failure). Step types: `command` (raw cmd), `intake_add` (params → workflow-dataset intake add), `release_demo` (params → workflow-dataset release demo).
- **Chain runner** (`chain/runner.py`): `run_chain(chain_id)` creates `data/local/chains/runs/<ts>_<rid>/`, runs each step via subprocess (expanded CLI command), writes per-step JSON and log, writes `run_report.json` (status, steps, operator_notes). Stop on first failure if `stop_conditions.on_step_failure`.
- **Run inspection:** `get_run_status(run_spec)` (run id or "latest"), `list_runs(limit)`.
- **CLI:** `workflow-dataset chain list`; `chain run --id ID [--no-stop-on-failure] [--timeout N] [--notes TEXT]`; `chain status --run latest|RUN_ID`.
- **Sample chains:** `data/local/chains/ops_reporting_chain_v1.yaml` (intake_add then release_demo); `simple_command_chain.json` (echo steps).

**Files:** `chain/__init__.py`, `chain/registry.py`, `chain/runner.py`; `cli.py`; `data/local/chains/*.yaml|*.json`; `tests/test_chain.py`; `docs/M23A_CHAIN_LAB_VALIDATION.md`.

**Tests:** `pytest tests/test_chain.py -v` (10 passed).

**Note:** The repo also contains a richer **chain_lab** package (`chain_lab/definition.py`, `runner.py`, `manifest.py`, `compare.py`, `report.py`, `config.py`) and additional CLI (e.g. chain define, report, compare, list-runs, artifact-tree), plus docs: `M23A_CHAIN_LAB_READ_FIRST.md`, `M23A_CHAIN_LAB_REUSE_MAP.md`, `M23A_CHAIN_LAB_SAMPLES.md`, `M23A_CHAIN_LAB_SUMMARY.md`, `M23A_F2_READ_FIRST.md`. These indicate concurrent or follow-up work in other chats.

---

### 2.6 M23B — Edge / Hardware Readiness Layer

**Objective:** Narrow edge-readiness layer: make runtime/dependency assumptions explicit, validate local deployment requirements, define a reproducible local deployment profile, package product state/config for edge-style deployment testing.

**What was built:**

- **Edge profile** (`edge/profile.py`): `build_edge_profile(repo_root, config_path)` returns: repo_root, config_path, config_exists, runtime_requirements (python_version_min/recommended/current, no_cloud_required), storage_assumptions (sandbox paths, writable_required), model_assumptions (local_llm_optional, llm_config_path, adapter_runs_dir, corpus_path), sandbox_path_assumptions (paths list), supported_workflows. Uses `SANDBOX_PATHS` and `SUPPORTED_WORKFLOWS`.
- **Readiness checks** (`edge/checks.py`): `run_readiness_checks(repo_root, config_path)` returns list of { check_id, passed, message, optional }. Checks: python_version, config_exists, sandbox path existence for core paths, llm_config (optional). `checks_summary(checks)` returns passed/failed/failed_required/optional_disabled/ready.
- **Reports** (`edge/report.py`): `generate_edge_readiness_report` (full markdown: summary, runtime, sandbox paths, checks, supported workflows); `generate_missing_dependency_report` (required vs optional missing); `generate_workflow_matrix_report` (workflow, description, required/optional; markdown or JSON); `generate_package_report` (package config, workflow availability, local model/runtime deps, readiness).
- **CLI:** `workflow-dataset edge readiness [--output PATH]`; `edge profile`; `edge report`; `edge missing-deps`; `edge workflow-matrix [--format json]`; `edge package-report`.

**Files:** `edge/__init__.py`, `edge/profile.py`, `edge/checks.py`, `edge/report.py`; `cli.py`; `tests/test_edge.py`; `docs/M23B_EDGE_READINESS_VALIDATION.md`. Repo also has `edge/package_report.py`, `edge/tiers.py` and CLI commands `edge matrix`, `edge compare`, suggesting concurrent work.

**Tests:** `pytest tests/test_edge.py -v` (8 passed).

---

## 3. What was built concurrently (in different chats)

Evidence of concurrent or follow-up work across chats comes from **multiple docs and code paths** for the same theme:

- **M22E (Templates / Composer):**  
  - Core: `M22E_TEMPLATES_VALIDATION.md`, `templates/registry.py`, CLI templates list/show, release demo --template.  
  - Concurrent/extension: `M22E_WORKFLOW_COMPOSER_READ_FIRST.md`, `M22E_F2_DELIVERY.md`, `M22E_F2_TEMPLATE_VERSIONING_READ_FIRST.md`, and likely `templates/validation.py`, CLI `templates validate`, `templates report`.

- **M23A (Chain lab):**  
  - Core: `chain/` (registry, runner), CLI chain list/run/status, `M23A_CHAIN_LAB_VALIDATION.md`.  
  - Concurrent/richer: `chain_lab/` (definition, runner, manifest, compare, report, config), `M23A_CHAIN_LAB_READ_FIRST.md`, `M23A_CHAIN_LAB_REUSE_MAP.md`, `M23A_CHAIN_LAB_SAMPLES.md`, `M23A_CHAIN_LAB_SUMMARY.md`, `M23A_F2_READ_FIRST.md`, and CLI chain define, report, compare, list-runs, artifact-tree.

- **M23B (Edge):**  
  - Core: `edge/profile.py`, `edge/checks.py`, `edge/report.py`, readiness/report/missing-deps/workflow-matrix/package-report.  
  - Concurrent: `edge/package_report.py`, `edge/tiers.py`, and CLI `edge matrix`, `edge compare` (tier compare).

- **Other batches (docs only, no separate validation in this list):**  
  - A3 (workspace rerun/diff/timeline), A4 (export contracts), C3 (cohort alert strip), C4 (dashboard action macros), D3 (proposal generator), M21W (devlab runbook), EVAL_OPERATOR_RUNBOOK, WORKSPACE_OPS_REPORTING_IMPLEMENTATION_SUMMARY.

This report does **not** have access to other chat transcripts; the above is inferred from repo file names, timestamps, and content. For a full list of “which chat did what,” you would need to inspect the **agent-transcripts** folder (per-session logs) or version history.

---

## 4. Achievements so far (consolidated)

- **Single CLI entry point:** `workflow-dataset` with many subcommands (dashboard, setup, assist, llm, trials, trial, release, pilot, review, edge, templates, intake, chain, mission-control, etc.).
- **Validated ops/reporting workflows:** Five workflow types with artifacts saved under `data/local/workspaces/<workflow>/`; review state and packages under `data/local/review` and `data/local/packages`.
- **Pilot and cohort:** Session start/end, feedback capture, aggregation, graduation check, cohort status/report (M21O, M21P, M21Q).
- **Unified mission control:** One read-only dashboard of product, evaluation, development, and incubator state plus a recommended next action (build/benchmark/cohort_test/promote/hold/rollback).
- **Role-based review lanes:** Workspaces and packages can be tagged by lane (operator, reviewer, stakeholder-prep, approver); lane-status, assign-lane, list-lane; no cloud.
- **Local knowledge intake:** User-owned paths registered and snapshotted into `data/local/intake/`; release demo can use `--intake <label>` for task context; provenance in manifest.
- **Workflow composition:** Templates define workflow_id and ordered artifacts; release demo `--template` saves only those artifacts in that order; template_id in manifest.
- **Internal chain lab:** Operator-started chains (list/run/status); steps run via workflow-dataset CLI; outputs and run report under `data/local/chains/runs/`; no uncontrolled looping.
- **Edge readiness:** Explicit profile (runtime, storage, model, sandbox paths), readiness checks, full readiness report, missing-dependency report, supported-workflow matrix, package report; all under `data/local/edge/`.
- **Documentation:** Pilot operator guide, devlab runbook, eval runbook, workspace/export/cohort/dashboard docs, and validation/read-first docs for M22B–M23B.

---

## 5. Prompts used so far (all chats)

**Limitation:** This agent only sees the **current conversation**. It does not have access to other chat sessions or to the full agent-transcripts directory. What follows is:

1. **Task prompts from this conversation** (the ones that led to the work summarized above).  
2. **A short note on how to get a full prompt inventory** across all chats.

### 5.1 Task prompts in this conversation

The user issued the following **task briefs** in this chat (paraphrased; exact wording may vary):

1. **M22B — Local Agent Product Foundry / Mission Control**  
   - Unify internal development surfaces into one local mission-control layer.  
   - Show product state, benchmark state, pilot/cohort state, proposal/experiment state, incubator state, and recommended next move.  
   - Include: product state summary, evaluation state, development state, workflow incubator state, next-action engine (build, benchmark, cohort-test, promote, hold, rollback).  
   - Surface: e.g. `workflow-dataset mission-control` or a section in the existing console/dashboard.  
   - Constraints: no end-user orchestration, no cloud, no auto-merge, no weakening of local-first/operator-controlled.

2. **M22C — Team Pilot Workspace + Role-Based Review Lanes**  
   - Build local-first team pilot workspace model with role-based review lanes.  
   - Lanes: operator, reviewer, stakeholder-prep, approver.  
   - Support: lane metadata on workspaces/packages, lane-specific queue views, lane-aware package flow, local reports (lane summary, pending by lane).  
   - Surface: e.g. `review lane-status`, `review assign-lane --workspace ... --lane ...`, `review list-lane --lane ...`.  
   - Constraints: no cloud collaboration, no broadening scope, preserve sandbox-only safety.

3. **M22D — Local Knowledge Intake Center for User-Owned Inputs**  
   - Local-first intake: accept user-owned local files/folders, snapshot into sandbox, parse structure, make available to workflows, preserve provenance.  
   - Build: intake registration (register paths, label, classify by type), intake snapshotting (copy/record into sandbox, never mutate originals), intake reports (file inventory, parse summary, workflow associations), workflow compatibility (named intake sets for release demo).  
   - Surface: e.g. `intake add --path ./notes --label sprint_notes`, `intake report --label sprint_notes`, `release demo ... --intake sprint_notes --save-artifact`.  
   - Constraints: no cloud, no silent watch, no auto-ingest.

4. **M22E — Workflow Composer + Template Studio**  
   - Local-first template/composer for ops/reporting: reusable workflow templates, control artifact set and ordering, stay within validated workflows.  
   - Build: template format (workflow id, input expectations, artifacts, ordering, optional wording/style), template registry (list, show, run template), composer behavior (combine artifacts into suite definitions), template-based saving.  
   - Surface: e.g. `templates list`, `templates show --id ops_reporting_core`, `release demo --template ops_reporting_core --save-artifact`.  
   - Constraints: no auto-apply code/files, no broadening to other workflow families, no uncontrolled chains.

5. **M23A — Internal Agent Chain Lab (Operator-Controlled)**  
   - Local operator-controlled chain runner: define small step sequences, run locally, persist step outputs, compare chain variants, operator-started and stoppable.  
   - Build: chain definition (id, ordered steps, expected artifacts, stop conditions), chain runner (run one chain, inspect outputs per step, stop/cancel), chain reports (step outputs, failures, final artifacts, operator notes).  
   - Surface: e.g. `chain list`, `chain run --id ops_reporting_chain_v1`, `chain status --run latest`.  
   - Constraints: no end-user orchestration, no uncontrolled looping, no auto-apply outside sandbox.

6. **M23B — Edge / Hardware Readiness Layer**  
   - Local deployment/readiness layer for future appliance/edge packaging.  
   - Build: edge profile (runtime, storage, model, sandbox assumptions), readiness checks (constrained machine, workflows vs components, optional features when unavailable), edge packaging metadata (package configs, workflow availability, local model/runtime deps), operator output (readiness report, missing-dependency report, supported-workflow matrix).  
   - Surface: e.g. `edge readiness`, `edge profile`, `edge package-report`.  
   - Constraints: no full hardware device design, no cloud-first assumptions, no weakening of local-first/privacy-first.

7. **Current request (this turn):**  
   - Produce a **detailed** markdown report (not a summary) of what was built so far, what was built concurrently in different chats, what is achieved, and **which all prompts are used so far in all chats**.  
   - Output: extensive markdown file.

### 5.2 How to get a full prompt inventory across all chats

- **Agent transcripts** are stored under the project’s agent-transcripts directory (e.g. `.../agent-transcripts/`). Each session may have a transcript file (e.g. UUID-based).  
- To list **all prompts used in all chats**, you would need to:  
  - Enumerate those transcript files, and  
  - Parse or search them for user messages (the “prompts” to the agent).  
- This report cannot do that enumeration itself; it can only report the **prompts visible in this conversation** (the seven items above).

---

## 6. File and command reference (quick index)

### 6.1 New or heavily modified modules (by deliverable)

| Deliverable | Modules / paths |
|-------------|------------------|
| M22B | `mission_control/__init__.py`, `state.py`, `next_action.py`, `report.py` |
| M22C | `release/review_state.py` (lane), `release/lane_views.py`, `release/package_builder.py` (lane in manifest) |
| M22D | `intake/__init__.py`, `registry.py`, `load.py`, `report.py`; `release/workspace_rerun_diff.py` (intake in rerun) |
| M22E | `templates/__init__.py`, `templates/registry.py`; `data/local/templates/*.yaml` |
| M23A | `chain/__init__.py`, `chain/registry.py`, `chain/runner.py`; `data/local/chains/*.yaml|*.json`; optionally `chain_lab/*` |
| M23B | `edge/__init__.py`, `edge/profile.py`, `edge/checks.py`, `edge/report.py`; optionally `edge/package_report.py`, `edge/tiers.py` |

### 6.2 CLI groups and selected commands

| Group | Selected commands |
|-------|--------------------|
| **app** | `console`, `build`, `qa`, `observe`, `mission-control` |
| **dashboard** | `dashboard`, `workspace`, `package`, `cohort`, `apply-plan`, `action` |
| **setup** | `init`, `run`, `status`, `summary`, `build-corpus`, `build-sft`, `build-personal-corpus` |
| **assist** | `suggest`, `draft`, `explain`, `next-step`, `refine-draft`, `chat`, `materialize`, `preview`, `apply-plan`, `apply`, `rollback`, `apply-preview`, `generate-*`, `bundle-*`, etc. |
| **llm** | `verify`, `prepare-corpus`, `build-sft`, `train`, `smoke-train`, `eval`, `compare-runs`, `demo`, `demo-suite`, `latest-run`, `latest-adapter` |
| **trials / trial** | `list`, `run`, `run-suite`, `compare`, `report`; `start`, `tasks`, `record-feedback`, `summary`, `aggregate-feedback` |
| **release** | `verify`, `run`, `demo` (--workflow, --context-file, --input-pack, --intake, --template, --save-artifact, --rerun-from), `package`, `report` |
| **pilot** | `start-session`, `verify`, `status`, `capture-feedback`, `end-session`, `aggregate`, `latest-report`, `graduation-status`, `cohort-status`, `cohort-report`, etc. |
| **review** | `list-workspaces`, `show-workspace`, `diff-workspaces`, `workspace-timeline`, `validate-workspace`, `export-contract`, `approve-artifact`, `set-artifact-state`, `build-package`, `metrics`, `list-profiles`, `package-status`, **lane-status**, **assign-lane**, **list-lane**, `queue-status`, `stage-package`, `stage-artifact`, `staging-board`, `unstage`, `clear-staging`, `build-apply-plan`, `apply-plan-status` |
| **edge** | **readiness**, **report**, **missing-deps**, **workflow-matrix**, **profile**, **package-report**; optionally matrix, compare |
| **templates** | **list**, **show**; optionally validate, report |
| **intake** | **add**, **list**, **report** |
| **chain** | **list**, **run**, **status**; optionally define, report, compare, list-runs, artifact-tree |

### 6.3 Documentation files (existing)

- **Operator / runbooks:** `PILOT_OPERATOR_GUIDE.md`, `DEVLAB_OPERATOR_RUNBOOK.md`, `EVAL_OPERATOR_RUNBOOK.md`
- **Validation / delivery:** `MISSION_CONTROL_VALIDATION.md`, `M22C_REVIEW_LANES_VALIDATION.md`, `M22D_INTAKE_VALIDATION.md`, `M22E_TEMPLATES_VALIDATION.md`, `M23A_CHAIN_LAB_VALIDATION.md`, `M23B_EDGE_READINESS_VALIDATION.md`
- **Read-first / design:** `M22E_WORKFLOW_COMPOSER_READ_FIRST.md`, `M22E_F2_TEMPLATE_VERSIONING_READ_FIRST.md`, `M23A_CHAIN_LAB_READ_FIRST.md`, `M23A_F2_READ_FIRST.md`, `M23B_EDGE_READINESS.md`
- **Other:** `A3_WORKSPACE_RERUN_DIFF_TIMELINE.md`, `A4_WORKSPACE_EXPORT_CONTRACTS.md`, `C3_COHORT_ALERT_STRIP.md`, `C4_DASHBOARD_ACTION_MACROS.md`, `D3_PROPOSAL_GENERATOR_DELIVERY.md`, `M22E_F2_DELIVERY.md`, `M23A_CHAIN_LAB*.md`, `WORKSPACE_OPS_REPORTING_IMPLEMENTATION_SUMMARY.md`

---

## 7. Test summary

| Test file | Scope | Typical count |
|-----------|--------|----------------|
| `test_mission_control.py` | M22B state, next_action, report | 4 |
| `test_review_lanes.py` | M22C lanes, set_workspace_lane, set_package_lane, get_lane_summary, list_* | 9 |
| `test_intake.py` | M22D add, list, get, load_intake_content, intake_report, format | 7 |
| `test_templates.py` | M22E load, list, get, template_artifact_order | 9 |
| `test_chain.py` | M23A load, list, run_chain, get_run_status, list_runs | 10 |
| `test_edge.py` | M23B profile, checks, readiness report, missing-deps, workflow matrix, package report | 8 |

Run all: `PYTHONPATH=src python3 -m pytest tests/test_mission_control.py tests/test_review_lanes.py tests/test_intake.py tests/test_templates.py tests/test_chain.py tests/test_edge.py -v`

---

*End of detailed build report. For prompts used in other chats, see agent-transcripts or version history.*
