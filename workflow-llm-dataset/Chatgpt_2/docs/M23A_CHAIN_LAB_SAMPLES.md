# M23A Chain Lab — Samples

## 1. Chain CLI usage

```bash
# List chain definitions
workflow-dataset chain list [--repo-root /path/to/repo]

# Define a chain from a JSON file
workflow-dataset chain define --id demo_chain --file ./chains/demo_chain.json [--repo-root /path]

# Run a chain (operator-started; stops on first failure by default)
workflow-dataset chain run demo_chain [--variant v1] [--no-stop-on-failure] [--repo-root /path]

# List recent runs
workflow-dataset chain list-runs [--limit 20] [--repo-root /path]

# Per-step report and run summary
workflow-dataset chain report <run_id> [--output report.md] [--repo-root /path]

# Artifact tree for a run
workflow-dataset chain artifact-tree <run_id> [--json] [--repo-root /path]

# Compare two chain runs
workflow-dataset chain compare <run_id_a> <run_id_b> [--json] [--repo-root /path]
```

## 2. Sample chain definition

File: `data/local/chain_lab/chains/demo_chain.json` (or any path passed to `chain define --file`):

```json
{
  "id": "demo_chain",
  "description": "Single step: release verify then demo weekly_status with save.",
  "steps": [
    {
      "id": "verify",
      "type": "cli",
      "label": "Release verify",
      "params": {
        "args": ["release", "verify"],
        "timeout": 60
      },
      "workflow_name": ""
    },
    {
      "id": "demo_weekly",
      "type": "cli",
      "label": "Demo weekly_status",
      "params": {
        "args": ["release", "demo", "--workflow", "weekly_status", "--save-artifact"],
        "timeout": 300
      },
      "workflow_name": "weekly_status"
    }
  ],
  "expected_inputs_per_step": {},
  "expected_outputs_per_step": {},
  "stop_conditions": ["stop_on_first_failure"],
  "workflow_names": ["weekly_status"],
  "variant_label": "default"
}
```

## 3. Sample chain run artifact tree

After `workflow-dataset chain run demo_chain` (run_id e.g. `a1b2c3d4e5f6`):

```
data/local/chain_lab/runs/
└── a1b2c3d4e5f6/
    ├── run_manifest.json
    └── steps/
        ├── 0/
        │   ├── input_snapshot.json
        │   ├── stdout.txt
        │   └── stderr.txt
        └── 1/
            ├── input_snapshot.json
            ├── stdout.txt
            └── stderr.txt
```

`run_manifest.json` contains: `run_id`, `chain_id`, `variant_label`, `status`, `step_results` (per-step status, started_at, ended_at, output_paths, error), `started_at`, `ended_at`, `failure_summary`.

## 4. Sample chain report

Output of `workflow-dataset chain report a1b2c3d4e5f6`:

```markdown
# Chain run report

- **Run ID:** a1b2c3d4e5f6
- **Chain ID:** demo_chain
- **Variant:** default
- **Status:** success
- **Started:** 2025-03-16T12:00:00.000000Z
- **Ended:** 2025-03-16T12:02:30.000000Z

## Steps

### Step 0: verify
- Status: success
- Started: 2025-03-16T12:00:00.000000Z
- Ended: 2025-03-16T12:00:05.000000Z
- Outputs:
  - `/path/to/runs/a1b2c3d4e5f6/steps/0/stdout.txt`
  - `/path/to/runs/a1b2c3d4e5f6/steps/0/stderr.txt`

### Step 1: demo_weekly
- Status: success
- Started: 2025-03-16T12:00:05.000000Z
- Ended: 2025-03-16T12:02:30.000000Z
- Outputs:
  - ...

---
*Report for run_id=a1b2c3d4e5f6*
```

## 5. Sample chain comparison output

Output of `workflow-dataset chain compare run_a run_b`:

```
Run A: run_a  {'chain_id': 'demo_chain', 'variant': 'v1', 'status': 'success'}
Run B: run_b  {'chain_id': 'demo_chain', 'variant': 'v2', 'status': 'failed'}
  Status diff: {'a': 'success', 'b': 'failed'}
  Step count diff: 0
  Step 1: success vs failed
  Failure diff: A=None  B=exit code 1
```

With `--json`:

```json
{
  "run_id_a": "run_a",
  "run_id_b": "run_b",
  "run_a": {"chain_id": "demo_chain", "variant": "v1", "status": "success"},
  "run_b": {"chain_id": "demo_chain", "variant": "v2", "status": "failed"},
  "status_diff": {"a": "success", "b": "failed"},
  "step_count_diff": null,
  "step_status_diff": [{"step_index": 1, "step_id_a": "demo_weekly", "step_id_b": "demo_weekly", "status_a": "success", "status_b": "failed"}],
  "failure_diff": {"a": null, "b": "exit code 1"}
}
```
