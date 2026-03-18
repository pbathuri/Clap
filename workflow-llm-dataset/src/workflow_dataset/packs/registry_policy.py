"""
M25D.1: Release-channel and registry-policy behavior. Local-first, operator-readable.
Channels: stable, preview, internal. Policy: allow | warn | block. Optional per-role overrides.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REGISTRY_POLICY_FILE = "registry/policy.json"
DEFAULT_PACKS_DIR = Path("data/local/packs")

# Default: stable allowed; preview/internal risky — warn or block
DEFAULT_CHANNEL_POLICY = {
    "stable": "allow",
    "preview": "warn",
    "internal": "block",
    "dev": "warn",
    "local": "allow",
}


def _packs_root(packs_dir: Path | str | None) -> Path:
    if packs_dir is not None:
        return Path(packs_dir).resolve()
    return DEFAULT_PACKS_DIR.resolve()


def get_registry_policy_path(packs_dir: Path | str | None = None) -> Path:
    """Path to registry/policy.json under packs dir."""
    return _packs_root(packs_dir) / REGISTRY_POLICY_FILE


def load_registry_policy(packs_dir: Path | str | None = None) -> dict[str, Any]:
    """
    Load registry policy from registry/policy.json.
    Expected shape:
      {
        "channels": { "stable": "allow", "preview": "warn", "internal": "block", ... },
        "default_channel_policy": "allow" | "warn" | "block",  // for unknown channels
        "role_overrides": { "role_id": { "preview": "allow", "internal": "block" }, ... }
      }
    Returns dict with at least "channels" (and defaults for missing keys).
    """
    path = get_registry_policy_path(packs_dir)
    if not path.exists():
        return {
            "channels": dict(DEFAULT_CHANNEL_POLICY),
            "default_channel_policy": "warn",
            "role_overrides": {},
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        channels = dict(DEFAULT_CHANNEL_POLICY)
        channels.update(data.get("channels", {}))
        return {
            "channels": channels,
            "default_channel_policy": data.get("default_channel_policy", "warn"),
            "role_overrides": data.get("role_overrides", {}),
        }
    except Exception:
        return {
            "channels": dict(DEFAULT_CHANNEL_POLICY),
            "default_channel_policy": "warn",
            "role_overrides": {},
        }


def check_channel_policy(
    release_channel: str,
    active_role: str,
    packs_dir: Path | str | None = None,
) -> tuple[str, str]:
    """
    Resolve policy for (channel, role). Returns (action, reason) where
    action is "allow" | "warn" | "block", and reason is a short human-readable string.
    """
    policy = load_registry_policy(packs_dir)
    channels = policy.get("channels", DEFAULT_CHANNEL_POLICY)
    default_action = policy.get("default_channel_policy", "warn")
    role_overrides = policy.get("role_overrides", {})

    # Per-role override for this channel
    if active_role and active_role in role_overrides:
        overrides = role_overrides[active_role]
        if isinstance(overrides, dict) and release_channel in overrides:
            action = overrides[release_channel]
            if action in ("allow", "warn", "block"):
                reason = f"role '{active_role}' policy for channel '{release_channel}': {action}"
                return action, reason

    # Machine-level channel policy
    action = channels.get(release_channel) or default_action
    if action not in ("allow", "warn", "block"):
        action = default_action
    reason = f"channel '{release_channel}' policy: {action}"
    return action, reason
