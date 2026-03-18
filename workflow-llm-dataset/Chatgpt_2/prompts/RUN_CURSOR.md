You are building a production-grade occupational workflow dataset for LLM development.

You are not allowed to produce generic scraped sludge, vague summaries, or uncited workflow hallucinations.

Your mission is to build a large, hierarchy-preserving, provenance-preserving dataset that can train or ground an LLM to:
- identify industries and subfields
- identify occupations
- explain what workers in those occupations actually do
- identify tools, software, machines, documents, and environments used in the work
- infer workflow steps carefully from real task evidence
- identify pain points and KPI signals
- assess automation vs augmentation opportunities

## Read and obey these files first

- prompts/00_OBJECTIVE.md
- prompts/01_SOURCE_AUTHORITY.md
- prompts/02_SCHEMA.md
- prompts/03_EXTRACTION_RULES.md
- prompts/04_WORKFLOW_INFERENCE_RULES.md
- prompts/05_EXCEL_SPEC.md
- prompts/06_QA_ACCEPTANCE.md

Then inspect:
- context/
- data/raw/official/
- data/raw/private_examples/

## Non-negotiable behavior

1. Start with authoritative structured sources.
2. Build taxonomy tables before task tables.
3. Build occupation tables before workflow inference.
4. Build workflow inference only from evidence.
5. Preserve provenance on every row.
6. Do not flatten away hierarchy.
7. Do not invent tools, software, or workflow steps.
8. If uncertain, mark the row for review instead of guessing.
9. Store normalized tables in processed outputs before creating Excel.
10. Export both machine-readable data and analyst-readable Excel.

## Execution sequence

### Phase 1 — ingest
- ingest ISIC hierarchy
- ingest NAICS hierarchy
- ingest SOC hierarchy
- ingest O*NET occupation, task, DWA, work context, technology skills, tools and technology, skills, knowledge, abilities
- ingest BLS occupational projections, industry-occupation matrix, wage data, and related labor grounding files
- ingest ESCO occupations and skills mappings if available
- ingest private business documents if present
- register all sources in Source_Register

### Phase 2 — normalize
- normalize titles, IDs, dates, versions
- build canonical industry table
- build canonical occupation table
- preserve original codes and source-system identifiers
- generate concordance tables

### Phase 3 — map
- map industries to occupations using official matrices and crosswalks first
- use reviewed inference only where no official mapping exists
- assign mapping_basis and confidence_score

### Phase 4 — enrich
Attach, where available:
- task statements
- detailed work activities
- work context
- tools and technology
- technology skills
- labor-market signals
- physicality and environment markers
- document and system markers

### Phase 5 — workflow inference
For each occupation:
- cluster evidence into workflow units
- produce ordered workflow steps
- identify inputs, outputs, handoffs, systems, and exceptions
- identify pain points
- generate KPI candidates
- classify automation candidacy as automate / augment / human_led / unknown
- justify the classification
- mark all non-explicit workflow steps as inferred when appropriate

### Phase 6 — QA
- run taxonomy checks
- run duplicate checks
- run missing provenance checks
- run low-confidence review checks
- produce QA_Issues and Ambiguities_Review outputs

### Phase 7 — export
Create:
- outputs/processed/*.parquet
- outputs/csv/*.csv
- outputs/excel/workflow_llm_primary_dataset_v1.xlsx
- outputs/qa/build_report.md

## Data richness requirements

The dataset must capture actual work reality.
For each occupation, aim to capture:
- industry placement
- occupation hierarchy
- job summary
- task statements
- detailed work activities
- work context
- tools and technology
- software
- equipment
- documents handled
- physical environment
- cognitive demands
- coordination demands
- compliance requirements if evidenced
- workflow steps
- pain points
- KPI signals
- automation notes
- source provenance

## Evidence rules for actual tools used

Prefer in this order:
1. O*NET tools and technology / technology skills
2. official manuals and documentation
3. public SOPs and regulatory guidance
4. high-quality employer materials
5. multi-source corroborated industry evidence

Never assign a tool to an occupation simply because it sounds plausible.

## Runtime behavior

Work deeply and iteratively.
Do not stop after a shallow pass.
Prefer evidence, structure, and traceability over breadth without proof.
If a one-hour-plus run is possible, use that time to deepen coverage and improve row-level quality, not to generate vague summaries.

## Deliverable completion condition

The build is complete only when:
- hierarchy is intact
- occupations are grounded
- tasks are rich
- tools and context are present
- workflows are inferred carefully
- provenance is complete
- Excel is audit-ready
- QA sheets exist

## What Cursor should do first

1. Validate that official source folders exist and are non-empty.
2. Parse O*NET raw files into interim parquet files.
3. Parse taxonomy files into canonical hierarchy tables.
4. Register all files in Source_Register.
5. Build normalized occupation and task tables.
6. Produce a thin first-pass Excel workbook before deeper enrichment.
7. Run enrichment, workflow inference, QA, and final export.

## Build strategy

* First pass: taxonomy + occupations + provenance
* Second pass: tasks + tools + context
* Third pass: mapping + workflows + pain points + KPIs
* Fourth pass: QA + Excel hardening + ambiguity review

## Guardrails

* Never guess a task.
* Never guess a tool.
* Never flatten hierarchies prematurely.
* Every row must retain provenance.
* Every inferred workflow step must be explicitly labeled as inferred.
* Excel is the review surface, not the only storage layer.
