"""
M23C-F1/F2: Desktop action adapter contracts, registry, simulate, and execute.
Local-first, simulate-first, approval-gated. F2: read-only + sandbox-only execution for file_ops and notes_document.
"""

from workflow_dataset.desktop_adapters.contracts import (
    AdapterContract,
    ActionSpec,
    BUILTIN_ADAPTERS,
)
from workflow_dataset.desktop_adapters.registry import (
    get_adapter,
    list_adapters,
    register_adapter,
    check_availability,
)
from workflow_dataset.desktop_adapters.simulate import (
    run_simulate,
    SimulateResult,
)
from workflow_dataset.desktop_adapters.execute import (
    run_execute,
    ExecuteResult,
    ProvenanceEntry,
)
from workflow_dataset.desktop_adapters.sandbox_config import get_sandbox_root
from workflow_dataset.desktop_adapters.url_validation import validate_local_or_allowed_url, UrlValidationResult
from workflow_dataset.desktop_adapters.app_allowlist import resolve_app_display_name, APPROVED_APP_NAMES

__all__ = [
    "AdapterContract",
    "ActionSpec",
    "BUILTIN_ADAPTERS",
    "register_adapter",
    "list_adapters",
    "get_adapter",
    "check_availability",
    "run_simulate",
    "SimulateResult",
    "run_execute",
    "ExecuteResult",
    "ProvenanceEntry",
    "get_sandbox_root",
    "validate_local_or_allowed_url",
    "UrlValidationResult",
    "resolve_app_display_name",
    "APPROVED_APP_NAMES",
]
