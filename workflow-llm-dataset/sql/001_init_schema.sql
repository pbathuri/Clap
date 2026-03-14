CREATE TABLE IF NOT EXISTS source_register (
  source_id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_path_or_url TEXT NOT NULL,
  publisher TEXT,
  taxonomy_version TEXT,
  publication_date TEXT,
  retrieval_date TEXT,
  license TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS industries (
  industry_id TEXT PRIMARY KEY,
  taxonomy_system TEXT NOT NULL,
  section_code TEXT,
  division_code TEXT,
  group_code TEXT,
  class_code TEXT,
  title TEXT NOT NULL,
  description TEXT,
  parent_id TEXT,
  taxonomy_version TEXT,
  source_id TEXT NOT NULL,
  FOREIGN KEY(source_id) REFERENCES source_register(source_id)
);

CREATE TABLE IF NOT EXISTS occupations (
  occupation_id TEXT PRIMARY KEY,
  taxonomy_system TEXT NOT NULL,
  occupation_code TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  parent_group TEXT,
  job_zone TEXT,
  education_level TEXT,
  source_id TEXT NOT NULL,
  FOREIGN KEY(source_id) REFERENCES source_register(source_id)
);

CREATE TABLE IF NOT EXISTS industry_occupation_map (
  map_id TEXT PRIMARY KEY,
  industry_id TEXT NOT NULL,
  occupation_id TEXT NOT NULL,
  mapping_basis TEXT NOT NULL,
  strength_score REAL,
  source_id TEXT NOT NULL,
  review_status TEXT NOT NULL,
  FOREIGN KEY(industry_id) REFERENCES industries(industry_id),
  FOREIGN KEY(occupation_id) REFERENCES occupations(occupation_id),
  FOREIGN KEY(source_id) REFERENCES source_register(source_id)
);

CREATE TABLE IF NOT EXISTS tasks (
  task_id TEXT PRIMARY KEY,
  occupation_id TEXT NOT NULL,
  task_text TEXT NOT NULL,
  task_type TEXT NOT NULL,
  frequency_signal REAL,
  importance_signal REAL,
  source_id TEXT NOT NULL,
  source_verbatim_excerpt TEXT,
  extracted_from_dataset TEXT,
  is_primary_source INTEGER NOT NULL,
  FOREIGN KEY(occupation_id) REFERENCES occupations(occupation_id),
  FOREIGN KEY(source_id) REFERENCES source_register(source_id)
);

CREATE TABLE IF NOT EXISTS tools_and_technology (
  tool_id TEXT PRIMARY KEY,
  occupation_id TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  tool_type TEXT NOT NULL,
  hot_technology_flag INTEGER,
  commodity_code TEXT,
  commodity_title TEXT,
  source_id TEXT NOT NULL,
  FOREIGN KEY(occupation_id) REFERENCES occupations(occupation_id),
  FOREIGN KEY(source_id) REFERENCES source_register(source_id)
);

CREATE TABLE IF NOT EXISTS workflow_steps (
  workflow_step_id TEXT PRIMARY KEY,
  occupation_id TEXT NOT NULL,
  workflow_name TEXT NOT NULL,
  step_order INTEGER NOT NULL,
  step_name TEXT NOT NULL,
  step_description TEXT,
  input_objects TEXT,
  output_objects TEXT,
  systems_used TEXT,
  human_role_type TEXT,
  automation_candidate TEXT,
  automation_reason TEXT,
  inference_method TEXT,
  source_id TEXT NOT NULL,
  confidence_score REAL,
  FOREIGN KEY(occupation_id) REFERENCES occupations(occupation_id),
  FOREIGN KEY(source_id) REFERENCES source_register(source_id)
);
