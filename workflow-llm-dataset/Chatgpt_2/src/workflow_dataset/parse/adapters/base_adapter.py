"""
Base domain adapter: declare supported families, inspect content, emit signals.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from workflow_dataset.parse.document_models import ParsedDocument
from workflow_dataset.setup.setup_models import ArtifactFamily


class AdapterSignal(BaseModel):
    """Structured signal emitted by an adapter (for graph/LLM)."""
    signal_type: str = Field(...)
    value: str | float | list[str] | dict[str, Any] = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    domain: str = Field(default="")
    source_path: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseDomainAdapter(ABC):
    """Base for domain adapters. Subclass and implement process()."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter id, e.g. creative, finance."""
        pass

    @property
    def supported_families(self) -> list[ArtifactFamily]:
        """Artifact families this adapter can interpret."""
        return []

    def can_handle(self, doc: ParsedDocument) -> bool:
        """True if this adapter should process this document."""
        try:
            fam = ArtifactFamily(doc.artifact_family)
            return fam in self.supported_families
        except ValueError:
            return False

    @abstractmethod
    def process(self, doc: ParsedDocument) -> list[AdapterSignal]:
        """
        Inspect document and emit signals. Deterministic; no side effects.
        Do not store raw private content.
        """
        pass

    def infer_domain_relevance(self, doc: ParsedDocument) -> float:
        """Return 0.0–1.0 relevance to this adapter's domain."""
        if not self.can_handle(doc):
            return 0.0
        signals = self.process(doc)
        if not signals:
            return 0.3
        return min(1.0, 0.3 + 0.1 * len(signals))
