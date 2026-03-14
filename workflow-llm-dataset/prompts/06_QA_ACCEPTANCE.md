# QA and Acceptance Criteria

## Build rejection conditions

Reject the build if any of the following occur:
- fabricated tasks
- fabricated tools
- occupations without provenance
- mappings without basis
- missing source register entries
- duplicate IDs
- orphan hierarchy nodes
- major sheets missing required columns
- broken Excel formulas
- flattened hierarchy replacing normalized structure
- inferred workflow steps with no linked evidence

## Minimum QA checks

### 1. Taxonomy integrity
- parent-child hierarchy valid
- no orphan nodes
- no cycles
- taxonomy levels consistent

### 2. Occupation integrity
- each occupation linked to a canonical taxonomy code
- duplicate titles reviewed
- aliases separated from canonical titles

### 3. Mapping integrity
- each industry_occupation_map row has mapping_basis
- confidence_score populated
- reviewed inference clearly labeled

### 4. Provenance integrity
- every substantive row linked to source_id
- every source_id exists in Source_Register
- source metadata populated sufficiently for audit

### 5. Workflow integrity
- each workflow step linked to occupation_id
- inferred steps labeled
- automation candidacy justified
- handoffs or inputs/outputs present for inferred process maps where possible

### 6. Excel integrity
- workbook opens cleanly
- no #REF!
- no #DIV/0!
- no blank header names
- no hidden evidence columns
- sheet order matches specification

### 7. Training usefulness
Dataset should be rich enough that an LLM can answer:
- what the job is
- what tasks exist
- which tools are used
- which context the worker operates in
- what sequence of work occurs
- where failures arise
- which KPIs matter
- what could be automated or augmented

## QA outputs required

Create:
- QA_Issues sheet
- Ambiguities_Review sheet
- outputs/qa/build_report.md

## Review status guidance

Use these labels consistently:
- accepted
- reviewed
- needs_review
- rejected
