-- Indexes for common lookups and joins
CREATE INDEX IF NOT EXISTS idx_industries_parent ON industries(parent_id);
CREATE INDEX IF NOT EXISTS idx_industries_taxonomy ON industries(taxonomy_system);
CREATE INDEX IF NOT EXISTS idx_occupations_taxonomy ON occupations(taxonomy_system);
CREATE INDEX IF NOT EXISTS idx_occupations_code ON occupations(occupation_code);
CREATE INDEX IF NOT EXISTS idx_iom_industry ON industry_occupation_map(industry_id);
CREATE INDEX IF NOT EXISTS idx_iom_occupation ON industry_occupation_map(occupation_id);
CREATE INDEX IF NOT EXISTS idx_tasks_occupation ON tasks(occupation_id);
CREATE INDEX IF NOT EXISTS idx_tools_occupation ON tools_and_technology(occupation_id);
CREATE INDEX IF NOT EXISTS idx_workflow_occupation ON workflow_steps(occupation_id);
