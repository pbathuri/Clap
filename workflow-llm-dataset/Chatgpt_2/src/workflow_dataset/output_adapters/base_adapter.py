"""
M13: Base interface for toolchain-native output adapters.

Adapters consume source artifact path + context and write a bundle under workspace_path.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from workflow_dataset.output_adapters.adapter_models import (
    OutputAdapterRequest,
    OutputBundle,
    OutputBundleManifest,
)


class BaseOutputAdapter(ABC):
    """Abstract base for output adapters. Sandbox-only; no real project writes."""

    adapter_type: str = ""

    @abstractmethod
    def create_bundle(
        self,
        request: OutputAdapterRequest,
        workspace_path: Path,
        source_content: str = "",
        style_profile_refs: list[str] | None = None,
        revision_note: str = "",
        populate: bool = False,
        allow_xlsx: bool = False,
        population_max_rows: int = 1000,
        population_max_sections: int = 50,
    ) -> tuple[OutputBundle, OutputBundleManifest]:
        """
        Create a toolchain-native bundle under workspace_path.
        M14: populate=True uses source_content to fill bundle; allow_xlsx enables XLSX when supported.
        Returns (bundle, manifest). All paths in bundle are relative to workspace_path.
        """
        ...


def read_source_artifact(source_path: str | Path) -> str:
    """Read text content from source artifact; safe for missing/binary."""
    p = Path(source_path)
    if not p.exists() or not p.is_file():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
