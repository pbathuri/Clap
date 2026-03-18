"""
Local observation state: enabled sources and consent overrides (M31).

Stored in data/local/observation_state.yaml. If present, used for status/boundaries;
otherwise config (agent.observation_enabled, agent.allowed_observation_sources) is used.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _state_path(state_dir: Path | str | None) -> Path:
    if state_dir is None:
        return Path("data/local/observation_state.yaml")
    return Path(state_dir) / "observation_state.yaml"


def load_observation_state(state_dir: Path | str | None = None) -> dict[str, Any]:
    """Load observation state from data/local/observation_state.yaml. Returns empty dict if missing."""
    path = _state_path(state_dir)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_observation_state(
    enabled_sources: list[str],
    observation_enabled: bool = True,
    state_dir: Path | str | None = None,
) -> Path:
    """Write observation state. Creates parent dir. Returns path written."""
    path = _state_path(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "observation_enabled": observation_enabled,
        "enabled_sources": list(enabled_sources),
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    return path


def enable_source(source_id: str, state_dir: Path | str | None = None) -> list[str]:
    """Add source to enabled_sources and set observation_enabled true. Returns new enabled list."""
    state = load_observation_state(state_dir)
    enabled = list(state.get("enabled_sources") or [])
    if source_id not in enabled:
        enabled.append(source_id)
    save_observation_state(enabled, observation_enabled=True, state_dir=state_dir)
    return enabled


def disable_source(source_id: str, state_dir: Path | str | None = None) -> list[str]:
    """Remove source from enabled_sources. Returns new enabled list."""
    state = load_observation_state(state_dir)
    enabled = list(state.get("enabled_sources") or [])
    if source_id in enabled:
        enabled.remove(source_id)
    save_observation_state(enabled, observation_enabled=len(enabled) > 0, state_dir=state_dir)
    return enabled


def effective_observation_config(
    config_enabled: bool,
    config_allowed_sources: list[str] | None,
    state_dir: Path | str | None = None,
) -> tuple[bool, list[str]]:
    """
    Return (observation_enabled, allowed_sources). If state file exists and has
    enabled_sources, use that; else use config values.
    """
    state = load_observation_state(state_dir)
    if state.get("enabled_sources") is not None:
        return bool(state.get("observation_enabled", True)), list(state["enabled_sources"])
    return config_enabled, list(config_allowed_sources or [])
