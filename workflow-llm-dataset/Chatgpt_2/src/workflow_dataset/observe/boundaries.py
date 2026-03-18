"""
Consent and scope boundary enforcement for observation (M31C).

- Enabled/disabled per source (from allowed_observation_sources and global observation_enabled)
- Allowed scopes/paths/apps (file: root_paths; others: from config when implemented)
- Observe-only vs rich_metadata mode
- Retention boundaries (per-source or global)
- Source health / source blocked state (scope violation, collector error, disabled)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.observe.sources import (
    CollectionMode,
    ObservationSourceDef,
    get_observation_source_registry,
)


def check_source_enabled(
    source_id: str,
    observation_enabled: bool,
    allowed_sources: list[str] | None,
) -> tuple[bool, str]:
    """
    Return (enabled, reason). Source is enabled only if global observation is on
    and source is in the allowed list.
    """
    if not observation_enabled:
        return False, "observation_disabled"
    if not allowed_sources or source_id not in allowed_sources:
        return False, "source_not_allowed"
    return True, "ok"


def check_file_scope(
    path: Path,
    root_paths: list[Path],
    exclude_dirs: set[str],
) -> tuple[bool, str]:
    """
    Return (in_scope, reason). Path must be under one of root_paths and not in an excluded dir.
    """
    if not root_paths:
        return False, "no_root_paths"
    try:
        resolved = path.resolve()
        for root in root_paths:
            r = root.resolve()
            try:
                resolved.relative_to(r)
            except ValueError:
                continue
            for part in resolved.parts:
                if part in exclude_dirs:
                    return False, "excluded_dir"
            return True, "ok"
    except Exception as e:
        return False, str(e)
    return False, "path_not_under_roots"


def get_source_health(
    source_id: str,
    observation_enabled: bool,
    allowed_sources: list[str] | None,
    scope_ok: bool = True,
    collector_ok: bool = True,
) -> tuple[str, str]:
    """
    Return (health, detail). health is one of SourceHealth-like values;
    detail is a short message.
    """
    registry = get_observation_source_registry()
    defn = registry.get(source_id)
    if not defn:
        return "blocked_unhealthy", "unknown_source"

    if not observation_enabled:
        return "blocked_disabled", "observation_disabled"
    if not allowed_sources or source_id not in allowed_sources:
        return "blocked_not_allowed", "source_not_in_allowed_list"
    if not scope_ok:
        return "blocked_scope", "scope_violation"
    if not collector_ok:
        return "blocked_unhealthy", "collector_error"
    if not defn.implemented:
        return "stub", "no_collector_implemented"
    return "ok", "ok"


def get_boundary_state(
    observation_enabled: bool,
    allowed_sources: list[str] | None,
    file_root_paths: list[str] | None = None,
) -> dict[str, Any]:
    """
    Aggregate boundary state for reporting: enabled sources, blocked sources,
    retention expectations, consent posture. No PII.
    """
    allowed_sources = allowed_sources or []
    registry = get_observation_source_registry()
    enabled: list[str] = []
    blocked: list[dict[str, str]] = []
    stubs: list[str] = []

    for sid in registry:
        defn = registry[sid]
        health, detail = get_source_health(
            sid,
            observation_enabled,
            allowed_sources,
            scope_ok=True,
            collector_ok=True,
        )
        if health == "ok":
            enabled.append(sid)
        elif health == "stub":
            stubs.append(sid)
        else:
            blocked.append({"source": sid, "reason": health, "detail": detail})

    return {
        "observation_enabled": observation_enabled,
        "allowed_sources": list(allowed_sources),
        "enabled_sources": enabled,
        "blocked_sources": blocked,
        "stub_sources": stubs,
        "file_root_paths_configured": bool(file_root_paths and len(file_root_paths) > 0),
        "retention_by_source": {
            sid: registry[sid].retention_days
            for sid in registry
            if registry[sid].retention_days is not None
        },
    }


def retention_days_for_source(source_id: str, default_days: int = 90) -> int:
    """Return suggested retention in days for this source; default if not set."""
    registry = get_observation_source_registry()
    defn = registry.get(source_id)
    if defn and defn.retention_days is not None:
        return defn.retention_days
    return default_days
