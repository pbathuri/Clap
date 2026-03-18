"""Ops adapter: SOPs, runbooks, templates, recurring workflows, operations artifacts."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.parse.adapters.base_adapter import BaseDomainAdapter, AdapterSignal
from workflow_dataset.parse.document_models import ParsedDocument
from workflow_dataset.setup.setup_models import ArtifactFamily

OPS_KEYWORDS = ["sop", "runbook", "process", "operations", "template", "recurring", "weekly", "daily", "checklist", "procedure", "workflow"]


class OpsAdapter(BaseDomainAdapter):
    @property
    def name(self) -> str:
        return "ops"

    @property
    def supported_families(self) -> list[ArtifactFamily]:
        return [ArtifactFamily.TEXT_DOCUMENT, ArtifactFamily.SPREADSHEET_TABLE, ArtifactFamily.PROJECT_DIRECTORY]

    def process(self, doc: ParsedDocument) -> list[AdapterSignal]:
        out: list[AdapterSignal] = []
        path = Path(doc.source_path)
        name_lower = (path.name + " " + doc.summary).lower()
        if any(k in name_lower for k in OPS_KEYWORDS):
            out.append(AdapterSignal(
                signal_type="ops_artifact",
                value=path.name[:80],
                confidence=0.7,
                domain="ops",
                source_path=doc.source_path,
            ))
        if doc.artifact_family == ArtifactFamily.PROJECT_DIRECTORY.value:
            if any(k in path.name.lower() for k in OPS_KEYWORDS):
                out.append(AdapterSignal(
                    signal_type="ops_project",
                    value=path.name,
                    confidence=0.6,
                    domain="ops",
                    source_path=doc.source_path,
                ))
        return out
