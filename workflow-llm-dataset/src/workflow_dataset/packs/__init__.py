"""
M22: Capability-pack installer, resolver, and runtime integration. Local-first.
"""

from __future__ import annotations

from workflow_dataset.packs.pack_models import PackManifest, validate_pack_manifest
from workflow_dataset.packs.pack_registry import (
    list_installed_packs,
    get_installed_pack,
    get_installed_manifest,
)
from workflow_dataset.packs.pack_installer import install_pack, uninstall_pack
from workflow_dataset.packs.pack_resolver import resolve_active_capabilities, ActiveCapabilities
from workflow_dataset.packs.pack_resolution_graph import resolve_with_priority, ResolutionExplanation
from workflow_dataset.packs.pack_conflicts import detect_conflicts, PackConflict, ConflictClass

__all__ = [
    "PackManifest",
    "validate_pack_manifest",
    "list_installed_packs",
    "get_installed_pack",
    "get_installed_manifest",
    "install_pack",
    "uninstall_pack",
    "resolve_active_capabilities",
    "ActiveCapabilities",
    "resolve_with_priority",
    "ResolutionExplanation",
    "detect_conflicts",
    "PackConflict",
    "ConflictClass",
]
