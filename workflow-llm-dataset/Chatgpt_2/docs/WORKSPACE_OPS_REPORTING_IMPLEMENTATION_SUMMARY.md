# Workspace & Ops Reporting — Implementation Summary (Recent Multi-Chats)

**Single entry point** for everything implemented in recent multi-chats: M21S (ops reporting workspace v2), A2 (input packs + schema hardening), A3 (rerun/diff/timeline), A4 (export contracts + handoff spec). This doc organizes **what** was built, **where** it lives, **how** it works, and **how much** is in scope. All of it is **local-only**, **sandbox-only**, and within the **ops/reporting** family.

---

## Table of contents

1. [Overview: What has actually been built](#1-overview-what-has-actually-been-built)
2. [Where everything lives](#2-where-everything-lives)
3. [How it works (end-to-end)](#3-how-it-works-end-to-end)
4. [How much: scope and limits](#4-how-much-scope-and-limits)
5. [Quick reference: CLI and paths](#5-quick-reference-cli-and-paths)
6. [Tests to run](#6-tests-to-run)

---

## 1. Overview: What Has Actually Been Built

| Milestone | What | Scope |
|-----------|------|--------|
| **M21S** | One coherent **ops reporting workspace** per run: single sandbox dir with manifest + source snapshot + 5 artifact .md files. | 6-prompt workflow, shared workspace save, reuse map, operator output. |
| **A2** | **Input packs** (named file sets or dir snapshots) + **artifact schema** (standard sections, source_snapshot template, validation). | `--input-pack`, manifest `input_sources_used` / `retrieval_relevance_weak_or_mixed`, schema hardening. |
| **A3** | **Rerun** from existing workspace, **diff** two runs, **provenance timeline**. | `--rerun-from`, `review diff-workspaces`, `review workspace-timeline`; no mutation of old workspaces. |
| **A4** | **Export contracts** + **downstream handoff spec**: schema version, required/optional files, manifest compatibility checks. | `review validate-workspace`, `review export-contract`; contracts per workflow. |

**Constraints (unchanged):** No cloud/network, no auto-apply, no scope beyond ops/reporting, backward compatibility for existing workflows (weekly_status, status_action_bundle, stakeholder_update_bundle, meeting_brief_bundle).

---

## 2. Where Everything Lives

### 2.1 New or heavily modified modules (`src/workflow_dataset/release/`)

| File | Purpose |
|------|--------|
| `workspace_save.py` | M21S. Shared save: `save_ops_reporting_workspace(artifacts, manifest_dict, pilot_dir, repo_root)` → writes `data/local/workspaces/ops_reporting_workspace/{ts}_{id}/` with artifact .md files + `workspace_manifest.json`, then `record_workflow_artifact`. |
| `input_packs.py` | A2. `load_input_pack(pack_name, repo_root)` → (content, source_descriptions). Packs under `data/local/input_packs/<name>.json` (manifest with `paths`, optional `root`) or `data/local/input_packs/<name>/` (directory snapshot of .md/.txt). `list_input_packs()`. |
| `artifact_schema.py` | A2. Expected sections per artifact; `build_source_snapshot_md(...)`; `validate_workspace_artifacts(artifacts)`; `validate_artifact_schema(content, artifact_name)`. |
| `workspace_rerun_diff.py` | A3. `infer_rerun_args(manifest)`; `diff_workspaces(path_a, path_b, include_artifact_diffs, max_diff_lines)`; `workspace_timeline(root, workflow, limit)`. |
| `workspace_export_contract.py` | A4. `WORKSPACE_EXPORT_SCHEMA_VERSION = "1.0"`; `EXPORT_CONTRACTS` per workflow; `get_export_contract(workflow)`; `validate_workspace_export(workspace_path)`. |

### 2.2 Existing modules used as-is or lightly touched

| File | Role |
|------|------|
| `reporting_workspaces.py` | Discovery: `get_workspace_inventory`, `list_reporting_workspaces`; loads `workspace_manifest.json` or `manifest.json`. M21S/A3/A4 rely on it. |
| `workspace_save.py` | Only writer for ops_reporting_workspace dirs; manifest dict is passed through (A2/A4 keys included by CLI). |
| `package_builder.py` | Consumes workspaces via `get_workspace_inventory`; can use A4 `validate_workspace_export` before building. |
| `review_state.py` | Per-artifact state (approved/needs_revision/excluded); unchanged by M21S/A2/A3/A4. |

### 2.3 CLI (`src/workflow_dataset/cli.py`)

**Release group (release demo):**

- `release demo` — `--workflow ops_reporting_workspace` (M21S), `--context-file`, `--context-text`, `--input-pack` (A2), `--rerun-from` (A3), `--save-artifact`. For ops_reporting_workspace: 6 prompts, then save via `workspace_save.save_ops_reporting_workspace` with manifest including `input_sources_used`, `retrieval_relevance_weak_or_mixed`, `schema_validation` (A2).

**Review group (workspace/review):**

- `review list-workspaces` — list recent reporting workspaces (includes ops_reporting_workspace runs).
- `review show-workspace <path>` — inventory + review state.
- `review diff-workspaces <path_a> <path_b>` — A3: inventory diff, manifest metadata diff, artifact deltas (optional `--no-diffs`).
- `review workspace-timeline` — A3: provenance timeline (optional `--workflow`, `--limit`).
- `review validate-workspace <path>` — A4: validate against export contract (exit 1 if invalid).
- `review export-contract` — A4: print contract for a workflow (default `ops_reporting_workspace`).
- `review approve-artifact`, `review set-artifact-state`, `review build-package`, etc. — unchanged in scope by M21S/A2/A3/A4.

### 2.4 Docs

| Doc | Content |
|-----|--------|
| `M21S_OPS_REPORTING_WORKSPACE_PLAN.md` | Plan: repo state, reuse, gap, steps. |
| `M21S_REUSE_MAP.md` | Reuse map: task context, retrieval, prompts, save pattern, pilot; workspace-specific layer. |
| `M21S_DELIVERY_OPS_REPORTING_WORKSPACE.md` | M21S delivery: files, CLI, sample tree/manifest/artifacts, tests. |
| `A2_OPS_REPORTING_INPUT_PACKS_AND_SCHEMA.md` | A2: input packs, schema, manifest, CLI, tests. |
| `A3_WORKSPACE_RERUN_DIFF_TIMELINE.md` | A3: rerun, diff, timeline, CLI, sample diff, tests. |
| `A4_WORKSPACE_EXPORT_CONTRACTS.md` | A4: export contract, validate/export-contract CLI, sample contract/manifest, tests, downstream handoff. |
| `FOUNDER_DEMO_FLOW.md` | Includes ops_reporting_workspace in workflow list and output location. |
| `BROADER_PILOT_RUNBOOK.md` | Workflow list and artifact path row for ops_reporting_workspace. |
| `PILOT_OPERATOR_GUIDE.md` | Output location and run flow include ops_reporting_workspace and new review commands. |
| `M21_PILOT_EXECUTION.md` | Workflow list and artifact table row for ops_reporting_workspace. |

### 2.5 Tests (`tests/test_release.py`)

- M21S: `test_ops_reporting_workspace_artifact_sandbox_format`, `test_save_ops_reporting_workspace_writes_sandbox`.
- A2: `test_load_input_pack_directory_snapshot`, `test_load_input_pack_with_manifest`, `test_build_source_snapshot_md`, `test_ops_reporting_workspace_manifest_includes_input_sources`; demo help asserts `--input-pack`.
- A3: `test_infer_rerun_args`, `test_diff_workspaces`, `test_workspace_timeline`.
- A4: `test_get_export_contract`, `test_validate_workspace_export_valid`, `test_validate_workspace_export_missing_required`, `test_validate_workspace_export_missing_manifest_key`, `test_review_validate_workspace_cli`.

---

## 3. How It Works (End-to-End)

### 3.1 Generating one ops reporting workspace (M21S + A2)

1. Operator runs:  
   `workflow-dataset release demo --workflow ops_reporting_workspace [--context-file ...] [--context-text ...] [--input-pack ...] [--retrieval] --save-artifact`
2. CLI loads task context (`_load_task_context`) and, if `--input-pack` is set, loads pack via `input_packs.load_input_pack` and merges into `task_context`; builds `input_sources_used` (context_file, context_text, pack sources).
3. Six prompts run (general, weekly_status, status_brief, action_register, stakeholder_update, decision_requests) with existing OPS_* instructions and weak-context honesty labels.
4. Outputs are collected; `build_source_snapshot_md` (A2) builds standardized `source_snapshot.md` from `input_sources_used`, grounding, retrieval relevance, and artifact list.
5. Manifest is built with `workflow`, `timestamp`, `grounding`, `input_sources_used`, `artifact_list`, `retrieval_used`, `retrieval_relevance_weak_or_mixed`, `schema_validation`, etc.
6. `save_ops_reporting_workspace(artifacts_dict, ws_manifest, pilot_dir)` writes only non-empty artifacts and `workspace_manifest.json` under `data/local/workspaces/ops_reporting_workspace/{YYYY-MM-DD_HHMM}_{8-char-id}/`, then `record_workflow_artifact("ops_reporting_workspace", dir_path)`.
7. CLI prints the saved path, lists files, and preview hint (“Which sources fed this run: see source_snapshot.md”).

### 3.2 Rerun (A3)

1. Operator runs:  
   `workflow-dataset release demo --rerun-from <workspace_path>`
2. CLI resolves path (`_resolve_workspace_arg`), loads `get_workspace_inventory(ws)`, then `infer_rerun_args(manifest)` to get `context_file`, `input_pack`, `retrieval`, `workflow`.
3. These override the demo options; `save_artifact` is set to True. The same flow as above runs and writes a **new** run dir; the original workspace is never modified.

### 3.3 Diff and timeline (A3)

- **Diff:** `review diff-workspaces <path_a> <path_b>` calls `diff_workspaces(pa, pb)`: compares artifact inventory (only_in_a, only_in_b, common), manifest metadata (workflow, timestamp, grounding, retrieval_used, etc.), and optional per-artifact unified diffs (unless `--no-diffs`).
- **Timeline:** `review workspace-timeline` calls `workspace_timeline(root, workflow, limit)`: lists runs newest first with timestamp, run_id, grounding, artifact_count (and path).

### 3.4 Export contract and validation (A4)

- **Contract:** Each workflow has an entry in `EXPORT_CONTRACTS`: `manifest_file`, `required_manifest_keys`, `required_files`, `optional_files`, and optionally `required_at_least_one_of`.
- **Validate:** `review validate-workspace <path>` runs `validate_workspace_export(ws)`: checks manifest exists, infers workflow, ensures required manifest keys and required files exist, and (for some workflows) “at least one of” optional files; returns `valid`, `errors`, `warnings`, `manifest_compatible`, `missing_required`, `missing_manifest_keys`.
- **Export contract:** `review export-contract [--workflow ...]` prints the contract for that workflow (schema version, required/optional files, manifest keys).

---

## 4. How Much: Scope and Limits

- **Workflows:** One new workflow type, `ops_reporting_workspace`, plus existing `weekly_status`, `status_action_bundle`, `stakeholder_update_bundle`, `meeting_brief_bundle`. All share the same release demo entrypoint and grounding (context + optional retrieval).
- **Artifacts per ops_reporting_workspace run:** Up to 7 files: `workspace_manifest.json`, `source_snapshot.md`, `weekly_status.md`, `status_brief.md`, `action_register.md`, `stakeholder_update.md`, `decision_requests.md`. Only non-empty outputs are written; `saved_artifact_paths` in the manifest lists exactly what was written.
- **Input packs:** Single pack per run (`--input-pack <name>`). Pack = either a JSON manifest at `data/local/input_packs/<name>.json` or a directory `data/local/input_packs/<name>/` (all .md/.txt). Content is capped (e.g. 8000 chars in current impl).
- **Rerun:** Reuses only what is stored in the manifest (`input_sources_used`, `retrieval_used`, `workflow`). Inline `--context-text` is not stored, so rerun does not replay it.
- **Diff:** Compares two workspace dirs; artifact deltas are unified diffs (with a max line limit per artifact). Read-only; no mutation.
- **Export contract:** Schema version is `1.0`. Contracts are defined for `ops_reporting_workspace`, `weekly_status`, `status_action_bundle`, `stakeholder_update_bundle`, `meeting_brief_bundle`. Downstream can depend on required/optional files and manifest keys; validation is read-only.

**Out of scope (by design):** Multiple context files in one run, cloud/network, auto-apply, changes outside `data/local/*`, non-ops workflows, multi-agent or external orchestration.

---

## 5. Quick reference: CLI and paths

| Action | Command |
|--------|--------|
| Generate workspace | `workflow-dataset release demo --workflow ops_reporting_workspace [--context-file F] [--context-text T] [--input-pack P] [--retrieval] --save-artifact` |
| Rerun from existing | `workflow-dataset release demo --rerun-from <path>` |
| List workspaces | `workflow-dataset review list-workspaces` |
| Show one workspace | `workflow-dataset review show-workspace <path>` |
| Diff two runs | `workflow-dataset review diff-workspaces <path_a> <path_b>` |
| Provenance timeline | `workflow-dataset review workspace-timeline [--workflow ops_reporting_workspace] [--limit 20]` |
| Validate export contract | `workflow-dataset review validate-workspace <path>` |
| Print contract | `workflow-dataset review export-contract [--workflow ops_reporting_workspace]` |

**Important paths:**

- Workspaces: `data/local/workspaces/ops_reporting_workspace/{YYYY-MM-DD_HHMM}_{id}/`
- Input packs: `data/local/input_packs/<name>/` or `data/local/input_packs/<name>.json`
- Pilot/session: `data/local/pilot` (e.g. `record_workflow_artifact`)

---

## 6. Tests to run

From repo root (with venv that has dependencies, e.g. pyyaml):

```bash
cd workflow-llm-dataset
python -m pytest tests/test_release.py -v --tb=short
```

To run only the workspace/ops-reporting–related tests:

```bash
python -m pytest tests/test_release.py -v --tb=short -k "ops_reporting_workspace or input_pack or source_snapshot or diff_workspaces or workspace_timeline or infer_rerun or export_contract or validate_workspace_export or review_validate"
```

---

This summary reflects the implementation state as built across the recent multi-chats (M21S, A2, A3, A4). For per-milestone detail, see the delivery/plan docs listed in §2.4.
