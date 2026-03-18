"""
M30D.1: Compatibility matrix — product version × runtime × packs × policy mode.
Warnings for unsafe or unsupported upgrade paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.install_upgrade.models import CHANNEL_STABLE, CHANNEL_PREVIEW, CHANNEL_INTERNAL
from workflow_dataset.install_upgrade.channels import get_channel, list_channels, RELEASE_CHANNELS


def _version_tuple(v: str) -> tuple[int, ...]:
    parts: list[int] = []
    for s in (v or "0.0.0").replace("-", ".").split("."):
        s = "".join(c for c in s if c.isdigit())
        parts.append(int(s) if s else 0)
    return tuple(parts)


def _version_ge(a: str, b: str) -> bool:
    """True if a >= b."""
    return _version_tuple(a) >= _version_tuple(b)


def build_compatibility_matrix(
    product_versions: list[str] | None = None,
    runtimes: list[str] | None = None,
    policy_modes: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build first-draft compatibility matrix: which product version + runtime + policy mode
    are supported per channel. Packs: advisory (no per-pack version in first-draft).
    """
    if product_versions is None:
        product_versions = ["0.1.0", "0.2.0", "0.3.0"]
    if runtimes is None:
        runtimes = ["local", "python_venv"]
    if policy_modes is None:
        policy_modes = ["enforce", "audit", "disabled", "permissive"]

    matrix: dict[str, Any] = {
        "channels": {},
        "product_versions": product_versions,
        "runtimes": runtimes,
        "policy_modes": policy_modes,
        "rows": [],
    }
    for ch in list_channels():
        channel_id = ch.channel_id
        matrix["channels"][channel_id] = {
            "label": ch.label,
            "min_product_version": ch.min_product_version,
            "allowed_policy_modes": list(ch.allowed_policy_modes),
            "upgrade_paths_to": list(ch.upgrade_paths_to),
        }
        for pv in product_versions:
            for rt in runtimes:
                for pm in policy_modes:
                    supported = _version_ge(pv, ch.min_product_version) and (pm in ch.allowed_policy_modes if ch.allowed_policy_modes else True)
                    matrix["rows"].append({
                        "channel": channel_id,
                        "product_version": pv,
                        "runtime": rt,
                        "policy_mode": pm,
                        "supported": supported,
                        "note": "" if supported else f"policy_mode {pm} not in channel {channel_id} allowed" if pm not in (ch.allowed_policy_modes or ()) else f"version {pv} < min {ch.min_product_version}",
                    })
    return matrix


def check_upgrade_path(
    from_version: str,
    to_version: str,
    from_channel: str = "",
    to_channel: str = "",
) -> dict[str, Any]:
    """
    Check upgrade path from (version, channel) to (version, channel).
    Returns: allowed, warnings[], unsafe_reasons[], supported.
    """
    from_channel = (from_channel or CHANNEL_STABLE).strip().lower()
    to_channel = (to_channel or CHANNEL_STABLE).strip().lower()
    from_ch = get_channel(from_channel)
    to_ch = get_channel(to_channel)
    warnings: list[str] = []
    unsafe: list[str] = []

    if not from_ch:
        warnings.append(f"Unknown from_channel: {from_channel}; treated as stable.")
        from_ch = get_channel(CHANNEL_STABLE)
    if not to_ch:
        warnings.append(f"Unknown to_channel: {to_channel}; treated as stable.")
        to_ch = get_channel(CHANNEL_STABLE)

    allowed = to_channel in (from_ch.upgrade_paths_to or ())
    if not allowed and from_channel != to_channel:
        unsafe.append(f"Upgrade from channel '{from_channel}' to '{to_channel}' is not in allowed upgrade_paths_to for {from_channel}.")

    if _version_tuple(to_version) < _version_tuple(from_version):
        if not getattr(to_ch, "supports_downgrade", False):
            unsafe.append("Downgrade is not supported on target channel.")
        else:
            warnings.append("Downgrade path: ensure rollback checkpoint exists.")

    if from_channel == CHANNEL_INTERNAL and to_channel == CHANNEL_STABLE:
        warnings.append("Internal → stable: unsupported path; use preview first or accept risk.")
        unsafe.append("Internal to stable is not a supported upgrade path.")
    if from_channel == CHANNEL_PREVIEW and to_channel == CHANNEL_STABLE:
        warnings.append("Preview → stable: ensure you have tested the preview build.")

    if not _version_ge(to_version, to_ch.min_product_version):
        unsafe.append(f"Target version {to_version} is below minimum {to_ch.min_product_version} for channel {to_channel}.")

    return {
        "allowed": allowed and not unsafe,
        "warnings": warnings,
        "unsafe_reasons": unsafe,
        "supported": allowed,
        "from_channel": from_channel,
        "to_channel": to_channel,
    }


def get_unsafe_upgrade_warnings(
    current_version: str,
    target_version: str,
    current_channel: str = "",
    target_channel: str = "",
) -> list[str]:
    """Return list of unsafe or unsupported upgrade path warnings (for use in upgrade plan)."""
    result = check_upgrade_path(current_version, target_version, current_channel, target_channel)
    out: list[str] = []
    out.extend(result.get("unsafe_reasons", []))
    out.extend(result.get("warnings", []))
    return out


def format_compatibility_matrix(matrix: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """Human-readable compatibility matrix (summary by channel + version)."""
    if matrix is None:
        matrix = build_compatibility_matrix(repo_root=repo_root)
    lines = [
        "=== Compatibility matrix (M30D.1) ===",
        "",
        "[Channels]",
    ]
    for cid, ch in matrix.get("channels", {}).items():
        lines.append(f"  {cid}: {ch.get('label', cid)}  min_version={ch.get('min_product_version', '')}  policy_modes={ch.get('allowed_policy_modes', [])}  upgrade_paths_to={ch.get('upgrade_paths_to', [])}")
    lines.append("")
    lines.append("[Sample rows: channel × product_version × policy_mode → supported]")
    rows = matrix.get("rows", [])
    seen: set[tuple[str, str, str]] = set()
    for r in rows[:24]:
        key = (r.get("channel", ""), r.get("product_version", ""), r.get("policy_mode", ""))
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"  {r.get('channel')}  {r.get('product_version')}  {r.get('policy_mode')}  supported={r.get('supported')}  {r.get('note', '')}")
    if len(rows) > 24:
        lines.append(f"  ... and {len(rows) - 24} more rows")
    lines.append("")
    lines.append("(Use release compatibility-matrix for full output. Warnings applied in upgrade-plan.)")
    return "\n".join(lines)
