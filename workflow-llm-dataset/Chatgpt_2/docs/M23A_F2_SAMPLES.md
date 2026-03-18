# M23A-F2 — Sample outputs

## 1. Chain failure / resume / compare CLI usage

```bash
# Report for latest run (or by run id)
workflow-dataset chain report
workflow-dataset chain report latest
workflow-dataset chain report --run latest
workflow-dataset chain report <run_id> --output report.md

# Resume from a step (keeps prior results, re-runs from step to end)
workflow-dataset chain resume --run latest
workflow-dataset chain resume --run <run_id> --from-step 1

# Retry a single step
workflow-dataset chain retry-step --run latest --step 0
workflow-dataset chain retry-step --run <run_id> --step demo_weekly

# Compare two runs (positional or --run-a / --run-b)
workflow-dataset chain compare <id_a> <id_b>
workflow-dataset chain compare --run-a latest --run-b <other_id>
workflow-dataset chain compare --run-a A --run-b B --artifact-diff --json
```

## 2. Sample failed-chain report

Output of `workflow-dataset chain report <run_id>` when the run failed at step 1:

```markdown
# Chain run report

- **Run ID:** a1b2c3d4e5f6
- **Chain ID:** demo_chain
- **Variant:** default
- **Status:** failed
- **Started:** 2025-03-16T12:00:00.000000Z
- **Ended:** 2025-03-16T12:02:30.000000Z

**Failure summary:** exit code 1

## Failure report

- **Failing step:** 1 — demo_weekly
- **Why:** exit code 1

- **Artifacts already produced:**
  - `/path/to/runs/a1b2c3d4e5f6/steps/0/stdout.txt`
  - `/path/to/runs/a1b2c3d4e5f6/steps/0/stderr.txt`

- **Resume possible:** Yes

- **Recommended next command(s):**
  - Retry failing step: `workflow-dataset chain retry-step --run a1b2c3d4e5f6 --step demo_weekly`
  - Resume from next step: `workflow-dataset chain resume --run a1b2c3d4e5f6 --from-step 1`

## Steps

### Step 0: verify
- Status: success
- Started: 2025-03-16T12:00:00.000000Z
- Ended: 2025-03-16T12:00:05.000000Z
- Contract: inputs=[], outputs=[], resumable=True
- Outputs:
  - `.../steps/0/stdout.txt`
  - `.../steps/0/stderr.txt`

### Step 1: demo_weekly
- Status: failed
- Started: 2025-03-16T12:00:05.000000Z
- Ended: 2025-03-16T12:00:06.000000Z
- Error: exit code 1
- Outputs:
  - `.../steps/1/stdout.txt`
  - `.../steps/1/stderr.txt`

---
*Report for run_id=a1b2c3d4e5f6*
```

## 3. Sample resumed-chain report

After `workflow-dataset chain resume --run a1b2c3d4e5f6 --from-step 1`, a subsequent `chain report a1b2c3d4e5f6` might show:

```markdown
# Chain run report

- **Run ID:** a1b2c3d4e5f6
- **Chain ID:** demo_chain
- **Variant:** default
- **Status:** success
- **Started:** 2025-03-16T12:00:00.000000Z
- **Ended:** 2025-03-16T12:05:00.000000Z

## Steps

### Step 0: verify
- Status: success
...

### Step 1: demo_weekly
- Status: success
- Started: 2025-03-16T12:04:00.000000Z
- Ended: 2025-03-16T12:05:00.000000Z
- Outputs: ...

---
*Report for run_id=a1b2c3d4e5f6*
```

## 4. Sample chain variant compare output

Output of `workflow-dataset chain compare --run-a run_v1 --run-b run_v2 --artifact-diff`:

```
Run A: run_v1  {'chain_id': 'demo_chain', 'variant': 'v1', 'status': 'success'}
Run B: run_v2  {'chain_id': 'demo_chain', 'variant': 'v2', 'status': 'success'}
  Output inventories: output_inventory_a, output_inventory_b (use --json to see)
  Artifact diff: only_in_a=2, only_in_b=2, common=4
```

With `--json`:

```json
{
  "run_id_a": "run_v1",
  "run_id_b": "run_v2",
  "run_a": {"chain_id": "demo_chain", "variant": "v1", "status": "success"},
  "run_b": {"chain_id": "demo_chain", "variant": "v2", "status": "success"},
  "status_diff": null,
  "step_count_diff": null,
  "step_status_diff": [],
  "failure_diff": null,
  "output_inventory_a": [
    {"step_id": "verify", "step_index": 0, "output_paths": [".../steps/0/stdout.txt", ".../steps/0/stderr.txt"]},
    {"step_id": "demo_weekly", "step_index": 1, "output_paths": [".../steps/1/stdout.txt", ".../steps/1/stderr.txt"]}
  ],
  "output_inventory_b": [
    {"step_id": "verify", "step_index": 0, "output_paths": [".../steps/0/stdout.txt", ".../steps/0/stderr.txt"]},
    {"step_id": "demo_weekly", "step_index": 1, "output_paths": [".../steps/1/stdout.txt", ".../steps/1/stderr.txt"]}
  ],
  "artifact_diff": {
    "only_in_a": ["/path/to/runs/run_v1/steps/0/stdout.txt", "..."],
    "only_in_b": ["/path/to/runs/run_v2/steps/0/stdout.txt", "..."],
    "common_count": 0
  }
}
```
