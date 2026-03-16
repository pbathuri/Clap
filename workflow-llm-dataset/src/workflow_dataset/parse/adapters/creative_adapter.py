"""
Creative adapter: asset structures, export patterns, revision naming, deliverable shapes.

Real from first pass using: exports, metadata, project folder structure,
file naming/revision patterns, asset bundle relationships, repeated deliverable shapes.
"""

from __future__ import annotations

import re
from pathlib import Path

from workflow_dataset.parse.adapters.base_adapter import BaseDomainAdapter, AdapterSignal
from workflow_dataset.parse.document_models import ParsedDocument
from workflow_dataset.setup.setup_models import ArtifactFamily

# Revision/export naming hints (creative workflows)
REV_HINTS = re.compile(r"(v\d+|_\d{4}-\d{2}-\d{2}|_final|_export|_render|_comp|_master)", re.I)
EXPORT_EXT = {"pdf", "mp4", "mov", "png", "jpg", "jpeg", "webm", "wav", "mp3"}


class CreativeAdapter(BaseDomainAdapter):
    @property
    def name(self) -> str:
        return "creative"

    @property
    def supported_families(self) -> list[ArtifactFamily]:
        return [
            ArtifactFamily.MEDIA_ASSET,
            ArtifactFamily.IMAGE_ASSET,
            ArtifactFamily.EXPORTED_DELIVERABLE,
            ArtifactFamily.PROJECT_DIRECTORY,
            ArtifactFamily.TEXT_DOCUMENT,  # scripts, captions
        ]

    def process(self, doc: ParsedDocument) -> list[AdapterSignal]:
        out: list[AdapterSignal] = []
        path = Path(doc.source_path)
        name = path.name.lower()
        ext = path.suffix.lstrip(".").lower()

        if ext in EXPORT_EXT:
            out.append(AdapterSignal(
                signal_type="export_output",
                value=ext,
                confidence=0.7,
                domain="creative",
                source_path=doc.source_path,
                metadata={"filename": path.name},
            ))
        if REV_HINTS.search(name):
            out.append(AdapterSignal(
                signal_type="revision_naming",
                value=name[:80],
                confidence=0.75,
                domain="creative",
                source_path=doc.source_path,
                description="Export/revision-style filename",
            ))
        if doc.artifact_family == ArtifactFamily.PROJECT_DIRECTORY.value:
            out.append(AdapterSignal(
                signal_type="project_folder",
                value=path.name,
                confidence=0.6,
                domain="creative",
                source_path=doc.source_path,
            ))
        # Metadata from ParsedDocument (e.g. media metadata if present)
        if doc.metadata.get("width") or doc.metadata.get("duration"):
            out.append(AdapterSignal(
                signal_type="media_metadata",
                value=dict((k, doc.metadata[k]) for k in ("width", "height", "duration", "codec") if doc.metadata.get(k)),
                confidence=0.8,
                domain="creative",
                source_path=doc.source_path,
            ))
        return out
