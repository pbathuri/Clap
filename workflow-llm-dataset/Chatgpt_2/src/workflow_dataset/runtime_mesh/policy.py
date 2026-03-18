"""
M23T: Runtime selection policy — which backend/model/integrations for task class and profile; what is missing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.runtime_mesh.backend_registry import (
    load_backend_registry,
    get_backend_profile,
)
from workflow_dataset.runtime_mesh.model_catalog import (
    load_model_catalog,
    list_models_by_capability,
    get_model_info,
)
from workflow_dataset.runtime_mesh.integration_registry import load_integration_registry

# Task classes the policy can recommend for
TASK_CLASSES = (
    "desktop_copilot",
    "inbox",
    "codebase_task",
    "coding_agent",
    "local_retrieval",
    "document_workflow",
    "vision",
    "plan_run_review",
    "lightweight_edge",
)

# Map task_class -> (capability_class, backend_preference)
TASK_CLASS_POLICY: dict[str, dict[str, Any]] = {
    "desktop_copilot": {"capability": "general_chat_reasoning", "backend_preference": ["ollama", "repo_local"], "suitable": "desktop_assistant_suitable"},
    "inbox": {"capability": "lightweight_edge", "backend_preference": ["ollama", "repo_local"], "suitable": "desktop_assistant_suitable"},
    "codebase_task": {"capability": "coding_agentic_coding", "backend_preference": ["ollama", "repo_local", "llama_cpp"], "suitable": "coding_agent_suitable"},
    "coding_agent": {"capability": "coding_agentic_coding", "backend_preference": ["ollama", "repo_local"], "suitable": "coding_agent_suitable"},
    "local_retrieval": {"capability": "embeddings", "backend_preference": ["ollama", "repo_local"], "suitable": None},
    "document_workflow": {"capability": "vision_ocr", "backend_preference": ["ollama", "repo_local"], "suitable": None},
    "vision": {"capability": "vision_ocr", "backend_preference": ["ollama"], "suitable": None},
    "plan_run_review": {"capability": "safety_guardrail", "backend_preference": ["ollama", "repo_local"], "suitable": None},
    "lightweight_edge": {"capability": "lightweight_edge", "backend_preference": ["ollama", "repo_local"], "suitable": None},
}


def _repo_root(repo_root: Path | str | None) -> Path | None:
    if repo_root is None or (isinstance(repo_root, str) and not repo_root.strip()):
        return None
    return Path(repo_root).resolve()


def recommend_for_task_class(
    task_class: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Recommend backend, model class, and integrations for a task class.
    Returns: backend_id, backend_status, model_class, model_ids[], integrations_available[], missing[], reason.
    """
    root = _repo_root(repo_root)
    backends = load_backend_registry(root)
    catalog = load_model_catalog(root)
    integrations = load_integration_registry(root)

    policy = TASK_CLASS_POLICY.get(task_class)
    if not policy:
        return {
            "task_class": task_class,
            "backend_id": None,
            "backend_status": None,
            "model_class": None,
            "model_ids": [],
            "integrations_available": [],
            "missing": [f"Unknown task_class: {task_class}"],
            "reason": "Unsupported task class.",
        }

    capability = policy.get("capability")
    backend_preference = policy.get("backend_preference") or []
    suitable_attr = policy.get("suitable")

    # Pick first available/configured backend from preference
    backend_id = None
    backend_status = None
    for bid in backend_preference:
        prof = get_backend_profile(bid, root)
        if not prof:
            continue
        if suitable_attr and not getattr(prof, suitable_attr, False):
            continue
        if prof.status in ("available", "configured"):
            backend_id = prof.backend_id
            backend_status = prof.status
            break
        if backend_status is None:
            backend_status = prof.status

    if backend_id is None and backends:
        for b in backends:
            if b.backend_id in backend_preference:
                backend_id = b.backend_id
                backend_status = b.status
                break

    # Models with this capability
    model_ids = [m.model_id for m in catalog if capability in m.capability_classes]

    # Integrations that support this task class
    job_key = task_class
    integrations_available = [
        i.integration_id for i in integrations
        if job_key in i.supported_job_categories
    ]

    missing: list[str] = []
    if not backend_id:
        missing.append(f"No backend available for task_class={task_class} (preference: {backend_preference})")
    elif backend_status == "missing":
        missing.append(f"Backend {backend_id} is missing (install or enable).")
    elif backend_status == "unsupported":
        missing.append(f"Backend {backend_id} is unsupported in this build.")
    if not model_ids:
        missing.append(f"No models in catalog for capability={capability}.")

    reason = f"Task class {task_class} maps to capability {capability}; backend preference {backend_preference}."

    return {
        "task_class": task_class,
        "backend_id": backend_id,
        "backend_status": backend_status,
        "model_class": capability,
        "model_ids": model_ids,
        "integrations_available": integrations_available,
        "missing": missing,
        "reason": reason,
    }


def recommend_backend_for_task(task_class: str, repo_root: Path | str | None = None) -> str | None:
    """Return recommended backend_id for task class, or None."""
    rec = recommend_for_task_class(task_class, repo_root)
    return rec.get("backend_id")


def compatibility_for_model(
    model_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Compatibility report for a model: catalog entry, backend status, suitable task classes.
    """
    root = _repo_root(repo_root)
    entry = get_model_info(model_id, root)
    if not entry:
        return {
            "model_id": model_id,
            "in_catalog": False,
            "backend_family": None,
            "backend_status": None,
            "capability_classes": [],
            "recommended_usage": [],
            "suitable_task_classes": [],
            "message": f"Model {model_id} not in catalog.",
        }

    backends = load_backend_registry(root)
    backend_prof = get_backend_profile(entry.backend_family, root)
    backend_status = backend_prof.status if backend_prof else "unsupported"

    # Task classes that use this model's capabilities
    suitable_task_classes = [
        tc for tc, pol in TASK_CLASS_POLICY.items()
        if pol.get("capability") in entry.capability_classes
    ]

    return {
        "model_id": model_id,
        "in_catalog": True,
        "backend_family": entry.backend_family,
        "backend_status": backend_status,
        "capability_classes": entry.capability_classes,
        "recommended_usage": entry.recommended_usage,
        "suitable_task_classes": suitable_task_classes,
        "message": f"Compatible for: {', '.join(suitable_task_classes) or 'none'}.",
    }
