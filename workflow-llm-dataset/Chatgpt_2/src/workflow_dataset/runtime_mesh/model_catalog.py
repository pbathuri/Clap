"""
M23T: Model capability catalog — by role/capability class, not every model in product logic.
Seed from user-provided Ollama model catalog; tags, compatibility filters, recommended usage classes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Capability classes (catalog classes)
CAPABILITY_CLASSES = (
    "general_chat_reasoning",
    "coding_agentic_coding",
    "embeddings",
    "vision_ocr",
    "safety_guardrail",
    "lightweight_edge",
    "high_context",
    "multilingual_translation",
)

DEFAULT_REGISTRY_DIR = "data/local/runtime"
MODEL_CATALOG_FILENAME = "model_catalog.json"


@dataclass
class ModelEntry:
    """Single model entry in the capability catalog. M42A: task_families, trust/safe flags, fallback, provenance."""

    model_id: str
    backend_family: str = "ollama"  # ollama, repo_local, llama_cpp
    capability_classes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    recommended_usage: list[str] = field(default_factory=list)  # e.g. desktop_copilot, codebase_task
    context_size: int | None = None
    notes: str = ""
    # M42A–M42D: task-aware routing and safe-use boundaries
    task_families: list[str] = field(default_factory=list)  # planning, summarization, review, suggestion, etc.
    tool_use: bool = False
    latency_tier: str = ""  # e.g. low, medium, high
    hardware_assumptions: list[str] = field(default_factory=list)  # e.g. gpu, 8gb_ram
    trust_notes: str = ""
    production_safe: bool = True
    experimental_safe: bool = True
    fallback_model_id: str = ""  # preferred fallback when this model unavailable
    version: str = ""
    provenance: str = ""  # e.g. ollama/default, repo_local/config


def _default_seed_catalog() -> list[dict[str, Any]]:
    """Seed catalog: representative models by capability class (Ollama-style names). M42: task_families, safe flags, fallback."""
    return [
        {"model_id": "llama3.2", "backend_family": "ollama", "capability_classes": ["general_chat_reasoning", "lightweight_edge"], "tags": ["chat"], "recommended_usage": ["desktop_copilot", "inbox"], "context_size": 128000, "notes": "General chat; edge-friendly.", "task_families": ["planning", "summarization", "suggestion"], "production_safe": True, "experimental_safe": True, "fallback_model_id": "local/small"},
        {"model_id": "qwen2.5-coder", "backend_family": "ollama", "capability_classes": ["coding_agentic_coding"], "tags": ["code"], "recommended_usage": ["codebase_task", "coding_agent"], "context_size": 32768, "notes": "Coding and agentic tasks.", "task_families": ["suggestion", "vertical_workflow"], "production_safe": True, "experimental_safe": True, "fallback_model_id": ""},
        {"model_id": "qwen3-coder-next", "backend_family": "ollama", "capability_classes": ["coding_agentic_coding", "high_context"], "tags": ["code"], "recommended_usage": ["codebase_task", "coding_agent"], "context_size": 128000, "notes": "Coding; high context.", "task_families": ["suggestion", "vertical_workflow", "adaptation_comparison"], "production_safe": True, "experimental_safe": True, "fallback_model_id": "qwen2.5-coder"},
        {"model_id": "nomic-embed-text", "backend_family": "ollama", "capability_classes": ["embeddings"], "tags": ["embedding"], "recommended_usage": ["local_retrieval"], "notes": "Embeddings for local retrieval.", "task_families": [], "production_safe": True, "experimental_safe": True},
        {"model_id": "llava", "backend_family": "ollama", "capability_classes": ["vision_ocr"], "tags": ["vision"], "recommended_usage": ["document_workflow", "vision"], "notes": "Vision / image understanding.", "task_families": ["vertical_workflow"], "production_safe": True, "experimental_safe": True},
        {"model_id": "local/small", "backend_family": "repo_local", "capability_classes": ["general_chat_reasoning", "lightweight_edge"], "tags": ["local"], "recommended_usage": ["desktop_copilot", "inbox"], "notes": "Pack-recommended local small profile.", "task_families": ["planning", "summarization", "suggestion"], "production_safe": True, "experimental_safe": True, "fallback_model_id": ""},
    ]


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root()
    except Exception:
        return Path.cwd()


def load_model_catalog(repo_root: Path | str | None = None) -> list[ModelEntry]:
    """Load model catalog from data/local/runtime/model_catalog.json or built-in seed."""
    root = _repo_root(repo_root)
    registry_dir = root / DEFAULT_REGISTRY_DIR
    path = registry_dir / MODEL_CATALOG_FILENAME
    if path.exists() and path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entries_data = data.get("models", data) if isinstance(data, dict) else data
            if not isinstance(entries_data, list):
                entries_data = _default_seed_catalog()
        except Exception:
            entries_data = _default_seed_catalog()
    else:
        entries_data = _default_seed_catalog()

    out: list[ModelEntry] = []
    for e in entries_data:
        if isinstance(e, dict):
            out.append(ModelEntry(
                model_id=str(e.get("model_id", "")),
                backend_family=str(e.get("backend_family", "ollama")),
                capability_classes=list(e.get("capability_classes", [])),
                tags=list(e.get("tags", [])),
                recommended_usage=list(e.get("recommended_usage", [])),
                context_size=e.get("context_size"),
                notes=str(e.get("notes", "")),
                task_families=list(e.get("task_families", [])),
                tool_use=bool(e.get("tool_use", False)),
                latency_tier=str(e.get("latency_tier", "")),
                hardware_assumptions=list(e.get("hardware_assumptions", [])),
                trust_notes=str(e.get("trust_notes", "")),
                production_safe=bool(e.get("production_safe", True)),
                experimental_safe=bool(e.get("experimental_safe", True)),
                fallback_model_id=str(e.get("fallback_model_id", "")),
                version=str(e.get("version", "")),
                provenance=str(e.get("provenance", "")),
            ))
    return out


def list_models_by_capability(
    capability_class: str,
    repo_root: Path | str | None = None,
) -> list[ModelEntry]:
    """List models that have the given capability class."""
    catalog = load_model_catalog(repo_root)
    return [m for m in catalog if capability_class in m.capability_classes]


def get_model_info(model_id: str, repo_root: Path | str | None = None) -> ModelEntry | None:
    """Get catalog entry for a model by id."""
    for m in load_model_catalog(repo_root):
        if m.model_id == model_id:
            return m
    return None
