"""
M25A: Pack registry index — curated list of available packs (local first; external explicit and approval-gated).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REGISTRY_INDEX_FILE = "registry/index.json"
DEFAULT_PACKS_DIR = Path("data/local/packs")


def _packs_root(packs_dir: Path | str | None) -> Path:
    if packs_dir is not None:
        return Path(packs_dir).resolve()
    return Path(DEFAULT_PACKS_DIR).resolve()


@dataclass
class RegistryEntry:
    """
    One entry in the pack registry: id, version, description, supported roles/workflows,
    compatibility, dependencies, source (local vs external), trust notes, verification metadata,
    release channel.
    """
    pack_id: str
    title: str = ""
    version: str = "0.1.0"
    description: str = ""
    supported_roles: list[str] = field(default_factory=list)
    supported_workflows: list[str] = field(default_factory=list)
    supported_tasks: list[str] = field(default_factory=list)
    compatibility_requirements: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    source_type: str = "local"  # local | external
    source_path: str = ""  # path to manifest or bundle
    source_url: str = ""  # optional; only when source_type=external and approved
    trust_notes: str = ""
    checksum: str = ""  # optional sha256 or similar
    signature_metadata: dict[str, Any] = field(default_factory=dict)
    release_channel: str = "stable"  # local | dev | stable
    install_status: str = ""  # filled at runtime: installed | available | unknown
    update_available: bool = False  # filled at runtime when newer in registry

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "supported_roles": list(self.supported_roles),
            "supported_workflows": list(self.supported_workflows),
            "supported_tasks": list(self.supported_tasks),
            "compatibility_requirements": list(self.compatibility_requirements),
            "dependencies": list(self.dependencies),
            "source_type": self.source_type,
            "source_path": self.source_path,
            "source_url": self.source_url,
            "trust_notes": self.trust_notes,
            "checksum": self.checksum,
            "signature_metadata": dict(self.signature_metadata),
            "release_channel": self.release_channel,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RegistryEntry:
        return cls(
            pack_id=d.get("pack_id", ""),
            title=d.get("title", d.get("name", "")),
            version=d.get("version", "0.1.0"),
            description=d.get("description", ""),
            supported_roles=list(d.get("supported_roles", d.get("role_tags", []))),
            supported_workflows=list(d.get("supported_workflows", d.get("workflow_tags", []))),
            supported_tasks=list(d.get("supported_tasks", d.get("task_tags", []))),
            compatibility_requirements=list(d.get("compatibility_requirements", [])),
            dependencies=list(d.get("dependencies", [])),
            source_type=d.get("source_type", "local"),
            source_path=d.get("source_path", ""),
            source_url=d.get("source_url", ""),
            trust_notes=d.get("trust_notes", ""),
            checksum=d.get("checksum", ""),
            signature_metadata=dict(d.get("signature_metadata", {})),
            release_channel=d.get("release_channel", "stable"),
        )


def get_registry_index_path(packs_dir: Path | str | None = None) -> Path:
    """Path to registry/index.json under packs dir."""
    return _packs_root(packs_dir) / REGISTRY_INDEX_FILE


def load_local_registry(packs_dir: Path | str | None = None) -> list[RegistryEntry]:
    """
    Load registry index from data/local/packs/registry/index.json.
    Format: { "entries": [ { pack_id, title, version, ... }, ... ] } or [ { ... }, ... ].
    Returns empty list if file missing or invalid.
    """
    path = get_registry_index_path(packs_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [RegistryEntry.from_dict(e) for e in data]
        entries = data.get("entries", data.get("packs", []))
        return [RegistryEntry.from_dict(e) for e in entries]
    except Exception:
        return []


def get_registry_entry(pack_id: str, packs_dir: Path | str | None = None) -> RegistryEntry | None:
    """Return registry entry for pack_id, or None."""
    for e in load_local_registry(packs_dir):
        if e.pack_id == pack_id:
            return e
    return None


def list_registry_entries(
    packs_dir: Path | str | None = None,
    channel: str | None = None,
) -> list[RegistryEntry]:
    """List all registry entries; optionally filter by release_channel."""
    entries = load_local_registry(packs_dir)
    if channel:
        entries = [e for e in entries if e.release_channel == channel]
    return entries
