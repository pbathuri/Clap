# M23B — Edge / Hardware Readiness Layer — Validation

## Summary

- **Local-only:** All edge outputs live under `data/local/edge/`. No cloud; no hardware device specs invented.
- **Explicit assumptions:** Profile makes runtime (Python), storage (sandbox paths), and model (local LLM optional) assumptions explicit.
- **Inspectable:** Readiness report, missing-deps report, workflow matrix, and package report are markdown/json files written to disk.

## Files Modified / Added

| Action | Path |
|--------|------|
| Added | `src/workflow_dataset/edge/__init__.py` |
| Added | `src/workflow_dataset/edge/profile.py` — build_edge_profile, SANDBOX_PATHS, SUPPORTED_WORKFLOWS |
| Added | `src/workflow_dataset/edge/checks.py` — run_readiness_checks, checks_summary |
| Added | `src/workflow_dataset/edge/report.py` — generate_edge_readiness_report, generate_missing_dependency_report, generate_workflow_matrix_report, generate_package_report |
| Modified | `src/workflow_dataset/cli.py` — edge readiness, edge package-report |
| Added | `tests/test_edge.py` |
| Added | `docs/M23B_EDGE_READINESS_VALIDATION.md` |

## Edge CLI Usage

```bash
# Run readiness checks and print summary
workflow-dataset edge readiness
workflow-dataset edge readiness --output data/local/edge/readiness.md

# Print edge profile (runtime, storage, model, workflows)
workflow-dataset edge profile
workflow-dataset edge profile --repo-root /path --config configs/settings.yaml

# Generate full edge readiness report
workflow-dataset edge report
workflow-dataset edge report --output /path/edge_readiness_report.md

# Missing dependency report
workflow-dataset edge missing-deps
workflow-dataset edge missing-deps --output data/local/edge/missing_dependency_report.md

# Supported workflow matrix (markdown or json)
workflow-dataset edge workflow-matrix
workflow-dataset edge workflow-matrix --format json --output matrix.json

# Edge packaging metadata (config, workflow availability, deps)
workflow-dataset edge package-report
workflow-dataset edge package-report --output data/local/edge/edge_package_report.md
```

## Sample Readiness Report

**data/local/edge/edge_readiness_report.md** (excerpt):

```markdown
# Edge Readiness Report

Local deployment profile and readiness checks. No cloud; no hardware specs.

## Summary

- **Ready:** true
- **Checks passed:** 12 / 12
- **Failed (required):** 0
- **Optional disabled:** 0

## Runtime requirements

- python_version_min: 3.10
- python_version_recommended: 3.11
- python_version_current: 3.13
- no_cloud_required: True

## Sandbox paths

- `data/local/workspaces` — exists
- `data/local/packages` — exists
- `data/local/review` — exists
- ...

## Readiness checks

- **python_version** — ok: Python 3.13 (min 3.10)
- **config_exists** — ok: configs/settings.yaml
- **sandbox_data_local_workspaces** — ok (optional): data/local/workspaces exists
- ...

## Supported workflows

- weekly_status
- status_action_bundle
- stakeholder_update_bundle
- meeting_brief_bundle
- ops_reporting_workspace

---
*Generated for local edge deployment. No cloud or production deployables.*
```

## Sample Supported-Workflow Matrix

**data/local/edge/supported_workflow_matrix.md**:

```markdown
# Supported Workflow Matrix

| Workflow | Description | Required | Optional |
|----------|-------------|----------|----------|
| weekly_status | Single weekly status artifact (summary, wins, blockers, next steps). | config, sandbox | llm_adapter, retrieval_corpus |
| status_action_bundle | Status brief + action register. | config, sandbox | llm_adapter, retrieval_corpus |
| stakeholder_update_bundle | Stakeholder-facing update + decision requests. | config, sandbox | llm_adapter, retrieval_corpus |
| meeting_brief_bundle | Meeting brief + action items. | config, sandbox | llm_adapter, retrieval_corpus |
| ops_reporting_workspace | Multi-artifact workspace (all six artifacts). | config, sandbox | llm_adapter, retrieval_corpus |
```

## Tests Run

```bash
cd workflow-llm-dataset
PYTHONPATH=src python3 -m pytest tests/test_edge.py -v
# 8 passed
```

## Constraints Preserved

- No hardware device specs; only runtime/storage/model assumptions and checks.
- No cloud-first assumptions; profile states no_cloud_required.
- No auto-package into production; reports are local and inspectable only.
- Local-first: all outputs under data/local/edge/.

---

## Recommendation for Next Edge/Productization Batch

1. **Version the profile:** Add a profile_version or schema_version so future edge packaging can detect compatibility.
2. **Optional feature matrix:** Extend the workflow matrix with a column listing which optional features each workflow can use (retrieval, adapter, intake) and how they degrade when unavailable.
3. **Bundle manifest:** Add a command or report section that lists which config files and paths would be included in a minimal “edge bundle” tarball for deployment testing (read-only manifest, no auto-packaging).
4. **CI readiness gate:** Use `workflow-dataset edge readiness` in CI and fail the job when `failed_required` > 0 so deployment assumptions stay validated.
