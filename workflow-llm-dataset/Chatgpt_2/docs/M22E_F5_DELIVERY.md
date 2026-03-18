# M22E-F5 — Template Testing Harness + Golden Output Fixtures — Delivery

## 1. Files modified

| File | Changes |
|------|--------|
| `src/workflow_dataset/templates/__init__.py` | Exported `expected_artifact_list_for_template`, `run_template_harness`, `validate_workspace_against_template`. |
| `src/workflow_dataset/cli.py` | Added `templates test --id X [--workspace path] [--repo-root]`. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/templates/harness.py` | `expected_artifact_list_for_template(template)`, `required_manifest_keys_for_template(template)`, `validate_workspace_against_template(workspace_path, template_id_or_dict, repo_root)` → `HarnessResult`; `run_template_harness(template_id, workspace_path=None, repo_root=None)`. |
| `tests/fixtures/template_harness/ops_reporting_core/workspace_manifest.json` | Golden manifest: workflow, template_id, artifact_list (source_snapshot + status_brief, action_register, decision_requests). |
| `tests/fixtures/template_harness/ops_reporting_core/*.md` | Minimal golden artifact files (source_snapshot, status_brief, action_register, decision_requests). |
| `tests/fixtures/template_harness/README.md` | Describes fixture layout. |
| `tests/test_template_harness.py` | Tests: expected list, required keys, validate success (fixture), missing artifact, wrong order, manifest mismatch, run without/with workspace, HarnessResult.to_message. |
| `docs/M22E_F5_DELIVERY.md` | This file. |

## 3. Exact test commands

```bash
cd workflow-llm-dataset && PYTHONPATH=src python3 -m pytest tests/test_template_harness.py -v
```

Optional (run harness for one template from CLI):

```bash
workflow-dataset templates test --id ops_reporting_core
workflow-dataset templates test --id ops_reporting_core --workspace tests/fixtures/template_harness/ops_reporting_core
```

## 4. Sample fixture definition

**Golden workspace layout** for template `ops_reporting_core`:

- **workspace_manifest.json** — Must include `workflow`, `template_id`, `artifact_list` (order matters).
- **source_snapshot.md** — First artifact (convention).
- **status_brief.md**, **action_register.md**, **decision_requests.md** — Template artifact filenames in template order.

**workspace_manifest.json** (excerpt):

```json
{
  "workflow": "ops_reporting_workspace",
  "template_id": "ops_reporting_core",
  "artifact_list": [
    "source_snapshot.md",
    "status_brief.md",
    "action_register.md",
    "decision_requests.md"
  ]
}
```

## 5. Sample harness output

**Pass (no workspace):**

```
PASS  ops_reporting_core
  Expected artifacts: ['source_snapshot.md', 'status_brief.md', 'action_register.md', 'decision_requests.md']
```

**Pass (with workspace):** Same, after validating fixture dir.

**Fail (missing artifact):**

```
FAIL  ops_reporting_core
  Missing artifacts: ['action_register.md', 'decision_requests.md']
Template: ops_reporting_core
Expected artifacts (order): ['source_snapshot.md', 'status_brief.md', 'action_register.md', 'decision_requests.md']
Actual artifacts: ['source_snapshot.md', 'status_brief.md']
```

**Fail (manifest):**

```
FAIL  ops_reporting_core
  Missing required manifest key: template_id
```

## 6. Exact tests run

```bash
cd /Users/prady/Desktop/Clap/workflow-llm-dataset && PYTHONPATH=src python3 -m pytest tests/test_template_harness.py -v
```

**Result:** 9 passed:

- `test_expected_artifact_list_for_template`
- `test_required_manifest_keys_for_template`
- `test_validate_workspace_against_template_success`
- `test_validate_workspace_against_template_missing_artifact`
- `test_validate_workspace_against_template_wrong_order`
- `test_validate_workspace_against_template_manifest_mismatch`
- `test_run_template_harness_without_workspace`
- `test_run_template_harness_with_fixture_workspace`
- `test_harness_result_to_message_readable`

## 7. Remaining weaknesses (this pane only)

- **Single golden template:** Only `ops_reporting_core` has a fixture workspace; `weekly_plus_stakeholder` and others can be added the same way.
- **No full-text golden comparison:** Harness checks inventory and order only; it does not assert artifact body content (by design; avoids brittle snapshots).
- **Manifest key set:** Required keys are fixed (`workflow`, `artifact_list`, `template_id`); optional keys are not validated.
- **Order from manifest only:** When manifest is missing, actual artifacts are taken from dir listing (sorted), so order check is skipped for that case.
- **No run-from-demo:** Harness does not invoke `release demo`; it validates an existing workspace dir. To regression-test “run demo then validate,” a separate integration test or script would be needed.
