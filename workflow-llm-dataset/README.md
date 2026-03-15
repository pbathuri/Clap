# Workflow LLM Dataset & Personal Agent Foundation

This repository is the **foundational intelligence layer** for a **local-first personal edge AI agent**: a plug-and-play device that learns from one user’s work environment and acts as a Jarvis-like desktop/work operator.

## Product vision

We are building a **personal work agent** that:

- Runs on a **physical edge device** (initial target: Raspberry Pi 5 + AI module; later stronger hardware)
- Connects to **one user’s** laptop/tools/data/workflows
- **Learns privately** from observation and explicit teaching
- Builds a **personal work memory graph** and a **task/workflow execution graph**
- Operates as a **desktop/work operator** with **safe simulated execution by default**
- Makes **no changes to the user’s real system** unless the user explicitly approves

**Principles:** Local-first, private-first, one-device-per-user, simulate-first, approval-gated local actions. Strongest-first verticals: **logistics**, **operations**, **founder workflows**, **office admin**.

## What this repo contains

### 1. Global work priors (dataset pipeline)

The existing **dataset build** produces occupational knowledge used as a **global prior** by the agent:

- Industries (ISIC, NAICS), occupations (O*NET-SOC), industry–occupation mapping
- Tasks, detailed work activities, work context, tools & technology, skills/knowledge/abilities
- Labor market data (BLS)
- **Workflow priors** (inferred workflow steps from tasks/DWA)
- Placeholders for KPI, pain-point, and automation priors

This is **not** the end product; it is the prior knowledge base that helps the device interpret what the user is doing. Outputs: parquet, CSV, Excel, QA report.

### 2. Personal agent scaffolding

- **Observation layer** (Tier 1–3): schema and modules for file, app, browser, terminal, calendar, and manual-teaching events — on-device only; no real collectors yet.
- **Personal work graph**: schema and modules for profile, projects, routines, workflows, preferences, approval boundaries — on-device only.
- **Agent execution layer**: execution modes (observe → simulate → assist → automate), action policy, audit log, sandbox runner — interfaces only; default mode **simulate**.

See **docs/** for architecture, vision, edge device plan, privacy model, and observation phases; **docs/schemas/** for personal graph, observation events, action log, and execution modes.

### 3. Local LLM training pipeline (Apple Silicon–first)

A **first-pass local training pipeline** lets the system:

1. **Prepare a domain-adaptation corpus** from global work priors (processed parquet).
2. **Build an instruction/SFT dataset** from priors + local graph (routines, suggestions).
3. **Train a small LoRA adapter** locally using **MLX / mlx-lm** (no CUDA-only or QLoRA-primary path).
4. **Evaluate** on repo-specific tasks (knowledge QA, workflow inference, routine explanation, next-step suggestion, etc.).
5. Stay **local-first** and **retrieval-friendly**: fine-tuning augments, and does not replace, the graph/store/parquet.

- **Why we don’t train from scratch**: We adapt a small instruction-tuned base model to the domain; the agent still relies on **retrieval** over corpus and graph for up-to-date facts and user-specific state.
- **Config**: `configs/llm_training.yaml` (backend, base_model, LoRA and data paths). All artifacts under `data/local/llm/`.
- **Details**: See **docs/LLM_TRAINING_PLAN.md** for scope, backend choice, risks, and future JAX/Flax option.

## Quick start (dataset build)

Run from the **workflow-llm-dataset** directory. On zsh, quote the optional extra: `'.[dev]'`.

```bash
cd workflow-llm-dataset   # if you're in the parent Clap repo
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python scripts/bootstrap_data_dirs.py
python -m workflow_dataset.cli build --config configs/settings.yaml
```

**Outputs:** `outputs/parquet/`, `outputs/csv/`, `outputs/excel/workflow_llm_primary_dataset_v1.xlsx`, `outputs/qa/build_report.md`.

### Quick start (LLM pipeline, Apple Silicon)

Prerequisites: processed outputs (run `build` above) and optionally observation + suggest (for routines/suggestions). Install MLX: `pip install 'mlx-lm[train]'` (optional, for training).

```bash
# 1. Prepare corpus from processed parquet
workflow-dataset llm prepare-corpus

# 2. Build SFT train/val/test from corpus + local graph
workflow-dataset llm build-sft

# 3. Train LoRA adapter (MLX)
workflow-dataset llm train

# 4. Evaluate on test split
workflow-dataset llm eval --run-dir data/local/llm/runs/eval_out

# 5. Demo: single prompt, optional retrieval
workflow-dataset llm demo --prompt "What does an operations coordinator do?" --retrieve 3
```

Corpus → `data/local/llm/corpus/corpus.jsonl`. SFT → `data/local/llm/sft/*.jsonl`. Runs → `data/local/llm/runs/<timestamp>/`. No cloud APIs; retrieval remains first-class.

### Local Operator Console (M9)

A guided TUI for setup, projects, suggestions, drafts, materialize, apply, rollback, and chat — without memorizing CLI commands. Local-only; apply and rollback require explicit confirmation.

```bash
workflow-dataset console
```

See **docs/LOCAL_OPERATOR_CONSOLE.md** for what it can do, safety/confirmation behavior, and limitations.

### Running tests

From the **workflow-llm-dataset** directory (not the parent `Clap` repo). Use `'.[dev]'` in zsh so the bracket is not globbed.

```bash
cd workflow-llm-dataset   # only if you're in Clap/
pip install -e '.[dev]'
pytest tests/test_ui_services.py tests/test_ui_state_store.py tests/test_console_cli.py -v
# or: pytest -v
```

## Config

- **configs/settings.yaml** — project paths, runtime, and **agent** section (observation, privacy, sync, execution mode, hardware/model profile, sandbox). Defaults: observation off, sync off, **execution_mode: simulate**.
- **configs/llm_training.yaml** — LLM pipeline: backend (mlx), base_model, LoRA hyperparameters, data paths (`corpus_path`, `sft_train_dir`, `runs_dir`), eval options.

## Architecture summary

| Layer | Role |
|-------|------|
| **A — Global work priors** | Dataset pipeline (current `build`): industries, occupations, tasks, DWAs, tools, workflow steps, labor market. |
| **B — Personal observation** | Local event capture (file, app, browser, terminal, calendar, teaching); phased by edge feasibility. |
| **C — Personal work graph** | Device-local graph: profile, projects, routines, workflows, preferences, approval boundaries. |
| **D — Agent execution** | Modes: observe, simulate, assist, automate. Default simulate; no local changes without approval. |
| **E — Device runtime** | Edge device, local model routing, vector store, event/graph persistence, privacy/sync boundaries, updates. |

## Roadmap

See **docs/ROADMAP_PERSONAL_AGENT.md** for:

- What exists today (dataset engine, scaffolding)
- Path from dataset → observation → personal graph → simulated assistant → approved-action agent → edge prototype
- Milestones: first local observer, first personal graph, first simulated suggestion loop, first approved action loop, first edge-device prototype

## Constraints

- **No cloud-first assumption** for learning or inference by default.
- **No agent autonomy on the real machine** by default; simulate first, approve then execute.
- The **dataset pipeline is preserved**; ingestion, normalization, mapping, exports, and QA are unchanged.
- Package name remains **workflow_dataset**; no broad rename.

## License and provenance

Primary-source-first; every row retains source_id. See methodology in the Excel README sheet and **docs/**.
