"""Finance adapter: spreadsheets, reports, invoices, ledgers, planning docs."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.parse.adapters.base_adapter import BaseDomainAdapter, AdapterSignal
from workflow_dataset.parse.document_models import ParsedDocument
from workflow_dataset.setup.setup_models import ArtifactFamily

FINANCE_KEYWORDS = ["invoice", "ledger", "budget", "forecast", "reconcil", "tax", "expense", "fy", "q1", "q2", "monthly", "quarterly", "p&l", "balance"]


class FinanceAdapter(BaseDomainAdapter):
    @property
    def name(self) -> str:
        return "finance"

    @property
    def supported_families(self) -> list[ArtifactFamily]:
        return [ArtifactFamily.SPREADSHEET_TABLE, ArtifactFamily.TEXT_DOCUMENT]

    def process(self, doc: ParsedDocument) -> list[AdapterSignal]:
        out: list[AdapterSignal] = []
        path = Path(doc.source_path)
        name_lower = (path.name + " " + doc.summary).lower()
        if any(k in name_lower for k in FINANCE_KEYWORDS):
            out.append(AdapterSignal(
                signal_type="finance_document",
                value=path.name[:80],
                confidence=0.7,
                domain="finance",
                source_path=doc.source_path,
            ))
        for t in doc.tables:
            headers_lower = " ".join(t.headers).lower()
            if any(k in headers_lower for k in FINANCE_KEYWORDS):
                out.append(AdapterSignal(
                    signal_type="finance_schema",
                    value=t.headers[:15],
                    confidence=0.75,
                    domain="finance",
                    source_path=doc.source_path,
                    metadata={"sheet": t.sheet_name},
                ))
        return out
