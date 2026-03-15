"""
M13: Registry for toolchain-native output adapters. Discovery and execution.

Sandbox-first; no real project writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from workflow_dataset.output_adapters.adapter_models import (
    OutputAdapterRequest,
    OutputBundle,
    OutputBundleManifest,
)
from workflow_dataset.output_adapters.base_adapter import BaseOutputAdapter, read_source_artifact
from workflow_dataset.output_adapters.bundle_manifest import save_bundle_manifest
from workflow_dataset.output_adapters.spreadsheet_adapter import SpreadsheetAdapter
from workflow_dataset.output_adapters.creative_package_adapter import CreativePackageAdapter
from workflow_dataset.output_adapters.design_package_adapter import DesignPackageAdapter
from workflow_dataset.output_adapters.ops_handoff_adapter import OpsHandoffAdapter


@dataclass
class AdapterMeta:
    """Metadata for a registered adapter."""

    adapter_type: str
    label: str
    description: str
    domains: list[str]
    output_kinds: list[str]


_adapters: dict[str, tuple[BaseOutputAdapter, AdapterMeta]] = {}


def register_adapter(adapter: BaseOutputAdapter, meta: AdapterMeta) -> None:
    """Register an output adapter by type."""
    _adapters[adapter.adapter_type] = (adapter, meta)


def get_adapter(adapter_type: str) -> tuple[BaseOutputAdapter, AdapterMeta] | None:
    """Get adapter and meta by type."""
    return _adapters.get(adapter_type)


def list_adapters() -> list[AdapterMeta]:
    """List all registered adapters."""
    return [meta for _, meta in _adapters.values()]


def create_bundle(
    adapter_type: str,
    request: OutputAdapterRequest,
    workspace_path: Path | str,
    bundle_store_path: Path | str,
    source_artifact_path: str = "",
    style_profile_refs: list[str] | None = None,
    revision_note: str = "",
    populate: bool = False,
    allow_xlsx: bool = False,
    population_max_rows: int = 1000,
    population_max_sections: int = 50,
) -> tuple[OutputBundle, OutputBundleManifest] | None:
    """
    Create an output bundle via named adapter. Persists manifest to bundle_store_path.
    M14: populate=True fills bundle from source; allow_xlsx enables XLSX when supported.
    Returns (bundle, manifest) or None if adapter not found / error.
    """
    entry = get_adapter(adapter_type)
    if not entry:
        return None
    adapter, _ = entry
    workspace_path = Path(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    source_content = read_source_artifact(source_artifact_path) if source_artifact_path else ""
    request.source_artifact_path = source_artifact_path or request.source_artifact_path
    request.workspace_path = str(workspace_path)
    try:
        bundle, manifest = adapter.create_bundle(
            request,
            workspace_path,
            source_content=source_content,
            style_profile_refs=style_profile_refs,
            revision_note=revision_note,
            populate=populate,
            allow_xlsx=allow_xlsx,
            population_max_rows=population_max_rows,
            population_max_sections=population_max_sections,
        )
        save_bundle_manifest(manifest, bundle_store_path)
        return bundle, manifest
    except Exception:
        return None


# Register built-in adapters
register_adapter(
    SpreadsheetAdapter(),
    AdapterMeta(
        adapter_type="spreadsheet",
        label="Spreadsheet / workbook",
        description="Multi-sheet CSV bundle, tab plan, column dictionary, tracker",
        domains=["finance", "ops", "design"],
        output_kinds=["csv", "markdown"],
    ),
)
register_adapter(
    CreativePackageAdapter(),
    AdapterMeta(
        adapter_type="creative_package",
        label="Creative package",
        description="Brief + storyboard + shotlist + asset structure + deliverables checklist",
        domains=["creative", "design"],
        output_kinds=["markdown", "folder_scaffold"],
    ),
)
register_adapter(
    DesignPackageAdapter(),
    AdapterMeta(
        adapter_type="design_package",
        label="Design / architecture package",
        description="Design brief, issue checklist, deliverable folder structure",
        domains=["design"],
        output_kinds=["markdown", "folder_scaffold"],
    ),
)
register_adapter(
    OpsHandoffAdapter(),
    AdapterMeta(
        adapter_type="ops_handoff",
        label="Ops handoff",
        description="Report + checklist + memo + tracker bundle",
        domains=["ops", "finance"],
        output_kinds=["markdown", "csv"],
    ),
)
