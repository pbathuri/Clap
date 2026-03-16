"""
M23T: Runtime mesh — backend registry, model capability catalog, integration manifests, selection policy.
Local-first; no auto-download; optional backends (Ollama, llama.cpp) opt-in.
"""

from __future__ import annotations

from workflow_dataset.runtime_mesh.backend_registry import (
    list_backend_profiles,
    get_backend_profile,
    get_backend_status,
    load_backend_registry,
)
from workflow_dataset.runtime_mesh.model_catalog import (
    load_model_catalog,
    list_models_by_capability,
    get_model_info,
)
from workflow_dataset.runtime_mesh.integration_registry import (
    load_integration_registry,
    list_integrations,
    get_integration,
)
from workflow_dataset.runtime_mesh.policy import (
    recommend_for_task_class,
    recommend_backend_for_task,
    compatibility_for_model,
)

__all__ = [
    "list_backend_profiles",
    "get_backend_profile",
    "get_backend_status",
    "load_backend_registry",
    "load_model_catalog",
    "list_models_by_capability",
    "get_model_info",
    "load_integration_registry",
    "list_integrations",
    "get_integration",
    "recommend_for_task_class",
    "recommend_backend_for_task",
    "compatibility_for_model",
]
