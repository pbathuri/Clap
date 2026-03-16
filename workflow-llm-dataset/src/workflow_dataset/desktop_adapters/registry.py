"""
M23C-F1: Desktop action adapter registry. Register, list, get, check availability.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.desktop_adapters.contracts import AdapterContract, BUILTIN_ADAPTERS

_registry: dict[str, AdapterContract] = {}


def _ensure_builtins() -> None:
    if not _registry:
        for c in BUILTIN_ADAPTERS:
            _registry[c.adapter_id] = c


def register_adapter(contract: AdapterContract) -> None:
    """Register a desktop action adapter by id."""
    _registry[contract.adapter_id] = contract


def list_adapters() -> list[AdapterContract]:
    """List all registered adapters."""
    _ensure_builtins()
    return list(_registry.values())


def get_adapter(adapter_id: str) -> AdapterContract | None:
    """Get adapter by id."""
    _ensure_builtins()
    return _registry.get(adapter_id.strip())


def check_availability(adapter_id: str) -> dict[str, Any]:
    """Check adapter availability. Returns {available: bool, adapter_id, message?, contract?}."""
    _ensure_builtins()
    a = get_adapter(adapter_id)
    if not a:
        return {"available": False, "adapter_id": adapter_id.strip(), "message": f"Adapter not found: {adapter_id}"}
    return {
        "available": True,
        "adapter_id": a.adapter_id,
        "contract": a,
        "supports_simulate": a.supports_simulate,
        "supports_real_execution": a.supports_real_execution,
    }
