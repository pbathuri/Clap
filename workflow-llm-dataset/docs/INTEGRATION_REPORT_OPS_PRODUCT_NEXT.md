# Integration Report — feat/ops-product-next-integration

**Date:** 2026-03-15  
**Target branch:** `feat/ops-product-next-integration`  
**Repo:** Clap (workflow-llm-dataset in subfolder)

---

## 1. Merge order executed

**No merges were executed.** The five pane branches are **not present** in the repository:

| Branch | Status |
|--------|--------|
| `feat/m22e-workflow-composer` | Does not exist (local or remote) |
| `feat/m21t-operator-surface` | Does not exist |
| `feat/m21w-devflywheel` | Does not exist |
| `feat/m23a-chain-lab` | Does not exist |
| `feat/m23b-edge-readiness` | Does not exist |

**Actions taken:**

- Confirmed only `main` and `remotes/origin/main` exist (`git branch -a` after `git fetch origin`).
- Created **`feat/ops-product-next-integration`** from current `main` so the integration branch exists for when the pane branches are available.
- Ran the requested test suite (and a subset that does not require full app deps) on the current tree — see §4.

**Intended merge order** (when branches exist):

1. `feat/m22e-workflow-composer`
2. `feat/m21t-operator-surface`
3. `feat/m21w-devflywheel`
4. `feat/m23a-chain-lab`
5. `feat/m23b-edge-readiness`

---

## 2. Conflicts encountered

**None** — no merges were performed.

---

## 3. How each conflict was resolved

N/A.

---

## 4. Tests run after each merge

Because no merges were done, tests were run **once** on the current state of `feat/ops-product-next-integration` (same as `main` plus any uncommitted changes in the working tree).

**Full requested suite** (requires project venv with pydantic, typer, etc.):

```bash
cd workflow-llm-dataset && PYTHONPATH=src pytest -q \
  tests/test_release.py \
  tests/test_console_cli.py \
  tests/test_pilot.py \
  tests/test_templates.py \
  tests/test_chain_lab.py \
  tests/test_edge.py \
  tests/test_ui_services.py \
  tests/test_ui_state_store.py
```

**Result:** Collection failed before any test ran: `ModuleNotFoundError: No module named 'pydantic'` when importing `workflow_dataset.cli` / `workflow_dataset.settings`. So the full suite **was not run** in this environment.

**Subset run** (tests that do not require importing the full CLI app):

```bash
cd workflow-llm-dataset && PYTHONPATH=src python3 -m pytest -q \
  tests/test_templates.py tests/test_chain_lab.py tests/test_edge.py
```

**Result:**

- **70 passed**
- **5 failed** — all due to missing `pydantic` when tests tried to import `workflow_dataset.cli` (CLI help tests in test_templates and test_chain_lab).

So:

- **Unit / library tests** for templates, chain_lab, and edge: **70 passed**.
- **CLI-facing tests** that import the app: **not run** (or fail in env without pydantic).

**Note:** The task referenced `tests/test_chain.py`; the repo has **`tests/test_chain_lab.py`** (no `test_chain.py`). The suite was run with `test_chain_lab.py`.

**Recommendation:** In CI or a full dev environment, install project dependencies (e.g. `pip install -e .` or use project venv) and run the full suite above plus, if present, `tests/test_devlab.py` and `tests/test_eval.py`.

---

## 5. Final integrated command surface summary

The following reflects the **current codebase** (build report + `cli.py` and related docs). No integration merge changed it.

**Top-level / console**

- `workflow-dataset console` — Launch operator console.
- `workflow-dataset build` / `qa` / `observe` — Build/QA/observe.
- `workflow-dataset mission-control` — Mission control report (M22B).

**Dashboard**

- `dashboard`, `dashboard workspace`, `dashboard package`, `dashboard cohort`, `dashboard apply-plan`, `dashboard action` — Command center and drill-downs (M21U, C2, C4).

**Setup**

- `setup init`, `run`, `status`, `summary`, `build-corpus`, `build-sft`, `build-personal-corpus`, etc.

**Assist / LLM / trials**

- `assist suggest`, `draft`, `explain`, `next-step`, `refine-draft`, `chat`, `materialize`, `preview`, `apply-plan`, `apply`, `rollback`, etc.
- `llm verify`, `prepare-corpus`, `build-sft`, `train`, `smoke-train`, `eval`, `compare-runs`, `demo`, `demo-suite`, `latest-run`, `latest-adapter`.
- `trials list`, `run`, `run-suite`, `compare`, `report`; `trial start`, `tasks`, `record-feedback`, `summary`, `aggregate-feedback`.

**Release**

- `release verify`, `run`, `demo` (--workflow, --template, --intake, --param, --save-artifact, --rerun-from), `package`, `report`.

**Pilot**

- `pilot start-session`, `verify`, `status`, `capture-feedback`, `end-session`, `aggregate`, `latest-report`, `graduation-status`, `cohort-status`, `cohort-report`, etc.

**Review**

- `review list-workspaces`, `show-workspace`, `diff-workspaces`, `workspace-timeline`, `validate-workspace`, `export-contract`, `approve-artifact`, `set-artifact-state`, `build-package`, `metrics`, `list-profiles`, `package-status`, `lane-status`, `assign-lane`, `list-lane`, `queue-status`, `stage-package`, `staging-board`, `build-apply-plan`, `apply-plan-status`, etc.

**Edge**

- `edge readiness`, `report`, `missing-deps`, `workflow-matrix`, `profile`, `package-report`, `matrix`, `compare`.

**Templates (M22E)**

- `templates list` (--show-status), `show`, `validate`, `report`, `export`, `import`, `test`.

**Intake (M22D)**

- `intake add`, `list`, `report`.

**Chain (M23A / chain lab)**

- `chain list`, `define`, `run`, `report`, `compare`, `list-runs`, `artifact-tree`, etc.

All of the above are **local-first**, **sandbox-only**, and **operator-controlled** (no silent apply, no cloud-only paths).

---

## 6. Remaining integration risks

1. **Pane branches missing**  
   Until `feat/m22e-workflow-composer`, `feat/m21t-operator-surface`, `feat/m21w-devflywheel`, `feat/m23a-chain-lab`, and `feat/m23b-edge-readiness` exist (pushed to this repo or available locally), the specified merge order cannot be run. Risk: integration is blocked until those branches are created or the work is re-applied as branches.

2. **Uncommitted work on main**  
   There are many modified and untracked files under `workflow-llm-dataset/` (templates, chain_lab, edge, pilot, release, docs, tests). If that work is the “pane” work, it has not been committed. Risk: merging future branches may conflict with this uncommitted state, or the work may be lost if branches are created from an older main.

3. **Test environment**  
   The full requested test suite depends on project dependencies (pydantic, typer, etc.). In a minimal or different env, CLI-based tests fail at import. Risk: integration “pass” might be environment-dependent unless CI uses the project venv/requirements.

4. **Conflict hotspots when branches exist**  
   When merges are actually run, likely collision points are:
   - **`src/workflow_dataset/cli.py`** — All panes add or touch commands; merge order helps but conflicts are still likely.
   - **Shared manifest / provenance** — e.g. `workspace_manifest.json`, `artifact_list`, `template_id`, release/review state.
   - **Workspace/package paths** — `data/local/workspaces`, `data/local/packages`, `data/local/templates`, etc.
   - **Runtime/config** — `configs/settings.yaml`, LLM/config paths.
   - **Test files** — `test_release.py`, `test_templates.py`, `test_chain_lab.py`, `test_edge.py`, `test_pilot.py`, etc.

5. **Naming**  
   Task referred to `test_chain.py`; repo has `test_chain_lab.py`. Ensure scripts/CI use the actual filename.

---

## 7. Recommendation for the next product-development batch

1. **Create or obtain the five pane branches**  
   - Either create branches from existing commits (if pane work was committed in logical chunks) or recreate branches from patch sets / other repos.  
   - Push them to the Clap remote (or make them available locally) so that `feat/ops-product-next-integration` can be updated by merging in the specified order.

2. **Stabilize the integration branch**  
   - Decide whether current uncommitted changes under `workflow-llm-dataset/` should be committed on `main` or on a separate branch that is then merged into `feat/ops-product-next-integration` (or used to create the pane branches).  
   - Avoid leaving large uncommitted chunks that could conflict with branch merges.

3. **Run the full test suite in a full env**  
   - Use the project venv (or `pip install -e .`) and run the full requested suite (including `test_devlab.py` and `test_eval.py` if present) after each merge and once at the end.  
   - Document the exact command and environment in CI so “integration pass” is reproducible.

4. **Conflict resolution rules (for when merges run)**  
   - Prefer **stable interfaces** (e.g. manifest keys, CLI group names) first.  
   - Then **safety boundaries** (sandbox-only, no silent apply).  
   - Then **UX consistency** (help text, command names).  
   - Do **not** drop another pane’s functionality to resolve a conflict; add a small reconciliation commit on the integration branch if needed.

5. **Optional: single integration commit**  
   - If the pane work exists only as uncommitted changes and there are no separate branches, one option is to commit all current changes on `feat/ops-product-next-integration` as a single “integration of pane work” commit, run the test suite, and treat that as the first integrated state. Then future work can branch from there. This does not replace the ordered merge of the five branches once they exist.

---

*Integration branch `feat/ops-product-next-integration` has been created from `main` and is ready for merges once the five pane branches are available.*
