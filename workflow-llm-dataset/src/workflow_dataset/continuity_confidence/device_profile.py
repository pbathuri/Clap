"""
M49I–M49L: Target device profile — build from current environment, compare source vs target.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.continuity_confidence.models import (
    TargetDeviceProfile,
    DeviceCapabilityClass,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_target_device_profile(
    repo_root: Path | str | None = None,
    device_id: str = "current",
) -> TargetDeviceProfile:
    """
    Build target device profile from current environment (edge tier, runtime, backends, version).
    Does not require a prior restore; use for "current device" or as target in comparison.
    """
    root = _root(repo_root)
    now = utc_now_iso()
    profile_id = f"device_{device_id}_{now[:10]}"
    runtime_id = "local"
    edge_tier = "local_standard"
    product_version = "0.0.0"
    allowed_backends: list[str] = []
    has_llm_backend = False

    try:
        from workflow_dataset.install_upgrade.version import get_current_version
        product_version = get_current_version(root) or "0.0.0"
    except Exception:
        pass

    try:
        from workflow_dataset.edge.profile import build_edge_profile
        ep = build_edge_profile(repo_root=root)
        runtime_req = ep.get("runtime_requirements") or {}
        if runtime_req:
            runtime_id = str(runtime_req.get("runtime_id", runtime_id))
        tier = ep.get("tier") or ep.get("edge_tier")
        if tier:
            edge_tier = str(tier)
    except Exception:
        pass

    try:
        from workflow_dataset.runtime_mesh.backend_registry import load_backend_registry, get_backend_status
        reg = load_backend_registry(repo_root=root)
        for backend_id, _ in (reg.get("backends") or {}).items():
            allowed_backends.append(backend_id)
            st = get_backend_status(backend_id, repo_root=root)
            if st.get("status") in ("available", "configured"):
                has_llm_backend = has_llm_backend or backend_id in ("ollama", "llama_cpp", "repo_local", "openai")
    except Exception:
        pass

    return TargetDeviceProfile(
        profile_id=profile_id,
        device_id=device_id,
        runtime_id=runtime_id,
        edge_tier=edge_tier,
        product_version=product_version,
        capability_class=DeviceCapabilityClass.UNKNOWN.value,
        allowed_backends=allowed_backends,
        has_llm_backend=has_llm_backend,
        notes="Built from current environment.",
        created_utc=now,
    )


def compare_source_target(
    source_profile: TargetDeviceProfile | None,
    target_profile: TargetDeviceProfile | None,
) -> str:
    """
    Compare source vs target device; return capability_class: stronger | same | weaker | different | unknown.
    """
    if not source_profile or not target_profile:
        return DeviceCapabilityClass.UNKNOWN.value
    # Heuristic: compare backends, tier, version
    src_backends = set(source_profile.allowed_backends or [])
    tgt_backends = set(target_profile.allowed_backends or [])
    src_llm = source_profile.has_llm_backend
    tgt_llm = target_profile.has_llm_backend
    tier_order = {"dev_full": 4, "local_standard": 3, "constrained_edge": 2, "minimal_eval": 1}

    def tier_rank(t: str) -> int:
        return tier_order.get(t, 0)

    if tgt_backends >= src_backends and tgt_llm >= src_llm and tier_rank(target_profile.edge_tier) >= tier_rank(source_profile.edge_tier):
        if tgt_backends > src_backends or tier_rank(target_profile.edge_tier) > tier_rank(source_profile.edge_tier):
            return DeviceCapabilityClass.STRONGER.value
        return DeviceCapabilityClass.SAME.value
    if tgt_backends <= src_backends and not (tgt_backends >= src_backends):
        return DeviceCapabilityClass.WEAKER.value
    if target_profile.edge_tier != source_profile.edge_tier or (tgt_llm != src_llm):
        return DeviceCapabilityClass.DIFFERENT.value
    return DeviceCapabilityClass.SAME.value
