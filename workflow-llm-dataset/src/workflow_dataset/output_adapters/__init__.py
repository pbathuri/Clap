"""
M13/M14: Toolchain-native output adapters. Spreadsheet, creative, design, ops handoff bundles.
M14: Content-aware population from reviewed/refined artifacts; optional XLSX.
Local-only; sandbox-first; adoptable via existing apply flow.
"""

from __future__ import annotations

from workflow_dataset.output_adapters.adapter_models import (
    OutputAdapterRequest,
    OutputBundle,
    OutputBundleManifest,
)
from workflow_dataset.output_adapters.base_adapter import BaseOutputAdapter, read_source_artifact
from workflow_dataset.output_adapters.adapter_registry import (
    register_adapter,
    get_adapter,
    list_adapters,
    create_bundle,
    AdapterMeta,
)
from workflow_dataset.output_adapters.bundle_manifest import (
    save_bundle_manifest,
    load_bundle_manifest,
    load_manifest_for_bundle,
    list_bundles,
)
from workflow_dataset.output_adapters.content_extractors import extract_content
from workflow_dataset.output_adapters.population_models import (
    SourceContentSlice,
    PopulatedSection,
    PopulatedTablePlan,
    PopulationResult,
)

__all__ = [
    "OutputAdapterRequest",
    "OutputBundle",
    "OutputBundleManifest",
    "BaseOutputAdapter",
    "read_source_artifact",
    "register_adapter",
    "get_adapter",
    "list_adapters",
    "create_bundle",
    "AdapterMeta",
    "save_bundle_manifest",
    "load_bundle_manifest",
    "load_manifest_for_bundle",
    "list_bundles",
    "extract_content",
    "SourceContentSlice",
    "PopulatedSection",
    "PopulatedTablePlan",
    "PopulationResult",
]
