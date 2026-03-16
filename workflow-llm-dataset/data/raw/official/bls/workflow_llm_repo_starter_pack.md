# Workflow LLM Repo Starter Pack

## Repository Tree

```text
workflow-llm-dataset/
├─ README.md
├─ .gitignore
├─ .env.example
├─ pyproject.toml
├─ Makefile
├─ configs/
│  ├─ settings.yaml
│  ├─ sources.yaml
│  └─ logging.yaml
├─ prompts/
│  ├─ 00_OBJECTIVE.md
│  ├─ 01_SOURCE_AUTHORITY.md
│  ├─ 02_SCHEMA.md
│  ├─ 03_EXTRACTION_RULES.md
│  ├─ 04_WORKFLOW_INFERENCE_RULES.md
│  ├─ 05_EXCEL_SPEC.md
│  ├─ 06_QA_ACCEPTANCE.md
│  └─ RUN_CURSOR.md
├─ context/
│  ├─ anthropic_labor_market_ai.pdf
│  ├─ report.md
│  ├─ Nowcasting_Econ-Report-v16.pdf
│  └─ target_industries.md
├─ data/
│  ├─ raw/
│  │  ├─ official/
│  │  │  ├─ isic/
│  │  │  ├─ naics/
│  │  │  ├─ soc/
│  │  │  ├─ onet/
│  │  │  ├─ bls/
│  │  │  └─ esco/
│  │  └─ private_examples/
│  ├─ interim/
│  └─ processed/
├─ outputs/
│  ├─ csv/
│  ├─ parquet/
│  ├─ excel/
│  └─ qa/
├─ sql/
│  ├─ 001_init_schema.sql
│  ├─ 002_indexes.sql
│  └─ 003_views.sql
├─ src/
│  └─ workflow_dataset/
│     ├─ __init__.py
│     ├─ cli.py
│     ├─ settings.py
│     ├─ logging_config.py
│     ├─ utils/
│     │  ├─ __init__.py
│     │  ├─ io.py
│     │  ├─ text.py
│     │  ├─ hashes.py
│     │  ├─ dates.py
│     │  └─ ids.py
│     ├─ models/
│     │  ├─ __init__.py
│     │  ├─ schema.py
│     │  └─ enums.py
│     ├─ ingest/
│     │  ├─ __init__.py
│     │  ├─ base.py
│     │  ├─ isic.py
│     │  ├─ naics.py
│     │  ├─ soc.py
│     │  ├─ onet.py
│     │  ├─ bls.py
│     │  ├─ esco.py
│     │  └─ private_docs.py
│     ├─ normalize/
│     │  ├─ __init__.py
│     │  ├─ taxonomies.py
│     │  ├─ occupations.py
│     │  ├─ tools.py
│     │  └─ provenance.py
│     ├─ map/
│     │  ├─ __init__.py
│     │  ├─ concordance.py
│     │  └─ industry_occupation.py
│     ├─ infer/
│     │  ├─ __init__.py
│     │  ├─ workflow.py
│     │  ├─ pain_points.py
│     │  ├─ kpis.py
│     │  └─ automation.py
│     ├─ validate/
│     │  ├─ __init__.py
│     │  ├─ taxonomy_checks.py
│     │  ├─ provenance_checks.py
│     │  ├─ duplicates.py
│     │  ├─ workflow_checks.py
│     │  └─ excel_checks.py
│     ├─ export/
│     │  ├─ __init__.py
│     │  ├─ csv_export.py
│     │  ├─ parquet_export.py
│     │  ├─ excel_export.py
│     │  └─ qa_report.py
│     └─ db/
│        ├─ __init__.py
│        ├─ sqlite.py
│        └─ repository.py
├─ tests/
│  ├─ test_ids.py
│  ├─ test_taxonomy_integrity.py
│  ├─ test_provenance.py
│  ├─ test_workflow_inference.py
│  └─ test_excel_export.py
└─ scripts/
   ├─ bootstrap_data_dirs.py
   ├─ run_full_build.py
   └─ profile_long_run.py
```

## README.md

```md
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

- `outputs/parquet/`
- `outputs/csv/`
- `outputs/excel/workflow_llm_primary_dataset_v1.xlsx`
- `outputs/qa/build_report.md`

## Build phases

1. Ingest authoritative source files
2. Normalize taxonomies and occupations
3. Map industries to occupations
4. Enrich with tasks, tools, context, labor data
5. Infer workflows, pain points, KPIs, automation candidacy
6. Validate integrity and provenance
7. Export machine-readable and analyst-readable outputs
```

## .gitignore

```gitignore
__pycache__/
*.pyc
.venv/
.env
.pytest_cache/
.mypy_cache/
.DS_Store
outputs/
data/interim/
data/processed/
*.sqlite
*.db
*.log
```

## .env.example

```bash
WORKFLOW_ENV=dev
WORKFLOW_DB_PATH=./workflow_dataset.sqlite
WORKFLOW_LOG_LEVEL=INFO
```

## pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "workflow-llm-dataset"
version = "0.1.0"
description = "Primary-source-first workflow dataset builder for LLM development"
requires-python = ">=3.11"
dependencies = [
  "pandas>=2.2",
  "pyarrow>=15.0",
  "openpyxl>=3.1",
  "xlsxwriter>=3.2",
  "pydantic>=2.6",
  "pyyaml>=6.0",
  "rapidfuzz>=3.9",
  "sqlalchemy>=2.0",
  "typer>=0.12",
  "rich>=13.7",
  "python-dateutil>=2.9",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "mypy>=1.8",
  "ruff>=0.5",
]

[project.scripts]
workflow-dataset = "workflow_dataset.cli:app"

[tool.setuptools.packages.find]
where = ["src"]
```

## Makefile

```make
.PHONY: lint test build qa

lint:
	ruff check src tests scripts
	mypy src

test:
	pytest -q

build:
	python -m workflow_dataset.cli build --config configs/settings.yaml

qa:
	python -m workflow_dataset.cli qa --config configs/settings.yaml
```

## configs/settings.yaml

```yaml
project:
  name: workflow_llm_dataset
  version: v1
  output_excel: outputs/excel/workflow_llm_primary_dataset_v1.xlsx
  output_csv_dir: outputs/csv
  output_parquet_dir: outputs/parquet
  qa_report_path: outputs/qa/build_report.md

runtime:
  timezone: UTC
  long_run_profile: true
  max_workers: 4
  fail_on_missing_provenance: true
  infer_low_confidence_threshold: 0.45
  infer_high_confidence_threshold: 0.8

paths:
  raw_official: data/raw/official
  raw_private: data/raw/private_examples
  interim: data/interim
  processed: data/processed
  prompts: prompts
  context: context
  sqlite_path: workflow_dataset.sqlite
```

## configs/sources.yaml

```yaml
sources:
  - source_name: isic
    source_type: taxonomy
    path: data/raw/official/isic
    required: true
  - source_name: naics
    source_type: taxonomy
    path: data/raw/official/naics
    required: true
  - source_name: soc
    source_type: taxonomy
    path: data/raw/official/soc
    required: true
  - source_name: onet
    source_type: occupation_database
    path: data/raw/official/onet
    required: true
  - source_name: bls
    source_type: labor_market
    path: data/raw/official/bls
    required: true
  - source_name: esco
    source_type: skills_graph
    path: data/raw/official/esco
    required: false
  - source_name: private_examples
    source_type: private_documents
    path: data/raw/private_examples
    required: false
```

## sql/001_init_schema.sql

```sql
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
```

## src/workflow_dataset/settings.py

```python
from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel
import yaml


class ProjectSettings(BaseModel):
    name: str
    version: str
    output_excel: str
    output_csv_dir: str
    output_parquet_dir: str
    qa_report_path: str


class RuntimeSettings(BaseModel):
    timezone: str
    long_run_profile: bool = True
    max_workers: int = 4
    fail_on_missing_provenance: bool = True
    infer_low_confidence_threshold: float = 0.45
    infer_high_confidence_threshold: float = 0.8


class PathSettings(BaseModel):
    raw_official: str
    raw_private: str
    interim: str
    processed: str
    prompts: str
    context: str
    sqlite_path: str


class Settings(BaseModel):
    project: ProjectSettings
    runtime: RuntimeSettings
    paths: PathSettings


def load_settings(config_path: str | Path) -> Settings:
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Settings.model_validate(data)
```

## src/workflow_dataset/cli.py

```python
from __future__ import annotations

import typer
from rich.console import Console

from workflow_dataset.settings import load_settings
from workflow_dataset.ingest.base import run_ingestion
from workflow_dataset.normalize.taxonomies import run_normalization
from workflow_dataset.map.industry_occupation import run_mapping
from workflow_dataset.infer.workflow import run_workflow_inference
from workflow_dataset.export.excel_export import export_excel
from workflow_dataset.export.csv_export import export_csv
from workflow_dataset.export.parquet_export import export_parquet
from workflow_dataset.export.qa_report import build_qa_report

app = typer.Typer()
console = Console()


@app.command()
def build(config: str = "configs/settings.yaml") -> None:
    settings = load_settings(config)
    console.print("[bold]Starting full dataset build[/bold]")
    run_ingestion(settings)
    run_normalization(settings)
    run_mapping(settings)
    run_workflow_inference(settings)
    export_csv(settings)
    export_parquet(settings)
    export_excel(settings)
    build_qa_report(settings)
    console.print("[green]Build complete[/green]")


@app.command()
def qa(config: str = "configs/settings.yaml") -> None:
    settings = load_settings(config)
    build_qa_report(settings)
    console.print("[green]QA report generated[/green]")
```

## src/workflow_dataset/ingest/base.py

```python
from __future__ import annotations

from workflow_dataset.ingest.isic import ingest_isic
from workflow_dataset.ingest.naics import ingest_naics
from workflow_dataset.ingest.soc import ingest_soc
from workflow_dataset.ingest.onet import ingest_onet
from workflow_dataset.ingest.bls import ingest_bls
from workflow_dataset.ingest.esco import ingest_esco
from workflow_dataset.ingest.private_docs import ingest_private_docs


def run_ingestion(settings) -> None:
    ingest_isic(settings)
    ingest_naics(settings)
    ingest_soc(settings)
    ingest_onet(settings)
    ingest_bls(settings)
    ingest_esco(settings)
    ingest_private_docs(settings)
```

## src/workflow_dataset/ingest/onet.py

```python
from __future__ import annotations

from pathlib import Path
import pandas as pd


def ingest_onet(settings) -> None:
    root = Path(settings.paths.raw_official) / "onet"
    out = Path(settings.paths.interim)
    out.mkdir(parents=True, exist_ok=True)

    expected = [
        "Occupation Data.txt",
        "Task Statements.txt",
        "Detailed Work Activities.txt",
        "Tools Used.txt",
        "Technology Skills.txt",
        "Skills.txt",
        "Knowledge.txt",
        "Abilities.txt",
        "Work Context.txt",
    ]

    discovered = {p.name for p in root.glob("*.txt")}
    missing = [name for name in expected if name not in discovered]
    if missing:
        print(f"Warning: missing O*NET files: {missing}")

    for txt in root.glob("*.txt"):
        try:
            df = pd.read_csv(txt, sep="\t", dtype=str)
            df.to_parquet(out / f"onet__{txt.stem.replace(' ', '_').lower()}.parquet", index=False)
        except Exception as exc:
            print(f"Failed to parse {txt.name}: {exc}")
```

## src/workflow_dataset/normalize/taxonomies.py

```python
from __future__ import annotations

from pathlib import Path
import pandas as pd


def run_normalization(settings) -> None:
    run_taxonomy_normalization(settings)
    run_occupation_normalization(settings)


def run_taxonomy_normalization(settings) -> None:
    interim = Path(settings.paths.interim)
    processed = Path(settings.paths.processed)
    processed.mkdir(parents=True, exist_ok=True)
    # placeholder: read interim taxonomy extracts, standardize columns,
    # generate canonical industry tables with stable IDs and parent-child links.


def run_occupation_normalization(settings) -> None:
    # placeholder: normalize O*NET / SOC occupation titles and codes
    pass
```

## src/workflow_dataset/map/industry_occupation.py

```python
from __future__ import annotations


def run_mapping(settings) -> None:
    # Use BLS industry-occupation matrix and official crosswalks first.
    # Only fall back to controlled reviewed inference when an official mapping is absent.
    pass
```

## src/workflow_dataset/infer/workflow.py

```python
from __future__ import annotations


def run_workflow_inference(settings) -> None:
    # Cluster task statements + DWAs + tools/context into ordered workflow units.
    # Mark every non-explicit step as inferred and attach confidence scores.
    pass
```

## src/workflow_dataset/export/excel_export.py

```python
from __future__ import annotations

from pathlib import Path
import pandas as pd


SHEET_ORDER = [
    "README",
    "Taxonomy_ISIC",
    "Taxonomy_NAICS",
    "Taxonomy_SOC",
    "Taxonomy_ONET",
    "Industry_Occupation_Map",
    "Occupations_Master",
    "Tasks",
    "Detailed_Work_Activities",
    "Work_Context",
    "Tools_Technology",
    "Skills_Knowledge_Abilities",
    "Workflow_Steps",
    "Pain_Points",
    "KPI_Library",
    "Labor_Market",
    "Source_Register",
    "Provenance_Row_Map",
    "QA_Issues",
    "Ambiguities_Review",
]


def export_excel(settings) -> None:
    output_path = Path(settings.project.output_excel)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        for sheet in SHEET_ORDER:
            df = pd.DataFrame()
            df.to_excel(writer, sheet_name=sheet, index=False)
            ws = writer.sheets[sheet]
            ws.freeze_panes(1, 0)
```

## scripts/bootstrap_data_dirs.py

```python
from __future__ import annotations

from pathlib import Path

DIRS = [
    "context",
    "data/raw/official/isic",
    "data/raw/official/naics",
    "data/raw/official/soc",
    "data/raw/official/onet",
    "data/raw/official/bls",
    "data/raw/official/esco",
    "data/raw/private_examples",
    "data/interim",
    "data/processed",
    "outputs/csv",
    "outputs/parquet",
    "outputs/excel",
    "outputs/qa",
    "prompts",
    "sql",
]

for d in DIRS:
    Path(d).mkdir(parents=True, exist_ok=True)

print("Directory bootstrap complete")
```

## tests/test_taxonomy_integrity.py

```python
from __future__ import annotations


def test_placeholder() -> None:
    assert True
```

## What Cursor should do first

1. Validate that official source folders exist and are non-empty.
2. Parse O*NET raw files into interim parquet files.
3. Parse taxonomy fi