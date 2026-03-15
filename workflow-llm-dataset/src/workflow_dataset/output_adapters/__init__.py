"""
M13: Toolchain-native output adapters. Spreadsheet, creative, design, ops handoff bundles.

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
]
