# Canonical Schema

Build normalized tables first.
Excel is an export and review surface, not the source of truth.

## General modeling rules

- Use stable unique IDs for every entity
- Preserve original source codes alongside canonical IDs
- Keep one row per atomic record whenever possible
- Do not collapse many-to-many relationships into comma-separated text unless required for Excel convenience exports
- Retain raw extracted text where useful
- Attach provenance to every substantive row

## Canonical entities

### source_register
Columns:
- source_id
- source_name
- source_type
- source_path_or_url
- publisher
- taxonomy_version
- publication_date
- retrieval_date
- license
- notes

### industries
Columns:
- industry_id
- taxonomy_system                # ISIC or NAICS
- section_code
- division_code
- group_code
- class_code
- title
- description
- parent_id
- taxonomy_level                 # section/division/group/class
- taxonomy_version
- source_id

### occupations
Columns:
- occupation_id
- taxonomy_system                # SOC, O*NET, ESCO
- occupation_code
- title
- description
- parent_group
- job_zone
- education_level
- source_id

### occupation_aliases
Columns:
- alias_id
- occupation_id
- alias_text
- alias_source
- source_id

### industry_occupation_map
Columns:
- map_id
- industry_id
- occupation_id
- mapping_basis                  # official_matrix / crosswalk / reviewed_inference
- strength_score
- source_id
- confidence_score
- review_status

### tasks
Columns:
- task_id
- occupation_id
- task_text
- task_type                      # core / supplemental / inferred_cluster
- frequency_signal
- importance_signal
- source_id
- source_verbatim_excerpt
- extracted_from_dataset
- is_primary_source
- confidence_score
- review_status

### detailed_work_activities
Columns:
- dwa_id
- occupation_id
- dwa_code
- dwa_title
- category
- source_id
- confidence_score
- review_status

### work_context
Columns:
- context_id
- occupation_id
- context_code
- context_title
- context_value
- scale_description
- source_id

### tools_and_technology
Columns:
- tool_id
- occupation_id
- tool_name
- tool_type                      # software / machine / equipment / dashboard / document / form / map / vehicle / sensor / handheld / spreadsheet
- hot_technology_flag
- commodity_code
- commodity_title
- source_id
- confidence_score
- review_status

### skills_knowledge_abilities
Columns:
- ska_id
- occupation_id
- dimension_type                 # skill / knowledge / ability / work_style / work_activity
- dimension_name
- importance
- level
- source_id

### workflow_steps
Columns:
- workflow_step_id
- occupation_id
- workflow_name
- step_order
- step_name
- step_description
- trigger_event
- preconditions
- input_objects
- output_objects
- systems_used
- documents_used
- tool_ids
- handoff_to_role
- human_role_type
- automation_candidate           # automate / augment / human_led / unknown
- automation_reason
- inference_method
- source_id
- confidence_score
- review_status

### pain_points
Columns:
- pain_point_id
- occupation_id
- workflow_step_id
- pain_point_type                # manual_entry / delay / approval_bottleneck / reconciliation / routing / scheduling / compliance / exception_handling / communication_gap
- pain_point_description
- evidence_type
- source_id
- confidence_score
- review_status

### kpis
Columns:
- kpi_id
- occupation_id
- workflow_name
- kpi_name
- kpi_definition
- kpi_formula
- unit
- problem_signal
- source_id

### labor_market
Columns:
- labor_id
- occupation_id
- employment
- median_pay
- projected_growth
- openings
- geography
- year
- source_id

### provenance_row_map
Columns:
- row_map_id
- entity_table
- entity_row_id
- source_id
- source_locator                 # line / page / row / tab / cell / url_fragment / filename
- retrieval_date
- extractor_notes

## Modeling rule for workflow inference

A workflow step is not the same thing as a raw task statement.
Workflows are derived structures.
Every derived structure must remain linked back to raw evidence rows.
