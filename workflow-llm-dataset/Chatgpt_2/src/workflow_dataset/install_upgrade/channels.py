"""
M30D.1: Release channels — stable / preview / internal. First-draft definitions.
"""

from __future__ import annotations

from workflow_dataset.install_upgrade.models import (
    ReleaseChannel,
    CHANNEL_STABLE,
    CHANNEL_PREVIEW,
    CHANNEL_INTERNAL,
)

RELEASE_CHANNELS: dict[str, ReleaseChannel] = {
    CHANNEL_STABLE: ReleaseChannel(
        channel_id=CHANNEL_STABLE,
        label="Stable",
        description="Production-ready releases. Recommended for non-developers.",
        min_product_version="0.1.0",
        allowed_policy_modes=("enforce", "audit", "disabled"),
        supports_downgrade=False,
        upgrade_paths_to=(CHANNEL_STABLE,),  # only same channel for stable
    ),
    CHANNEL_PREVIEW: ReleaseChannel(
        channel_id=CHANNEL_PREVIEW,
        label="Preview",
        description="Pre-release builds. New features; may have regressions.",
        min_product_version="0.1.0",
        allowed_policy_modes=("enforce", "audit", "disabled"),
        supports_downgrade=True,
        upgrade_paths_to=(CHANNEL_PREVIEW, CHANNEL_STABLE),
    ),
    CHANNEL_INTERNAL: ReleaseChannel(
        channel_id=CHANNEL_INTERNAL,
        label="Internal",
        description="Internal/dev builds. Unsupported upgrade paths; use with caution.",
        min_product_version="0.0.1",
        allowed_policy_modes=("enforce", "audit", "disabled", "permissive"),
        supports_downgrade=True,
        upgrade_paths_to=(CHANNEL_INTERNAL, CHANNEL_PREVIEW, CHANNEL_STABLE),
    ),
}


def get_channel(channel_id: str) -> ReleaseChannel | None:
    """Return release channel by id (stable, preview, internal)."""
    return RELEASE_CHANNELS.get((channel_id or "").strip().lower())


def list_channels() -> list[ReleaseChannel]:
    """Return ordered list of channels: stable, preview, internal."""
    return [
        RELEASE_CHANNELS[CHANNEL_STABLE],
        RELEASE_CHANNELS[CHANNEL_PREVIEW],
        RELEASE_CHANNELS[CHANNEL_INTERNAL],
    ]
