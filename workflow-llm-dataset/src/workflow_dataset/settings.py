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
