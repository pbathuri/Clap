"""
M23T: Integration manifest registry — external tools (OpenClaw, coding-agent, IDE, automation, RAG).
Manifests: id, local/remote, job categories, required runtime/model classes, approvals, security notes, enable state.
Registry + compatibility only; no full implementation of every integration.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY_DIR = "data/local/runtime"
INTEGRATION_MANIFESTS_FILENAME = "integration_manifests.json"


@dataclass
class IntegrationManifest:
    """Single integration manifest."""

    integration_id: str
    local: bool = True
    optional_remote: bool = False
    supported_job_categories: list[str] = field(default_factory=list)
    required_runtime_classes: list[str] = field(default_factory=list)  # e.g. ollama, repo_local
    required_model_classes: list[str] = field(default_factory=list)  # e.g. coding_agentic_coding
    required_approvals: list[str] = field(default_factory=list)
    supported_adapters: list[str] = field(default_factory=list)
    security_notes: str = ""
    install_status: str = "unknown"  # installed | not_installed | optional
    enabled: bool = False


def _default_manifests() -> list[dict[str, Any]]:
    """Built-in integration manifests (reference/compatibility only)."""
    return [
        {
            "integration_id": "openclaw",
            "local": True,
            "optional_remote": False,
            "supported_job_categories": ["desktop_assistant", "orchestration"],
            "required_runtime_classes": ["ollama", "repo_local"],
            "required_model_classes": ["general_chat_reasoning", "desktop_assistant_suitable"],
            "required_approvals": ["optional_wrapper"],
            "supported_adapters": ["reference_only"],
            "security_notes": "Reference-only in this repo; no live import.",
            "install_status": "optional",
            "enabled": False,
        },
        {
            "integration_id": "coding_agent",
            "local": True,
            "optional_remote": False,
            "supported_job_categories": ["codebase_task", "coding_agent"],
            "required_runtime_classes": ["ollama", "repo_local", "llama_cpp"],
            "required_model_classes": ["coding_agentic_coding"],
            "required_approvals": [],
            "supported_adapters": ["ide", "cli"],
            "security_notes": "Local execution only when enabled.",
            "install_status": "optional",
            "enabled": False,
        },
        {
            "integration_id": "ide_editor",
            "local": True,
            "optional_remote": False,
            "supported_job_categories": ["codebase_task", "editor"],
            "required_runtime_classes": ["ollama", "repo_local"],
            "required_model_classes": ["coding_agentic_coding"],
            "required_approvals": [],
            "supported_adapters": ["cursor", "vscode"],
            "security_notes": "Metadata only; no auto-enable.",
            "install_status": "optional",
            "enabled": False,
        },
        {
            "integration_id": "notebook_rag",
            "local": True,
            "optional_remote": False,
            "supported_job_categories": ["notebook", "chat", "rag"],
            "required_runtime_classes": ["ollama", "repo_local"],
            "required_model_classes": ["general_chat_reasoning", "embeddings"],
            "required_approvals": [],
            "supported_adapters": ["notebook", "retrieval"],
            "security_notes": "Local retrieval and chat.",
            "install_status": "optional",
            "enabled": False,
        },
    ]


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root()
    except Exception:
        return Path.cwd()


def load_integration_registry(repo_root: Path | str | None = None) -> list[IntegrationManifest]:
    """Load integration manifests from data/local/runtime/integration_manifests.json or built-in."""
    root = _repo_root(repo_root)
    registry_dir = root / DEFAULT_REGISTRY_DIR
    path = registry_dir / INTEGRATION_MANIFESTS_FILENAME
    if path.exists() and path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entries = data.get("integrations", data) if isinstance(data, dict) else data
            if not isinstance(entries, list):
                entries = _default_manifests()
        except Exception:
            entries = _default_manifests()
    else:
        entries = _default_manifests()

    out: list[IntegrationManifest] = []
    for e in entries:
        if isinstance(e, dict):
            out.append(IntegrationManifest(
                integration_id=str(e.get("integration_id", "")),
                local=bool(e.get("local", True)),
                optional_remote=bool(e.get("optional_remote", False)),
                supported_job_categories=list(e.get("supported_job_categories", [])),
                required_runtime_classes=list(e.get("required_runtime_classes", [])),
                required_model_classes=list(e.get("required_model_classes", [])),
                required_approvals=list(e.get("required_approvals", [])),
                supported_adapters=list(e.get("supported_adapters", [])),
                security_notes=str(e.get("security_notes", "")),
                install_status=str(e.get("install_status", "unknown")),
                enabled=bool(e.get("enabled", False)),
            ))
    return out


def list_integrations(repo_root: Path | str | None = None) -> list[IntegrationManifest]:
    """List all integration manifests."""
    return load_integration_registry(repo_root)


def get_integration(integration_id: str, repo_root: Path | str | None = None) -> IntegrationManifest | None:
    """Get manifest by integration id."""
    for m in load_integration_registry(repo_root):
        if m.integration_id == integration_id:
            return m
    return None


def _manifest_to_dict(m: IntegrationManifest) -> dict[str, Any]:
    """Serialize IntegrationManifest to dict for JSON."""
    return {
        "integration_id": m.integration_id,
        "local": m.local,
        "optional_remote": m.optional_remote,
        "supported_job_categories": m.supported_job_categories,
        "required_runtime_classes": m.required_runtime_classes,
        "required_model_classes": m.required_model_classes,
        "required_approvals": m.required_approvals,
        "supported_adapters": m.supported_adapters,
        "security_notes": m.security_notes,
        "install_status": m.install_status,
        "enabled": m.enabled,
    }


def set_integration_enabled(
    integration_id: str,
    enabled: bool,
    repo_root: Path | str | None = None,
) -> bool:
    """
    Set enabled flag for an integration and persist to data/local/runtime/integration_manifests.json.
    Returns True if the integration was found and file was written.
    """
    root = _repo_root(repo_root)
    manifests = load_integration_registry(root)
    found = False
    for m in manifests:
        if m.integration_id == integration_id:
            m.enabled = enabled
            found = True
            break
    if not found:
        return False
    registry_dir = root / DEFAULT_REGISTRY_DIR
    registry_dir.mkdir(parents=True, exist_ok=True)
    path = registry_dir / INTEGRATION_MANIFESTS_FILENAME
    data = {"integrations": [_manifest_to_dict(m) for m in manifests]}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return True
