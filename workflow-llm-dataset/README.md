# Workflow LLM Dataset Builder

This repository builds a primary-source-first, hierarchy-preserving occupational workflow dataset for downstream LLM training and retrieval.

## Core goals

The dataset should allow a model or analyst to answer:
- What is this industry, field, or subfield?
- Which occupations exist within it?
- What do those workers actually do?
- Which tools, software, machines, forms, maps, and documents are used?
- What are the workflow steps, handoffs, bottlenecks, and KPI signals?
- Which parts are automatable, augmentable, or human-led?

## Principles

- Primary-source-first
- Provenance on every row
- Hierarchy preserved
- No hallucinated tasks or tools
- Refreshable, versioned, auditable

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python scripts/bootstrap_data_dirs.py
python -m workflow_dataset.cli build --config configs/settings.yaml
```

## Main outputs

* `outputs/parquet/`
* `outputs/csv/`
* `outputs/excel/workflow_llm_primary_dataset_v1.xlsx`
* `outputs/qa/build_report.md`

## Build phases

1. Ingest authoritative source files
2. Normalize taxonomies and occupations
3. Map industries to occupations
4. Enrich with tasks, tools, context, labor data
5. Infer workflows, pain points, KPIs, automation candidacy
6. Validate integrity and provenance
7. Export machine-readable and analyst-readable outputs
