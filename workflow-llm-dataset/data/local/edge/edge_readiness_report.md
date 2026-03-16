# Edge Readiness Report

Generated: 2026-03-16T05:14:00.220439+00:00
Repo root: /Users/prady/Desktop/Clap/workflow-llm-dataset

## 1. Profile summary

- **Supported workflows:** weekly_status, status_action_bundle, stakeholder_update_bundle, meeting_brief_bundle, ops_reporting_workspace
- **Sandbox paths:** 14
- **Runtime Python:** 3.13 (recommended 3.10+)

## 2. Constrained run check

- **OK:** True
- **Missing critical:** none

- ⚠ Optional path missing: data/local/workspaces
- ⚠ Optional path missing: data/local/packages
- ⚠ Optional path missing: data/local/pilot

## 3. Failure when component missing

- **LLM backend**: release demo and trials fall back to baseline or fail
  - Degraded: baseline (no adapter)
- **base_model config**: demo exits; trials need LLM config
- **adapter_path**: demo/trials use base model only
  - Degraded: baseline
- **data/local (sandbox)**: writes fail; workspace/package flows fail
- **configs/settings.yaml**: setup/assist commands may fail; release verify may warn
  - Degraded: CLI uses defaults where possible
- **configs/release_narrow.yaml**: release verify/run use defaults
  - Degraded: default trial set

## 4. Optional features (disabled when missing)

- **retrieval-augmented generation**: missing retrieval corpus or pack → no retrieval; context-only generation
- **adapter fine-tuning**: missing mlx or sft data → no adapter; base model only
- **pack-driven trials**: missing data/local/packs or role pack → default trial_ids used
- **staging board**: missing data/local/staging → stage commands create dir or skip
- **eval board**: missing data/local/eval → eval commands create dir or skip
- **devlab experiments**: missing data/local/devlab → devlab commands create dir or skip

## 5. Missing dependency summary

- **Overall OK:** True
- **Missing required:** none
- **Missing optional:** data/local/workspaces, data/local/packages, data/local/pilot, data/local/review, data/local/staging, data/local/devlab, data/local/eval, data/local/llm/runs, data/local/llm/corpus, data/local/llm/sft, data/local/incubator, data/local/packs, data/local/input_packs, data/local/trials

## 6. Supported workflow matrix

- **weekly_status**: Single weekly status artifact.
  - Required files: ['manifest.json', 'weekly_status.md']
- **status_action_bundle**: Status brief + action register bundle.
  - Required files: ['manifest.json']
- **stakeholder_update_bundle**: Stakeholder update + decision requests bundle.
  - Required files: ['manifest.json']
- **meeting_brief_bundle**: Meeting brief + action items bundle.
  - Required files: ['manifest.json']
- **ops_reporting_workspace**: Multi-artifact ops reporting workspace (M21S/A2).
  - Required files: ['workspace_manifest.json', 'source_snapshot.md']
