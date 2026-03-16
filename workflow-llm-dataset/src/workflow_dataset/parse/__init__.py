"""
Safe local document parsing and semantic extraction for the personal work agent.

Parses user documents locally, extracts structured signals (no raw dumping by default),
enriches the personal graph, and feeds the LLM corpus/SFT pipeline.
All parsing is config-gated and privacy-safe.
"""

from workflow_dataset.parse.document_models import (
    ParsedDocument,
    ParsedSection,
    ParsedTable,
    DocumentSignal,
    ExtractionPolicy,
)
from workflow_dataset.parse.document_router import route_and_parse_file
from workflow_dataset.parse.artifact_classifier import classify_artifact, is_supported_for_parsing

__all__ = [
    "ParsedDocument",
    "ParsedSection",
    "ParsedTable",
    "DocumentSignal",
    "ExtractionPolicy",
    "route_and_parse_file",
    "classify_artifact",
    "is_supported_for_parsing",
]
