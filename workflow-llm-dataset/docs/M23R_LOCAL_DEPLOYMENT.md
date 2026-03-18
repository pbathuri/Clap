# M23R — Packaged Local Deployment + First-Run Installer Flow

## Objective

Make the product deployable to a real user machine as a coherent local product:

1. **Package** current local product state into a reproducible profile  
2. **Validate** local runtime requirements at install time  
3. **First-run** install/bootstrap with handoff into onboarding  
4. **Verify** which product surfaces are available (jobs, routines, macros)  
5. **Reproducible** local deployment profile (JSON + report)  
6. **Prepare** for real-world usage and future appliance-style packaging  

Constraints: **local-only**, no cloud installer, no broad OS-level mutation beyond explicit local setup, no hidden services.

---

## CLI

```bash
workflow-dataset package local-deploy [--repo-root PATH] [--output PATH] [--tier TIER]
workflow-dataset package install-check [--repo-root PATH] [--output PATH]
workflow-dataset package first-run [--repo-root PATH] [--output PATH] [--skip-onboarding]
```

- **package local-deploy** — Build deployment profile (edge + readiness + trust + product surfaces), write `data/local/deployment/local_deployment_profile.json` and `local_deployment_report.md`. Optional `--output` for profile JSON path; `--tier` for edge tier.
- **package install-check** — Run readiness validation (edge checks + package readiness). Exits 1 if required checks fail. Optional `--output` to write report.
- **package first-run** — Ensure local dirs, run install-check, run onboarding bootstrap (unless `--skip-onboarding`), build first-run summary. Prints combined report and next-step hint (onboard bootstrap, console, macro run).

---

## Local deployment profile

- **Location**: `data/local/deployment/local_deployment_profile.json`  
- **Contents**: `version`, `generated_at`, `repo_root`, `edge_profile` (runtime, storage, sandbox paths), `readiness` (machine + product readiness), `trust_summary` (safe_to_expand, failed_gates_count, approval_registry_exists), `product_surfaces` (job_packs_count, routines_count, macros_count, sample ids), `errors`.

Report: `data/local/deployment/local_deployment_report.md` (human-readable summary).

---

## Install check

- Runs **edge readiness checks** (Python version, config exists, sandbox paths).  
- Runs **package readiness** (machine + product).  
- Returns **passed** (bool), **failed_required**, **missing_prereqs**, **checks** (list of check_id, passed, message, optional).  
- **No mutation**; validation only.

---

## First-run flow

1. **Ensure dirs** — Create `data/local/*` and `data/local/deployment` if missing.  
2. **Install check** — Run validation; result included in report.  
3. **Onboarding** — `run_onboarding_flow(..., persist_profile=True)` unless `--skip-onboarding`.  
4. **First-run summary** — `build_first_run_summary` + `format_first_run_summary` (what can do safely, recommended first workflow).  
5. **Handoff** — Report text + “Next: workflow-dataset onboard bootstrap — then workflow-dataset console or macro run”.

---

## Sample deployment profile (excerpt)

```json
{
  "version": "1",
  "generated_at": "2025-03-16T12:00:00.000000Z",
  "repo_root": "/path/to/repo",
  "edge_profile": {
    "repo_root": "/path/to/repo",
    "config_exists": true,
    "runtime_requirements": {
      "python_version_min": "3.10",
      "python_version_current": "3.11",
      "no_cloud_required": true
    }
  },
  "readiness": { "current_machine_readiness": { "ready": true, "passed": 12, "total": 12 }, "ready_for_first_real_user_install": false },
  "trust_summary": { "safe_to_expand": false, "failed_gates_count": 1, "approval_registry_exists": false },
  "product_surfaces": { "job_packs_count": 0, "routines_count": 0, "macros_count": 0 }
}
```

---

## Sample install-check output

```
=== Install check (local deployment) ===

2 required check(s) failed. Fix missing prerequisites before install.

[Missing prerequisites]
  - data/local/workspaces missing
  - configs missing

[Checks]
  PASS  python_version — Python 3.11 (min 3.10)
  FAIL  config_exists — configs/settings.yaml
  FAIL  sandbox_data_local_workspaces — data/local/workspaces missing
  ...

(Validation only. No changes made.)
```

---

## Tests

```bash
pytest tests/test_local_deployment.py -v
```

Covers: get_deployment_dir, build_local_deployment_profile structure, write_deployment_profile (JSON + report), run_install_check structure, format_install_check_report, run_first_run structure (skip_onboarding), format_deployment_report.

---

## Files modified / created

| Action | Path |
|--------|------|
| Created | `src/workflow_dataset/local_deployment/__init__.py` |
| Created | `src/workflow_dataset/local_deployment/profile.py` — build_local_deployment_profile, write_deployment_profile, format_deployment_report, get_deployment_dir |
| Created | `src/workflow_dataset/local_deployment/install_check.py` — run_install_check, format_install_check_report |
| Created | `src/workflow_dataset/local_deployment/first_run.py` — run_first_run, _ensure_local_dirs |
| Modified | `src/workflow_dataset/cli.py` — package local-deploy, install-check, first-run |
| Created | `tests/test_local_deployment.py` |
| Created | `docs/M23R_LOCAL_DEPLOYMENT.md` — this doc |

---

## Next phase

- **Appliance-style packaging**: Script or Make target that runs `package local-deploy`, then tars/zips `data/local/deployment` + configs for copy to another machine; optional `package install-check` on target.  
- **First-run wizard**: Optional TUI or guided prompts after `package first-run` (e.g. “Create approval registry?”, “Run first macro?”).  
- **Deployment profile versioning**: Schema version in profile and compatibility check when loading on another machine.
