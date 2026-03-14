# Excel Workbook Specification

Create one workbook:
outputs/excel/workflow_llm_primary_dataset_v1.xlsx

This workbook must be large, structured, readable, and suitable for both:
- analyst review
- downstream LLM dataset inspection

## Sheet order

1. README
2. Taxonomy_ISIC
3. Taxonomy_NAICS
4. Taxonomy_SOC
5. Taxonomy_ONET
6. Industry_Occupation_Map
7. Occupations_Master
8. Occupation_Aliases
9. Tasks
10. Detailed_Work_Activities
11. Work_Context
12. Tools_Technology
13. Skills_Knowledge_Abilities
14. Workflow_Steps
15. Pain_Points
16. KPI_Library
17. Labor_Market
18. Source_Register
19. Provenance_Row_Map
20. QA_Issues
21. Ambiguities_Review

## Formatting rules

- freeze top row on every sheet
- apply autofilter to every sheet
- use wrapped header text
- no merged cells inside tables
- keep column names explicit and stable
- do not hide evidence columns
- keep IDs visible
- use built-in number/date formats
- reset filters before final export
- ensure workbook opens with no broken formulas

## README sheet requirements

Include:
- project purpose
- build timestamp
- source versions used
- methodology summary
- confidence model summary
- limitations
- definitions of key review_status values
- sheet descriptions
- refresh instructions

## Required columns on substantive sheets

Every major sheet must include where relevant:
- row_id or entity_id
- source_id
- retrieval_date
- version_tag
- confidence_score
- review_status

## Excel modeling rules

- do not create only one giant denormalized sheet
- preserve hierarchy in separate taxonomy sheets
- keep evidence-rich atomic tables available
- allow downstream analysts to inspect row-level provenance
- do not overwrite raw task text with short summaries

## Review usability requirement

The workbook should allow an analyst to answer:
- what is this occupation
- where does it sit in the hierarchy
- what does the worker actually do
- what tools and systems are used
- what workflow steps were inferred
- what pain points and KPIs were attached
- which claims came from which source
