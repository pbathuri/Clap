# Missing Dependency Report

Generated: 2026-03-16T05:14:00.221290+00:00
Repo root: /Users/prady/Desktop/Clap/workflow-llm-dataset

## Summary

- **Overall OK:** True
- **Missing required:** none

## Required dependencies (reference)

- **python** (runtime): 3.10+ recommended
- **typer** (pip): CLI
- **rich** (pip): console output
- **pyyaml** (pip): configs
- **data/local** (storage): sandbox root
- **LLM backend (mlx or openai)** (runtime): required for full demo
- **base_model in LLM config** (config): required for demo

## Optional dependencies (reference)

- **mlx** (pip): local LLM backend
- **transformers** (pip): adapter training
- **adapter_path** (artifact): fine-tuned adapter; baseline used if missing
- **corpus_path** (config): retrieval corpus
- **configs/settings.yaml** (config): setup/assist defaults if missing
- **configs/release_narrow.yaml** (config): release defaults if missing
- **data/local/packs** (storage): pack-driven trials
- **data/local/eval** (storage): eval board
- **data/local/devlab** (storage): devlab experiments

## Path status

- `data/local/workspaces`: missing
- `data/local/packages`: missing
- `data/local/pilot`: missing
- `data/local/review`: missing
- `data/local/staging`: missing
- `data/local/devlab`: missing
- `data/local/eval`: missing
- `data/local/llm/runs`: missing
- `data/local/llm/corpus`: missing
- `data/local/llm/sft`: missing
- `data/local/incubator`: missing
- `data/local/packs`: missing
- `data/local/input_packs`: missing
- `data/local/trials`: missing

- ⚠ Optional path missing: data/local/workspaces
- ⚠ Optional path missing: data/local/packages
- ⚠ Optional path missing: data/local/pilot
