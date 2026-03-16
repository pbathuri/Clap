"""Document adapter: text documents, headings, summaries."""

from __future__ import annotations

from workflow_dataset.parse.adapters.base_adapter import BaseDomainAdapter, AdapterSignal
from workflow_dataset.parse.document_models import ParsedDocument
from workflow_dataset.setup.setup_models import ArtifactFamily


class DocumentAdapter(BaseDomainAdapter):
    @property
    def name(self) -> str:
        return "document"

    @property
    def supported_families(self) -> list[ArtifactFamily]:
        return [ArtifactFamily.TEXT_DOCUMENT]

    def process(self, doc: ParsedDocument) -> list[AdapterSignal]:
        out: list[AdapterSignal] = []
        if doc.summary:
            out.append(AdapterSignal(
                signal_type="has_summary",
                value=doc.summary[:200],
                confidence=0.8,
                domain="document",
                source_path=doc.source_path,
                metadata={"length": len(doc.summary)},
            ))
        if doc.sections:
            headings = [s.heading for s in doc.sections if s.heading]
            if headings:
                out.append(AdapterSignal(
                    signal_type="heading_structure",
                    value=headings[:20],
                    confidence=0.7,
                    domain="document",
                    source_path=doc.source_path,
                ))
        return out
