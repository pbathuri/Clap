# Objective

Build a production-grade, primary-source-first occupational workflow dataset for downstream LLM training, retrieval, workflow intelligence, and business process analysis.

This dataset must allow a system to:
- identify industries, subfields, and business activity categories
- identify real occupations linked to those industries
- understand what workers in those occupations actually do
- identify tools, software, machines, documents, vehicles, maps, forms, and systems used in the work
- reconstruct workflow steps carefully from task evidence
- detect pain points, bottlenecks, handoffs, delays, failure modes, and KPI signals
- assess whether a process is best suited for automation, augmentation, orchestration, or human-led execution

This is not a toy dataset.
It is intended to become a primary knowledge layer for building an LLM that can identify, learn, compare, explain, and generate workflows.

## Required characteristics

The dataset must be:
- hierarchy-preserving
- provenance-preserving
- source-traceable
- versioned
- refreshable
- context-rich
- machine-readable
- analyst-auditable
- suitable for export to a structured Excel workbook

## Core questions the dataset must answer

For any selected field, subfield, company type, or occupation:
1. What is it?
2. Where does it sit in the industry hierarchy?
3. Which occupations materially operate in this area?
4. What tasks do those workers actually perform?
5. In what sequence do those tasks occur in practice?
6. What tools, documents, environments, and systems are involved?
7. Which work steps are manual, repetitive, judgment-heavy, regulated, or physical?
8. Which failures or inefficiencies are visible in the workflow?
9. What KPIs reveal those failures?
10. Which parts are automatable, augmentable, or should remain human-led?

## Primary outputs

1. Large multi-sheet Excel workbook for analyst review
2. Normalized CSV files for inspection
3. Parquet files for model-building and retrieval pipelines
4. Source register and row-level provenance mapping
5. QA report and ambiguity review log

## Prohibited outcomes

Do not produce:
- fabricated tasks
- fabricated tools
- fabricated workflow steps
- uncited industry-to-occupation mappings
- generic summaries with no raw evidence
- flattened datasets that destroy hierarchy
- outputs that cannot be audited back to a source
