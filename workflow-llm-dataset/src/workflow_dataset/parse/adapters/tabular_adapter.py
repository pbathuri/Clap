"""Tabular adapter: spreadsheets, schemas, repeated column patterns."""

from __future__ import annotations

from workflow_dataset.parse.adapters.base_adapter import BaseDomainAdapter, AdapterSignal
from workflow_dataset.parse.document_models import ParsedDocument
from workflow_dataset.setup.setup_models import ArtifactFamily


class TabularAdapter(BaseDomainAdapter):
    @property
    def name(self) -> str:
        return "tabular"

    @property
    def supported_families(self) -> list[ArtifactFamily]:
        return [ArtifactFamily.SPREADSHEET_TABLE]

    def process(self, doc: ParsedDocument) -> list[AdapterSignal]:
        out: list[AdapterSignal] = []
        for t in doc.tables:
            if t.headers:
                out.append(AdapterSignal(
                    signal_type="schema_headers",
                    value=t.headers,
                    confidence=0.9,
                    domain="tabular",
                    source_path=doc.source_path,
                    metadata={"sheet": t.sheet_name, "rows": len(t.rows)},
                ))
        for s in doc.signals:
            if s.signal_type in ("schema_headers", "sheet_names"):
                out.append(AdapterSignal(
                    signal_type=s.signal_type,
                    value=s.value,
                    confidence=s.confidence,
                    domain="tabular",
                    source_path=doc.source_path,
                    metadata=s.metadata,
                ))
        return out
