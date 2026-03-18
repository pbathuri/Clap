"""
Pydantic models for the Initial Setup Analyzer.

Defines: setup session, scan job, artifact family, adapter run, status/progress,
resumable checkpoints, error records, timestamps, scan scope, discovered domains.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SetupStage(str, Enum):
    """Onboarding pipeline stages. Order matters for resumability."""
    BOOTSTRAP = "bootstrap"           # 0: validate config, create session, scan roots
    INVENTORY = "inventory"           # 1: scan files/folders, classify artifact families
    PARSING = "parsing"               # 2: run low-level parsers, extract signals
    INTERPRETATION = "interpretation" # 3: run domain adapters, infer workflow/style
    GRAPH_ENRICHMENT = "graph_enrichment"  # 4: update personal graph
    LLM_PREP = "llm_prep"             # 5: mark artifacts/signals for corpus/SFT
    SUMMARY = "summary"               # 6: produce onboarding summary report


class ArtifactFamily(str, Enum):
    """High-level artifact families for classification."""
    TEXT_DOCUMENT = "text_document"
    SPREADSHEET_TABLE = "spreadsheet_table"
    PROJECT_DIRECTORY = "project_directory"
    MEDIA_ASSET = "media_asset"
    IMAGE_ASSET = "image_asset"
    EXPORTED_DELIVERABLE = "exported_deliverable"
    UNKNOWN = "unknown"


class ScanScope(BaseModel):
    """Scope of a scan: roots, exclusions, limits."""
    root_paths: list[str] = Field(default_factory=list, description="Absolute paths to scan")
    exclude_dirs: list[str] = Field(default_factory=lambda: [".git", "__pycache__", "node_modules", ".venv"])
    max_file_size_bytes: int = Field(default=50 * 1024 * 1024, description="Skip files larger than this (50MB default)")
    max_files_per_scan: int = Field(default=500_000, description="Cap files per full scan")
    allowed_extensions: list[str] = Field(default_factory=list, description="Empty = all")


class DiscoveredDomain(BaseModel):
    """A domain inferred from artifacts (e.g. creative, finance, ops)."""
    domain_id: str = Field(..., description="Stable id, e.g. creative, design, finance")
    label: str = Field(default="", description="Human-readable label")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_count: int = Field(default=0)
    signals: list[str] = Field(default_factory=list, description="Signal keys that contributed")


class SetupSession(BaseModel):
    """A single onboarding setup session (long-running, resumable)."""
    session_id: str = Field(..., description="Stable unique session id")
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")
    current_stage: SetupStage = Field(default=SetupStage.BOOTSTRAP)
    onboarding_mode: str = Field(default="conservative", description="conservative | full_onboarding")
    scan_scope: ScanScope = Field(default_factory=ScanScope)
    enabled_artifact_families: list[ArtifactFamily] = Field(default_factory=lambda: list(ArtifactFamily))
    enabled_adapters: list[str] = Field(default_factory=lambda: ["document", "tabular", "creative", "design", "finance", "ops"])
    max_runtime_hours: float = Field(default=36.0, ge=0.1)
    resume_enabled: bool = Field(default=True)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)


class ScanJob(BaseModel):
    """A single scan job (e.g. one root or one batch). Resumable via checkpoint."""
    job_id: str = Field(...)
    session_id: str = Field(...)
    stage: SetupStage = Field(...)
    root_path: str = Field(default="")
    started_utc: str = Field(default="")
    finished_utc: str = Field(default="")
    status: str = Field(default="pending", description="pending | running | completed | failed | skipped")
    checkpoint_path: str = Field(default="", description="Path or cursor for resume")
    files_scanned: int = Field(default=0)
    artifacts_classified: int = Field(default=0)
    docs_parsed: int = Field(default=0)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdapterRun(BaseModel):
    """Record of one domain adapter run over a set of artifacts."""
    run_id: str = Field(...)
    session_id: str = Field(...)
    adapter_name: str = Field(..., description="e.g. creative, finance")
    stage: SetupStage = Field(default=SetupStage.INTERPRETATION)
    started_utc: str = Field(default="")
    finished_utc: str = Field(default="")
    artifacts_processed: int = Field(default=0)
    signals_emitted: int = Field(default=0)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SetupProgress(BaseModel):
    """Aggregate progress for a setup session (for status reporting)."""
    session_id: str = Field(...)
    updated_utc: str = Field(default="")
    current_stage: SetupStage = Field(...)
    files_scanned: int = Field(default=0)
    artifacts_classified: int = Field(default=0)
    docs_parsed: int = Field(default=0)
    projects_detected: int = Field(default=0)
    style_patterns_extracted: int = Field(default=0)
    graph_nodes_created: int = Field(default=0)
    adapter_errors: int = Field(default=0)
    adapter_skips: int = Field(default=0)
    job_counts: dict[str, int] = Field(default_factory=dict, description="e.g. pending: 1, completed: 5")
    details: dict[str, Any] = Field(default_factory=dict)
