from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel, Field
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
    exclude_dirs: list[str] = [".git", "__pycache__",
                               "node_modules", ".venv", ".tox", "venv"]
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


class SetupSettings(BaseModel):
    """Initial setup/onboarding analyzer. Local-first; defaults privacy-safe and conservative."""
    setup_enabled: bool = False
    setup_mode: str = "conservative"  # conservative | full_onboarding
    setup_scan_roots: list[str] = []
    setup_max_runtime_hours: float = 36.0
    setup_resume_enabled: bool = True
    setup_stage_controls: list[str] = []  # empty = all stages
    allow_raw_text_parsing: bool = False  # True when full_onboarding and user opted in
    allow_raw_text_persistence: bool = False  # persist raw text locally; requires full_onboarding + explicit
    allow_llm_corpus_from_parsed_signals: bool = False
    allow_llm_corpus_from_raw_text: bool = False  # when allow_raw_text_persistence and user allows
    allowed_extensions: list[str] = []  # empty = all supported
    max_file_size: int = 50 * 1024 * 1024  # 50MB (max_file_size_mb in yaml converted if needed)
    max_file_size_mb: float | None = None  # optional; overrides max_file_size when set
    enabled_artifact_families: list[str] = []  # empty = all
    enabled_domain_adapters: list[str] = ["document", "tabular", "creative", "design", "finance", "ops"]
    enable_media_metadata: bool = True
    enable_style_signature_extraction: bool = True
    include_media_metadata: bool = True  # legacy alias
    include_raw_text_snippets: bool = False  # legacy; prefer allow_raw_text_parsing
    exclude_paths: list[str] = [".git", "__pycache__", "node_modules", ".venv"]
    low_power_mode: bool = False
    setup_dir: str = "data/local/setup"
    parsed_artifacts_dir: str = "data/local/parsed_artifacts"
    style_signals_dir: str = "data/local/style_signals"
    style_profiles_dir: str = "data/local/style_profiles"
    setup_reports_dir: str = "data/local/setup_reports"
    suggestions_dir: str = "data/local/suggestions"
    draft_structures_dir: str = "data/local/draft_structures"
    persist_style_signals: bool = True
    allow_personal_corpus_from_setup: bool = False
    allow_personal_sft_from_setup: bool = False
    allow_raw_text_for_personal_corpus: bool = False
    allow_raw_text_for_personal_sft: bool = False
    max_media_metadata_files: int = 10_000


class AgentLoopSettings(BaseModel):
    """M6 assistive agent loop: retrieval-backed, graph-grounded, no execution."""
    agent_loop_enabled: bool = True
    agent_loop_default_use_retrieval: bool = True
    agent_loop_default_use_llm: bool = False
    agent_loop_max_context_docs: int = 5
    agent_loop_project_scope_default: str = ""
    agent_loop_save_sessions: bool = True
    agent_sessions_dir: str = "data/local/agent_sessions"
    agent_responses_dir: str = "data/local/agent_responses"


class MaterializationSettings(BaseModel):
    """M7 sandboxed artifact materialization. Local workspace only; no real filesystem writes."""
    materialization_enabled: bool = True
    materialization_default_use_llm: bool = False
    materialization_workspace_root: str = "data/local/workspaces"
    materialization_allow_csv: bool = True
    materialization_allow_markdown: bool = True
    materialization_allow_json: bool = True
    materialization_allow_xlsx: bool = False
    materialization_allow_folder_scaffolds: bool = True
    materialization_save_manifests: bool = True
    materialization_graph_persistence: bool = True
    materialization_preview_enabled: bool = True


class ApplySettings(BaseModel):
    """M8 user-approved apply-to-project. Explicit confirm; local-only; backups and rollback."""
    apply_enabled: bool = False
    apply_require_confirm: bool = True
    apply_default_dry_run: bool = True
    apply_allow_overwrite: bool = False
    apply_create_backups: bool = True
    apply_allowed_target_roots: list[str] = Field(default_factory=list)
    apply_backup_root: str = "data/local/applies"
    apply_manifest_root: str = "data/local/applies"
    apply_graph_persistence: bool = True
    apply_rollback_enabled: bool = True


class GenerationSettings(BaseModel):
    """M10/M11 sandboxed multimodal generation. Local-only; scaffold-first; backend execution config-gated."""
    generation_enabled: bool = True
    generation_default_use_llm: bool = False
    generation_workspace_root: str = "data/local/generation"
    generation_allow_style_packs: bool = True
    generation_allow_prompt_packs: bool = True
    generation_allow_asset_plans: bool = True
    generation_enable_demo_backend: bool = False
    generation_enable_document_backend: bool = False
    generation_enable_image_demo_backend: bool = False
    generation_default_backend: str = "mock"
    generation_backend_timeout_sec: int = 300
    generation_backend_allow_llm: bool = False
    generation_backend_fallback_enabled: bool = True
    generation_backend_registry: list[str] = Field(default_factory=lambda: ["mock"])
    generation_graph_persistence: bool = True
    # M12 review/refinement/adoption
    generation_review_enabled: bool = True
    generation_refinement_enabled: bool = True
    generation_refinement_default_use_llm: bool = False
    generation_variant_retention: int = 50
    generation_adoption_bridge_enabled: bool = True
    generation_preview_enabled: bool = True


class OutputAdaptersSettings(BaseModel):
    """M13/M14 toolchain-native output adapters. Sandbox-first; no real project writes without apply."""
    output_adapters_enabled: bool = True
    output_adapter_registry: list[str] = Field(default_factory=lambda: ["spreadsheet", "creative_package", "design_package", "ops_handoff"])
    output_adapter_allow_xlsx: bool = False
    output_adapter_bundle_root: str = "data/local/bundles"
    output_adapter_graph_persistence: bool = True
    output_adapter_preview_enabled: bool = True
    # M14 content population
    output_adapter_population_enabled: bool = True
    output_adapter_population_use_refined_artifacts: bool = True
    output_adapter_population_use_generated_artifacts: bool = True
    output_adapter_population_max_rows: int = 1000
    output_adapter_population_max_sections: int = 50
    output_adapter_population_require_provenance: bool = False


class Settings(BaseModel):
    project: ProjectSettings
    runtime: RuntimeSettings
    paths: PathSettings
    agent: AgentSettings | None = None
    setup: SetupSettings | None = None
    agent_loop: AgentLoopSettings | None = None
    materialization: MaterializationSettings | None = None
    apply: ApplySettings | None = None
    generation: GenerationSettings | None = None
    output_adapters: OutputAdaptersSettings | None = None


def load_settings(config_path: str | Path) -> Settings:
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        data = {}
    if "agent" not in data:
        data["agent"] = {}
    if "agent" in data and isinstance(data["agent"], dict) and "file_observer" not in data["agent"]:
        data["agent"]["file_observer"] = {}
    if "setup" not in data:
        data["setup"] = {}
    if "agent_loop" not in data:
        data["agent_loop"] = {}
    if "materialization" not in data:
        data["materialization"] = {}
    if "apply" not in data:
        data["apply"] = {}
    if "generation" not in data:
        data["generation"] = {}
    if "output_adapters" not in data:
        data["output_adapters"] = {}
    # Convert max_file_size_mb to max_file_size (bytes) when present
    if isinstance(data.get("setup"), dict) and data["setup"].get("max_file_size_mb") is not None:
        mb = float(data["setup"]["max_file_size_mb"])
        data["setup"]["max_file_size"] = int(mb * 1024 * 1024)
    return Settings.model_validate(data)
