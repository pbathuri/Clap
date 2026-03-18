"""
M25D: Report formatting for registry, verify, history.
"""

from __future__ import annotations

from workflow_dataset.packs.registry_index import RegistryEntry, load_local_registry, get_registry_entry
from workflow_dataset.packs.pack_history import get_pack_history
from workflow_dataset.packs.verify import verify_pack


def format_registry_list(entries: list[RegistryEntry], installed_versions: dict[str, str] | None = None) -> str:
    """Format registry entries as lines. installed_versions: pack_id -> current version."""
    lines = ["=== Pack registry ===", ""]
    inst = installed_versions or {}
    for e in entries:
        cur = f"  installed={inst.get(e.pack_id, '—')}" if inst else ""
        lines.append(f"  {e.pack_id}  {e.version}  {e.title or e.pack_id}{cur}")
    if not entries:
        lines.append("  (no entries; add data/local/packs/registry/index.json)")
    return "\n".join(lines)


def format_registry_show(entry: RegistryEntry | None, pack_id: str) -> str:
    """Format single registry entry."""
    if not entry:
        return f"Pack not in registry: {pack_id}"
    lines = [
        f"pack_id: {entry.pack_id}",
        f"title: {entry.title}",
        f"version: {entry.version}",
        f"description: {entry.description or '—'}",
        f"supported_roles: {entry.supported_roles}",
        f"supported_workflows: {entry.supported_workflows}",
        f"source_type: {entry.source_type}",
        f"source_path: {entry.source_path or '—'}",
        f"release_channel: {entry.release_channel}",
        f"trust_notes: {entry.trust_notes or '—'}",
    ]
    return "\n".join(lines)


def format_verify_result(valid: bool, warnings: list[str], errors: list[str], pack_id: str) -> str:
    """Format verify_pack result."""
    lines = [f"=== Pack verify: {pack_id} ===", ""]
    if valid:
        lines.append("Result: valid")
    else:
        lines.append("Result: invalid")
    for e in errors:
        lines.append(f"  error: {e}")
    for w in warnings:
        lines.append(f"  warning: {w}")
    return "\n".join(lines)


def format_blocked_install(message: str, pack_id: str = "") -> str:
    """Format a blocked install/update message. M25D.1."""
    prefix = f"Blocked ({pack_id}): " if pack_id else "Blocked: "
    return prefix + message


def format_warned_install(message: str) -> str:
    """Format a warning for install/update from risky channel. M25D.1."""
    return "Warning: " + message


def format_pack_history(pack_id: str, history: list[dict], limit: int = 10) -> str:
    """Format pack install history."""
    lines = [f"=== Pack history: {pack_id} ===", ""]
    for i, rec in enumerate(history[:limit], 1):
        ver = rec.get("version", "—")
        ts = rec.get("installed_utc", 0)
        from datetime import datetime
        try:
            dt = datetime.utcfromtimestamp(ts).isoformat() + "Z" if ts else "—"
        except Exception:
            dt = str(ts)
        lines.append(f"  {i}. version={ver}  installed_utc={dt}")
    if not history:
        lines.append("  (no history)")
    return "\n".join(lines)
