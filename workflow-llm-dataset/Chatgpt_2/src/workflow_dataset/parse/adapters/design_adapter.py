"""
Design adapter: layout, UI/CAD hints, asset organization, project structure.

Uses folder hierarchy, naming schemes, and extension patterns (e.g. .fig, .sketch, .dwg).
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.parse.adapters.base_adapter import BaseDomainAdapter, AdapterSignal
from workflow_dataset.parse.document_models import ParsedDocument
from workflow_dataset.setup.setup_models import ArtifactFamily

DESIGN_EXT = {"fig", "sketch", "xd", "psd", "ai", "dwg", "dxf", "svg", "pdf"}
DESIGN_FOLDER_NAMES = {"assets", "exports", "source", "design", "ui", "components", "layouts"}


class DesignAdapter(BaseDomainAdapter):
    @property
    def name(self) -> str:
        return "design"

    @property
    def supported_families(self) -> list[ArtifactFamily]:
        return [
            ArtifactFamily.IMAGE_ASSET,
            ArtifactFamily.EXPORTED_DELIVERABLE,
            ArtifactFamily.PROJECT_DIRECTORY,
        ]

    def process(self, doc: ParsedDocument) -> list[AdapterSignal]:
        out: list[AdapterSignal] = []
        path = Path(doc.source_path)
        name = path.name.lower()
        ext = path.suffix.lstrip(".").lower()
        parent_name = path.parent.name.lower() if path.parent else ""

        if ext in DESIGN_EXT:
            out.append(AdapterSignal(
                signal_type="design_artifact",
                value=ext,
                confidence=0.85,
                domain="design",
                source_path=doc.source_path,
                metadata={"filename": path.name},
            ))
        if parent_name in DESIGN_FOLDER_NAMES:
            out.append(AdapterSignal(
                signal_type="asset_organization",
                value=parent_name,
                confidence=0.7,
                domain="design",
                source_path=doc.source_path,
                description="File in design-style folder",
            ))
        if doc.artifact_family == ArtifactFamily.PROJECT_DIRECTORY.value:
            out.append(AdapterSignal(
                signal_type="project_structure",
                value=path.name,
                confidence=0.5,
                domain="design",
                source_path=doc.source_path,
            ))
        return out
