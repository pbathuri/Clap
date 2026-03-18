"""
M49L.1: Device classes — full local workstation, constrained laptop, recovery-safe environment.
"""

from __future__ import annotations

from workflow_dataset.continuity_confidence.models import DeviceClass, TargetDeviceProfile


def _builtin_device_classes() -> list[DeviceClass]:
    return [
        DeviceClass(
            class_id="full_local_workstation",
            label="Full local workstation",
            description="Full-capability local machine: typical dev_full or local_standard tier, LLM backends available.",
            edge_tiers=["dev_full", "local_standard"],
            requires_llm_backend=False,
            typical_backends=["ollama", "repo_local", "llama_cpp", "openai"],
            safe_for_operator_mode_default=True,
            when_to_use="Use when the target device has full local runtime, multiple backends, and is your primary workstation.",
        ),
        DeviceClass(
            class_id="constrained_laptop",
            label="Constrained laptop",
            description="Laptop or resource-constrained machine: local_standard or constrained_edge; may have limited backends.",
            edge_tiers=["local_standard", "constrained_edge"],
            requires_llm_backend=False,
            typical_backends=["ollama", "repo_local"],
            safe_for_operator_mode_default=False,
            when_to_use="Use when the target is a laptop or has fewer backends / constrained edge tier; narrow production cut and review before operator mode.",
        ),
        DeviceClass(
            class_id="recovery_safe_environment",
            label="Recovery-safe environment",
            description="Minimal or recovery environment: constrained_edge or minimal_eval; run for recovery or validation only.",
            edge_tiers=["constrained_edge", "minimal_eval"],
            requires_llm_backend=False,
            typical_backends=[],
            safe_for_operator_mode_default=False,
            when_to_use="Use when the target is a recovery or minimal-eval environment; avoid operator mode and real execution until upgraded.",
        ),
    ]


_CLASSES: list[DeviceClass] | None = None


def list_device_classes() -> list[DeviceClass]:
    """Return all built-in device classes."""
    global _CLASSES
    if _CLASSES is None:
        _CLASSES = _builtin_device_classes()
    return list(_CLASSES)


def get_device_class(class_id: str) -> DeviceClass | None:
    """Return the device class with the given class_id, or None."""
    for c in list_device_classes():
        if c.class_id == class_id:
            return c
    return None


def resolve_device_class(profile: TargetDeviceProfile) -> DeviceClass:
    """
    Resolve the best-matching device class for a target device profile.
    Uses edge_tier and has_llm_backend / allowed_backends.
    """
    tier = (profile.edge_tier or "").strip().lower()
    has_llm = profile.has_llm_backend
    backends = set(profile.allowed_backends or [])

    for c in list_device_classes():
        if tier not in [t.lower() for t in c.edge_tiers]:
            continue
        if c.requires_llm_backend and not has_llm:
            continue
        return c

    # Fallback: pick by tier only
    if tier in ("dev_full", "local_standard") and has_llm:
        return get_device_class("full_local_workstation") or list_device_classes()[0]
    if tier == "constrained_edge":
        return get_device_class("constrained_laptop") or list_device_classes()[1]
    if tier == "minimal_eval":
        return get_device_class("recovery_safe_environment") or list_device_classes()[2]

    return list_device_classes()[0]
