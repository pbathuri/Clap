"""
M24A: External capability source registry — unified view from integrations, backends, model catalog.
Load/merge from existing runtime_mesh data; optional override file for activation status.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.external_capability.schema import (
    ExternalCapabilitySource,
    SOURCE_CATEGORIES,
    ACTIVATION_STATUSES,
)

DEFAULT_REGISTRY_DIR = "data/local/runtime"
EXTERNAL_SOURCES_FILENAME = "external_capability_sources.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _integration_to_source(manifest: Any) -> ExternalCapabilitySource:
    """Map IntegrationManifest to ExternalCapabilitySource."""
    cat = "openclaw" if manifest.integration_id == "openclaw" else (
        "coding_agent" if manifest.integration_id == "coding_agent" else (
            "ide_editor" if manifest.integration_id == "ide_editor" else "automation"
        )
    )
    status = "configured" if manifest.enabled else ("available" if manifest.install_status == "installed" else manifest.install_status or "unknown")
    return ExternalCapabilitySource(
        source_id=manifest.integration_id,
        category=cat,
        local=manifest.local,
        optional_remote=manifest.optional_remote,
        install_prerequisites=[],
        security_notes=manifest.security_notes or "",
        approval_notes="; ".join(manifest.required_approvals) if manifest.required_approvals else "",
        supported_task_classes=manifest.supported_job_categories,
        supported_domain_pack_ids=[],
        supported_tiers=["dev_full", "local_standard"],
        estimated_resource="medium",
        activation_status=status,
        enabled=manifest.enabled,
        display_name=manifest.integration_id.replace("_", " ").title(),
        notes="",
        rollback_notes="Set enabled=false in integration manifest or run: capabilities external disable --source " + manifest.integration_id,
    )


def _backend_to_source(profile: Any) -> ExternalCapabilitySource:
    """Map BackendProfile to ExternalCapabilitySource (runtime backend as a 'source')."""
    cat = "ollama_model" if profile.backend_id == "ollama" else "optional_model_dataset"
    if profile.backend_id == "llama_cpp":
        cat = "optional_model_dataset"
    if profile.backend_id == "repo_local":
        cat = "optional_model_dataset"
    return ExternalCapabilitySource(
        source_id=f"backend_{profile.backend_id}",
        category=cat,
        local=profile.local,
        optional_remote=profile.optional_remote,
        install_prerequisites=list(profile.install_prerequisites) if hasattr(profile, "install_prerequisites") else [],
        trust_notes=getattr(profile, "risk_trust_notes", "") or "",
        security_notes="",
        supported_task_classes=[],
        supported_domain_pack_ids=[],
        supported_tiers=["dev_full", "local_standard", "constrained_edge"],
        estimated_resource="medium" if profile.backend_id == "ollama" else "low",
        activation_status=profile.status if hasattr(profile, "status") else "unknown",
        enabled=profile.status in ("available", "configured"),
        display_name=f"Backend: {profile.backend_id}",
        notes=getattr(profile, "notes", "") or "",
        machine_requirements=list(getattr(profile, "hardware_profile_requirements", []) or []),
        rollback_notes="Disable via config or integration manifest if applicable.",
    )


def _model_to_source(model: Any, backend_status: str) -> ExternalCapabilitySource:
    """Map ModelEntry to ExternalCapabilitySource (Ollama/repo_local model)."""
    safe_id = "".join(c if c.isalnum() or c in "-_." else "_" for c in model.model_id)
    source_id = f"ollama_{safe_id}" if getattr(model, "backend_family", "ollama") == "ollama" else f"model_{safe_id}"
    return ExternalCapabilitySource(
        source_id=source_id,
        category="ollama_model" if getattr(model, "backend_family", "ollama") == "ollama" else "optional_model_dataset",
        local=True,
        optional_remote=False,
        install_prerequisites=["Ollama installed", f"Pull model: {model.model_id}"],
        supported_task_classes=list(getattr(model, "recommended_usage", [])),
        supported_domain_pack_ids=[],
        supported_tiers=["dev_full", "local_standard"],
        estimated_resource="high" if (getattr(model, "context_size", 0) or 0) > 100000 else "medium",
        activation_status=backend_status,
        enabled=False,
        display_name=model.model_id,
        notes=getattr(model, "notes", "") or "",
        machine_requirements=["ollama_running"] if getattr(model, "backend_family", "ollama") == "ollama" else [],
        rollback_notes="Remove model from config or leave unused; no auto-remove.",
    )


def _load_override_sources(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Load optional override file: source_id -> partial attributes (e.g. activation_status, enabled)."""
    path = repo_root / DEFAULT_REGISTRY_DIR / EXTERNAL_SOURCES_FILENAME
    if not path.exists() or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("sources", data) if isinstance(data, dict) else data
        if not isinstance(entries, list):
            return {}
        return {str(e.get("source_id", "")): e for e in entries if isinstance(e, dict) and e.get("source_id")}
    except Exception:
        return {}


def load_external_sources(repo_root: Path | str | None = None) -> list[ExternalCapabilitySource]:
    """
    Build unified external capability source list from:
    - integration_registry (OpenClaw, coding_agent, ide_editor, notebook_rag)
    - backend_registry (ollama, repo_local, llama_cpp as backend_*)
    - model_catalog (each model as ollama_<model_id> or model_<model_id>)
    Optional override file: data/local/runtime/external_capability_sources.json (sources[].source_id + overrides).
    """
    root = _repo_root(repo_root)
    seen: set[str] = set()
    out: list[ExternalCapabilitySource] = []
    overrides = _load_override_sources(root)

    # 1. Integrations
    try:
        from workflow_dataset.runtime_mesh.integration_registry import load_integration_registry
        for m in load_integration_registry(root):
            src = _integration_to_source(m)
            if src.source_id in overrides:
                o = overrides[src.source_id]
                for k, v in o.items():
                    if k in ("activation_status", "enabled", "display_name", "notes", "supported_tiers"):
                        setattr(src, k, v)
            if src.source_id not in seen:
                seen.add(src.source_id)
                out.append(src)
    except Exception:
        pass

    # 2. Backends (as capability sources)
    try:
        from workflow_dataset.runtime_mesh.backend_registry import load_backend_registry
        for p in load_backend_registry(root):
            src = _backend_to_source(p)
            if src.source_id in overrides:
                o = overrides[src.source_id]
                for k, v in o.items():
                    if hasattr(src, k):
                        setattr(src, k, v)
            if src.source_id not in seen:
                seen.add(src.source_id)
                out.append(src)
    except Exception:
        pass

    # 3. Model catalog (Ollama / repo_local models)
    try:
        from workflow_dataset.runtime_mesh.model_catalog import load_model_catalog
        from workflow_dataset.runtime_mesh.backend_registry import get_backend_status
        catalog = load_model_catalog(root)
        ollama_status = get_backend_status("ollama", root)
        repo_status = get_backend_status("repo_local", root)
        for model in catalog:
            bf = getattr(model, "backend_family", "ollama")
            st = ollama_status if bf == "ollama" else repo_status
            src = _model_to_source(model, st)
            if src.source_id in overrides:
                o = overrides[src.source_id]
                for k, v in o.items():
                    if hasattr(src, k):
                        setattr(src, k, v)
            if src.source_id not in seen:
                seen.add(src.source_id)
                out.append(src)
    except Exception:
        pass

    return out


def list_external_sources(repo_root: Path | str | None = None) -> list[ExternalCapabilitySource]:
    """List all external capability sources."""
    return load_external_sources(repo_root)


def get_external_source(source_id: str, repo_root: Path | str | None = None) -> ExternalCapabilitySource | None:
    """Get one external capability source by source_id."""
    for s in load_external_sources(repo_root):
        if s.source_id == source_id:
            return s
    return None
