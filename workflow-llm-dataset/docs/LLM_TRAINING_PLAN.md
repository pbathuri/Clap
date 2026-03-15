# LLM Training Plan (Local-First, Apple Silicon)

## Current scope

- **Domain-adaptation corpus**: Build natural-language documents from global work priors (processed parquet: industries, occupations, tasks, DWAs, workflow steps, tools, work context, skills). Output: `data/local/llm/corpus/corpus.jsonl`.
- **SFT dataset**: Instruction examples from corpus + local graph (routines, suggestions). Task types: knowledge_qa, workflow_inference, routine_interpretation, suggestion_justification, next_step_suggestion, safety_boundary. Outputs: `data/local/llm/sft/train.jsonl`, `val.jsonl`, `test.jsonl`.
- **Training**: LoRA fine-tuning via **MLX / mlx-lm** (Apple-Silicon-first). No CUDA-only or QLoRA-primary path. Artifacts under `data/local/llm/runs/<timestamp>/`.
- **Evaluation**: Held-out test set; metrics: exact match, token overlap (ROUGE-lite), explanation completeness. Modes: model-only and retrieval+model.
- **Retrieval**: Lightweight lexical (BM25-like) retrieval over corpus for context-augmented prompts. Fine-tuning does **not** replace the graph/store/parquet; retrieval remains first-class.

## Why this repo is not training from scratch

We are **not** pretraining a base LM. We use a small instruction-tuned base (e.g. Llama 3.2 3B) and:

1. **Adapt it to the domain** using our corpus and SFT data (occupations, workflows, routines, suggestions).
2. **Keep retrieval central**: the agent answers by combining retrieved context (from corpus + graph) with a small local adapter. Training improves instruction-following and grounding on our task types; it does not replace the need to retrieve up-to-date priors and local graph state.

## Why retrieval remains necessary

- **Data freshness**: Parquet and graph are updated by the dataset pipeline and observation layer. The fine-tuned model cannot hold all occupations, workflows, and user-specific routines in weights.
- **Structured data**: Labels, IDs, and relationships live in the graph and exports; the model is better used to interpret and summarize retrieved snippets than to memorize them.
- **Local-first**: All retrieval is over local corpus and graph; no cloud APIs.

## Backend decision rationale

- **MLX / mlx-lm** chosen as the **first** backend because:
  - Native Apple Silicon support (MPS), no CUDA dependency.
  - LoRA training and inference via `mlx_lm.lora` and `mlx_lm.generate`.
  - Fits “run on a Mac” and future edge (e.g. Pi + NPU) story.
- **Modular design**: `train_backend.TrainBackend` is abstract; `MLXBackend` is one implementation. A future **JAX/Flax** or **PyTorch** backend can be added for non-Apple hardware or research without changing corpus/SFT/eval contracts.

## Risks

- **mlx-lm API/CLI drift**: We wrap the current `mlx_lm.lora` CLI; flags or data format may change. Mitigation: pin mlx-lm version in docs; use subprocess with clear error handling.
- **Small SFT size**: With little local graph data, SFT may be corpus-heavy; eval should track both corpus-only and graph-derived task types.
- **No merge step yet**: We save the adapter only; merge into base model is optional and not implemented in the first pass.

## Future work

- **JAX/Flax backend**: For non-Apple or research runs; same `TrainingRunConfig` and data paths.
- **Continued pretraining**: Hooks exist for domain-adaptation corpus as causal LM data; first working path is SFT-only.
- **Richer eval**: Retrieval-only baseline, base-model baseline, fine-tuned, fine-tuned+retrieval comparison; more task categories and metrics.
- **Eval set builder**: Dedicated held-out builder for occupational knowledge, workflow inference, routine explanation, project classification, next-step suggestion, suggestion justification, safety/boundary reasoning.

## M16 — Full-train and comparison (recommended command sequence)

After smoke-train has verified the path, run a **strong full-train** and evaluate personalization:

1. **Prepare/update corpus**  
   `workflow-dataset llm prepare-corpus --config configs/settings.yaml --llm-config configs/llm_training_full.yaml`

2. **Build/update SFT**  
   `workflow-dataset llm build-sft --config configs/settings.yaml --llm-config configs/llm_training_full.yaml`

3. **Launch full-train** (uses `configs/llm_training_full.yaml`: more epochs, M4/24GB-friendly)  
   `workflow-dataset llm train --llm-config configs/llm_training_full.yaml`

4. **Run comparison** (baseline vs smoke vs full adapter, retrieval off/on)  
   `workflow-dataset llm compare-runs --llm-config configs/llm_training_full.yaml`

5. **Run demo-suite** (curated personalization prompts for qualitative check)  
   `workflow-dataset llm demo-suite --llm-config configs/llm_training_full.yaml`  
   With retrieval: `workflow-dataset llm demo-suite --retrieval`

6. **Inspect reports**  
   - `data/local/llm/runs/comparison_latest.md` — slice metrics and retrieval impact  
   - `data/local/llm/runs/<run_dir>/quality_report.md` — per full-run summary and recommendation  

Naming: smoke runs live in `runs/smoke_YYYYMMDD_HHMMSS/`; full runs in `runs/YYYYMMDD_HHMMSS/`. Eval outputs go under `runs/eval_out/` or `runs/comparison_YYYYMMDD_HHMMSS/`.

## Local-first preservation

- All training inputs and outputs live under `data/local/llm/` (or configurable equivalent).
- No cloud APIs; no hidden network calls during training except explicit model download (e.g. Hugging Face once).
- Observation layer, personal graph, and dataset pipeline are unchanged; the LLM pipeline only **reads** from processed outputs and graph.
