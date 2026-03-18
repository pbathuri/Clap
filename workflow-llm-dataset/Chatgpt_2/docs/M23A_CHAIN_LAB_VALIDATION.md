# M23A — Internal Agent Chain Lab — Validation

## Summary

- **Operator-controlled:** Chains are started explicitly via `workflow-dataset chain run --id <id>`. No auto-run; no uncontrolled looping.
- **Local-only:** Definitions in `data/local/chains/*.yaml|*.json`; run outputs in `data/local/chains/runs/<run_id>/`. No cloud; no auto-apply outside sandbox.
- **Inspectable:** Each step’s stdout/stderr and result are written to the run dir; run report and step JSON are persisted.

## Files Modified / Added

| Action | Path |
|--------|------|
| Added | `src/workflow_dataset/chain/__init__.py` |
| Added | `src/workflow_dataset/chain/registry.py` — load_chain, list_chains, get_chain, _expand_step_to_cmd |
| Added | `src/workflow_dataset/chain/runner.py` — run_chain, get_run_status, list_runs |
| Added | `data/local/chains/ops_reporting_chain_v1.yaml` |
| Added | `data/local/chains/simple_command_chain.json` |
| Modified | `src/workflow_dataset/cli.py` — chain list, chain run, chain status |
| Added | `tests/test_chain.py` |
| Added | `docs/M23A_CHAIN_LAB_VALIDATION.md` |

## Chain CLI Usage

```bash
# List defined chains
workflow-dataset chain list
workflow-dataset chain list --repo-root /path

# Run a chain (operator-started)
workflow-dataset chain run --id ops_reporting_chain_v1
workflow-dataset chain run -i simple_command_chain --notes "test run"
workflow-dataset chain run --id my_chain --no-stop-on-failure --timeout 600

# Inspect run status (run id or "latest")
workflow-dataset chain status --run latest
workflow-dataset chain status -r 202501151200_abc12def
```

## Sample Chain Definition

**data/local/chains/ops_reporting_chain_v1.yaml:**

```yaml
id: ops_reporting_chain_v1
name: Ops reporting chain v1
steps:
  - id: ingest
    type: intake_add
    params:
      path: ./notes
      label: sprint_notes
  - id: demo
    type: release_demo
    params:
      intake: sprint_notes
      template: ops_reporting_core
      save_artifact: true
expected_artifacts: []
stop_conditions:
  on_step_failure: true
```

**Step types:**

- **command** — raw shell command: `cmd: "workflow-dataset intake add --path ./x --label l1"`.
- **intake_add** — expanded to `workflow-dataset intake add --path <path> --label <label>`.
- **release_demo** — expanded to `workflow-dataset release demo` with `--intake`, `--template`, `--save-artifact` from params.

## Sample Chain Run Report

After `workflow-dataset chain run --id simple_command_chain`:

**data/local/chains/runs/<ts>_<rid>/run_report.json:**

```json
{
  "run_id": "202501151200_abc12def",
  "run_dir": "/path/to/data/local/chains/runs/202501151200_abc12def",
  "chain_id": "simple_command_chain",
  "status": "completed",
  "steps": [
    { "step_id": "step1", "status": "ok", "exit_code": 0, "stdout_path": "..." },
    { "step_id": "step2", "status": "ok", "exit_code": 0, "stdout_path": "..." }
  ],
  "steps_total": 2,
  "last_step_index": -1,
  "expected_artifacts": [],
  "operator_notes": ""
}
```

Per-step files:

- `step_0_step1.log` — stdout/stderr for step 0.
- `step_0_step1.json` — step result (status, exit_code, paths).
- Same for step 1.

## Tests Run

```bash
cd workflow-llm-dataset
PYTHONPATH=src python3 -m pytest tests/test_chain.py -v
# 10 passed
```

## Constraints Preserved

- No end-user orchestration: chain commands are for internal/dev use.
- No uncontrolled looping: chains are a fixed list of steps; no loops in the definition.
- No auto-apply outside sandbox: steps run workflow-dataset CLI (intake, release demo, etc.) which already stay in sandbox.
- All step outputs and reports are under `data/local/chains/runs/` and are inspectable.

---

## Recommendation for Next Internal Automation Batch

1. **Compare chain variants:** Add `workflow-dataset chain compare --run-a <id> --run-b <id>` to diff two run reports (step outcomes, exit codes) for the same or different chains.
2. **Max steps / guardrails:** Enforce a small `max_steps` in chain definition (e.g. 10) and reject runs that exceed it to keep chains short.
3. **Operator stop file:** Support a “stop file” (e.g. `data/local/chains/stop`) that the runner checks between steps; if present, abort and mark run as `stopped`.
4. **Artifact collection:** Optionally collect paths of known artifacts (e.g. workspace dirs created by release demo) into `run_report.json` under `final_artifacts` for easier inspection.
