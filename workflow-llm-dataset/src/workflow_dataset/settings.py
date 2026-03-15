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
    event_log_dir: str = "data/local/event_log"
    graph_store_path: str = "data/local/work_graph.sqlite"
    audit_log_path: str = "data/local/agent_audit.sqlite"


class FileObserverSettings(BaseModel):
    """File metadata observer (Tier 1). Safe defaults: no roots, low limit."""
    root_paths: list[str] = []
    max_files_per_scan: int = 10_000
    exclude_dirs: list[str] = [".git", "__pycache__", "node_modules", ".venv", ".tox", "venv"]
    allowed_extensions: list[str] = []  # empty = all
    graph_update_enabled: bool = True


class AgentSettings(BaseModel):
    """Personal agent: observation and execution (local-first). Defaults: observe off, sync off, simulate."""
    observation_enabled: bool = False
    observation_tier: int = 1
    allowed_observation_sources: list[str] = []
    privacy_mode: str = "local_only"
    sync_enabled: bool = False
    execution_mode: str = "simulate"
    hardware_profile: str = "pi5"
    local_model_profile: str = "small"
    vector_store_path: str = "data/local/vector_store"
    sandbox_enabled: bool = True
    file_observer: FileObserverSettings | None = None


class Settings(BaseModel):
    project: ProjectSettings
    runtime: RuntimeSettings
    paths: PathSettings
    agent: AgentSettings | None = None


def load_settings(config_path: str | Path) -> Settings:
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        data = {}
    if "agent" not in data:
        data["agent"] = {}
    if "agent" in data and isinstance(data["agent"], dict) and "file_observer" not in data["agent"]:
        data["agent"]["file_observer"] = {}
    return Settings.model_validate(data)
