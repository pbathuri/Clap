"""
M24A: Pull/install/enable plans — explicit local plans only; no execution, no blind downloads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.external_capability.registry import get_external_source
from workflow_dataset.external_capability.schema import ExternalCapabilitySource


def build_activation_plan(
    source_id: str,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """
    Build an explicit activation plan for the given source (steps only; no execution).
    Returns list of steps: [{ "action": str, "detail": str, "safe_local": bool }].
    """
    source = get_external_source(source_id, repo_root)
    if not source:
        return [{"action": "unknown", "detail": f"Source '{source_id}' not found in registry.", "safe_local": False}]

    steps: list[dict[str, Any]] = []

    if source.category == "ollama_model":
        # e.g. ollama_qwen2.5-coder -> pull model via Ollama (plan only)
        model_part = source_id.replace("ollama_", "", 1) if source_id.startswith("ollama_") else source_id
        steps.append({
            "action": "ensure_ollama_running",
            "detail": "Ensure Ollama is installed and running (e.g. http://127.0.0.1:11434).",
            "safe_local": True,
        })
        steps.append({
            "action": "pull_model",
            "detail": f"Pull model '{model_part}' via Ollama (e.g. ollama pull {model_part}). Plan only — no auto-download.",
            "safe_local": True,
        })
        steps.append({
            "action": "enable_in_config",
            "detail": "Add or confirm model in configs/settings.yaml or runtime model_catalog for this capability.",
            "safe_local": True,
        })

    elif source_id == "openclaw":
        steps.append({
            "action": "enable_openclaw_compatibility",
            "detail": "Enable OpenClaw compatibility (reference-only in this repo; no live import). Update integration manifest if desired.",
            "safe_local": True,
        })

    elif source_id == "coding_agent":
        steps.append({
            "action": "prepare_coding_agent",
            "detail": "Prepare coding-agent integration: ensure Ollama or repo_local backend with coding_agentic_coding model.",
            "safe_local": True,
        })
        for pr in (source.install_prerequisites or []):
            steps.append({"action": "prerequisite", "detail": pr, "safe_local": True})

    elif source_id == "ide_editor":
        steps.append({
            "action": "add_ide_metadata",
            "detail": "Add IDE/editor integration metadata; no auto-enable. Configure adapter (cursor, vscode) if desired.",
            "safe_local": True,
        })

    elif source_id.startswith("backend_"):
        backend = source_id.replace("backend_", "", 1)
        steps.append({
            "action": "configure_backend",
            "detail": f"Configure backend '{backend}': {'; '.join(source.install_prerequisites or ['see backend registry'])}.",
            "safe_local": True,
        })

    else:
        for pr in (source.install_prerequisites or []):
            steps.append({"action": "prerequisite", "detail": pr, "safe_local": True})
        steps.append({
            "action": "enable_source",
            "detail": f"Enable source '{source_id}' via local config or approval. No silent enablement.",
            "safe_local": True,
        })

    return steps
