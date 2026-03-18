"""
M23T/M23S: Runtime mesh — backend registry, model catalog, integrations, policy, summary, validate, optional llama.cpp.
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
from workflow_dataset.runtime_mesh.profiles_and_policies import (
    list_vertical_profiles,
    list_routing_policies,
    get_vertical_profile,
    get_routing_policy,
    build_routing_policy_report,
)
from workflow_dataset.runtime_mesh.routing import (
    route_for_task,
    availability_check,
    build_fallback_report,
    explain_route,
    TASK_FAMILIES,
    ROUTE_OUTCOME_PREFERRED,
    ROUTE_OUTCOME_ALLOWED,
    ROUTE_OUTCOME_DEGRADED,
    ROUTE_OUTCOME_BLOCKED,
)
from workflow_dataset.runtime_mesh.summary import build_runtime_summary, format_runtime_summary
from workflow_dataset.runtime_mesh.validate import run_runtime_validate, format_validation_report
from workflow_dataset.runtime_mesh.llama_cpp_check import llama_cpp_check, format_llama_cpp_check_report

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
    "list_vertical_profiles",
    "list_routing_policies",
    "get_vertical_profile",
    "get_routing_policy",
    "build_routing_policy_report",
    "route_for_task",
    "availability_check",
    "build_fallback_report",
    "explain_route",
    "TASK_FAMILIES",
    "ROUTE_OUTCOME_PREFERRED",
    "ROUTE_OUTCOME_ALLOWED",
    "ROUTE_OUTCOME_DEGRADED",
    "ROUTE_OUTCOME_BLOCKED",
    "build_runtime_summary",
    "format_runtime_summary",
    "run_runtime_validate",
    "format_validation_report",
    "llama_cpp_check",
    "format_llama_cpp_check_report",
]
