# M23W — Integration Hardening + Incubator Stabilization + Full Env Validation

## Objective

Make the integrated product surface (M23T + M23U + M23V) stable and testable as one product: incubator present, environment status explicit, validation report available.

## What was built

### 1. Incubator stabilization

- **Package:** `src/workflow_dataset/incubator/`
  - `registry.py`: `list_candidates`, `add_candidate`, `get_candidate`, `update_candidate`, `set_promotion_decision`, `mark_stage`, `attach_evidence`. Local file store under `data/local/incubator`.
  - `gates.py`: `evaluate_gates`, `promotion_report`. Minimal gates (stage + evidence).
- Mission-control no longer emits `[Incubator] error: No module named 'workflow_dataset.incubator'`.
- CLI `workflow-dataset incubator add-candidate|list|show|evaluate|promote|reject|hold|mark-stage|attach-evidence` works.

### 2. Environment / dependency hardening

- **Module:** `src/workflow_dataset/validation/env_health.py`
  - `check_environment_health(repo_root)`: required deps (pydantic, typer, rich, yaml), optional deps (pandas, sqlalchemy, …), python_version, incubator_present.
  - `format_health_report(health)`: plain-text report for console or file.
- **CLI:** `workflow-dataset health` — prints environment health; optional `--output` to write to file.
- No automatic installs; operator installs per `pyproject.toml` (e.g. `pip install -e .[dev]`).

### 3. Full-surface validation

- **Module:** `src/workflow_dataset/validation/run_validation.py`
  - `run_pytest_and_categorize(repo_root, tests_path, extra_args)`: runs pytest, returns passed/failed/errors/skipped and categorized failures (environment_issue, integration_issue, optional_dependency, stale_test).
- **Module:** `src/workflow_dataset/validation/validation_report.py`
  - `build_validation_report(repo_root)`: health + test run; `ready_for_operator_expansion` = required_ok and no failed/errors.
  - `format_validation_report_md(report)`: markdown report.
- **CLI:** `workflow-dataset validate` — runs health + pytest, prints or writes markdown report (`--output`).

### 4. Mission-control additive visibility

- **State:** `mission_control/state.py` section 16: `environment_health` (required_ok, optional_ok, python_version, incubator_present).
- **Report:** `mission_control/report.py`: `[Environment] required_ok=... optional_ok=... incubator_present=... python=...`.

### 5. Tests

- `tests/test_incubator.py`: registry and gates.
- `tests/test_env_health.py`: health check and report format.
- `tests/test_mission_control.py`: `test_mission_control_incubator_no_error_when_present`, `test_mission_control_report_includes_environment`.

## Commands

| Command | Purpose |
|--------|--------|
| `workflow-dataset health` | Environment and dependency health (no installs). |
| `workflow-dataset health --output path` | Write health report to file. |
| `workflow-dataset validate` | Health + pytest run, integrated validation report (stdout). |
| `workflow-dataset validate --output path` | Write validation report (markdown) to file. |

## Constraints respected

- No new product layers; no cloud; no weakening of local-first / sandbox-only / approval-gated.
- No silent installs; missing deps are reported explicitly.
- Incubator is local-only file store.

## Remaining known risks

- **Optional deps:** Some tests may still skip or fail if optional deps (e.g. pandas, sqlalchemy) are missing; categorized in validation report.
- **Full suite:** Run `pytest tests/` in project venv for full regression; `validate` runs the same suite and summarizes.
