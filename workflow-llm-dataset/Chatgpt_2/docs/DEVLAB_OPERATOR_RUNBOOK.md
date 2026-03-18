# M21W Development Lab — Operator Runbook

## Purpose

- **Curated external intake**: Register and inspect open-source repos in a sandbox; parse-only (no execution of external code).
- **Multi-provider model lab**: Compare Ollama (local-first) and optional OpenAI/Anthropic on workflow prompts; development use only.
- **Operator-controlled dev loop**: One-shot run that gathers evidence, repo reports, model comparison, and writes local artifacts; no autonomous code merging.

## Safety boundaries

- **No auto-run**: Cloned repos are parsed (file tree, README, deps); external code is never executed by default.
- **No silent adoption**: Adopting ideas or code from a repo is an explicit later step; devlab does not merge into product code.
- **No silent cloud**: API adapters (OpenAI, Anthropic) are used only when the corresponding API key is explicitly set; no fallback from local to cloud.
- **Explicit loop**: The dev loop is started by the operator (`devlab run-loop`); it does not run on a timer or daemon unless you configure one yourself.

## Sandbox paths

All devlab data lives under:

- `data/local/devlab/` (or `--devlab-root` if set)
  - `registry.json` — registered candidate repos
  - `repos/<repo_id>/` — cloned repos (sandbox only)
  - `reports/` — per-repo intake reports (`repo_intake_report_<id>.json`)
  - `model_compare/` — `model_compare_report.json`
  - `experiments/` — experiment definitions (`<id>.json`)
  - `experiment_queue.json` — D4 run history and queue (queued, running, done, failed, cancelled)
  - `proposals/` — patch proposals per run
  - `devlab_report.md`, `next_patch_plan.md`, `loop_status.json`

## Commands

### Repo registration and intake

```bash
# Register a candidate repo (does not clone)
workflow-dataset devlab add-repo --url https://github.com/owner/repo --label "Evaluation harness" --category evaluation

# List registered repos
workflow-dataset devlab list

# Clone into sandbox and parse (no execution)
workflow-dataset devlab ingest-repo owner_repo
# or by URL if already registered
workflow-dataset devlab ingest-repo https://github.com/owner/repo

# Generate per-repo intake report
workflow-dataset devlab repo-report owner_repo
```

### Model comparison

```bash
# Compare Ollama only (local)
workflow-dataset devlab compare-models --workflow weekly_status --providers ollama

# Compare multiple providers (OpenAI/Anthropic only if API keys set)
workflow-dataset devlab compare-models --workflow weekly_status --providers ollama,openai,anthropic
```

Workflows: `weekly_status`, `status_action_bundle`, `stakeholder_update_bundle`, `ops_reporting_workspace`.

### Dev loop

```bash
# One-shot run: evidence, repo reports, model compare, memo, tests
workflow-dataset devlab run-loop --workflow weekly_status --providers ollama

# Status (last run, artifact paths)
workflow-dataset devlab loop-status

# Clear running flag
workflow-dataset devlab stop-loop
```

## API keys (optional)

- **Ollama**: No key; ensure Ollama is running locally (`http://127.0.0.1:11434`).
- **OpenAI**: Set `OPENAI_API_KEY` in the environment to enable the OpenAI adapter.
- **Anthropic**: Set `ANTHROPIC_API_KEY` in the environment to enable the Anthropic adapter.

### D4: Scheduler + run history board

Local operator-controlled scheduler and run history. No background daemon; all actions are explicit.

| Action | Command |
|--------|--------|
| **Run once** | `workflow-dataset devlab run-experiment <experiment_id>` |
| **Queue run** | `workflow-dataset devlab queue-experiment <experiment_id>` |
| **List recent runs** | `workflow-dataset devlab run-history [--limit N] [--output file.json\|file.md]` |
| **Show run status** | `workflow-dataset devlab show-run <run_id\|experiment_id\|index>` |
| **Run next from queue** | `workflow-dataset devlab run-next` (runs one queued; then stops) |
| **Cancel queued** | `workflow-dataset devlab cancel-queued <experiment_id\|index>` |
| **Queue status** | `workflow-dataset devlab experiment-status` |

- **run-history** lists queue entries newest first; index `0` = most recent. Optional `--output` writes JSON or Markdown.
- **show-run** accepts: a `run_id` (e.g. from eval), an `experiment_id` (latest entry for that experiment), or a history index (e.g. `0` for most recent).
- **cancel-queued** only affects entries with status `queued`; done/failed/running are unchanged.
- **run-next** runs exactly one queued experiment (oldest in queue order) and returns; no perpetual loop.

#### Sample run history output

```bash
workflow-dataset devlab run-history --limit 5
```

```
  [0]  ops_reporting_benchmark  done  queued=2026-01-15T14:00:00  run_id=run_abc123  proposal_id=prop_xyz
  [1]  ops_reporting_benchmark  queued  queued=2026-01-15T14:05:00  run_id=  proposal_id=
  [2]  ops_reporting_benchmark  failed  queued=2026-01-14T10:00:00  run_id=  proposal_id=
```

```bash
workflow-dataset devlab show-run 0
```

```
  experiment_id: ops_reporting_benchmark
  status: done
  queued_at: 2026-01-15T14:00:00Z
  completed_at: 2026-01-15T14:06:00Z
  run_id: run_abc123
  proposal_id: prop_xyz
```

```bash
workflow-dataset devlab experiment-status
```

```
  queued: 1  running: 0  done: 2  failed: 1  cancelled: 0
  last: ops_reporting_benchmark  done  proposal=prop_xyz
```

### Experiments and proposals

```bash
# Seed default experiment definition
workflow-dataset devlab seed-experiment

# Queue then run (or run once directly)
workflow-dataset devlab queue-experiment ops_reporting_benchmark
workflow-dataset devlab run-next
# or run by id
workflow-dataset devlab run-experiment ops_reporting_benchmark
```

## Next steps

- Review `data/local/devlab/reports/repo_intake_report_<id>.json` and `model_compare_report.json` to decide what to adopt.
- Apply any code or pattern adoption explicitly; do not rely on the lab to merge into product.
