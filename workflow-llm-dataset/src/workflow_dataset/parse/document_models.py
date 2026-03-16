"""
Unified models for parsed documents and extracted signals.

Used by low-level parsers, artifact interpreters, and domain adapters.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ExtractionPolicy(str, Enum):
    """How much content to extract (privacy-safe defaults)."""
    METADATA_ONLY = "metadata_only"
    SUMMARIES = "summaries"
    SIGNALS_AND_SUMMARIES = "signals_and_summaries"
    FULL_TEXT = "full_text"  # Config-gated; avoid by default


class ParsedSection(BaseModel):
    """A section of a document (e.g. heading + content)."""
    heading: str = Field(default="")
    content: str = Field(default="")
    level: int = Field(default=1, ge=1, le=6)


class ParsedTable(BaseModel):
    """A table extracted from a document or spreadsheet."""
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    sheet_name: str = Field(default="")
    source_path: str = Field(default="")


class DocumentSignal(BaseModel):
    """A structured signal extracted from a document (for graph/LLM, not raw content)."""
    signal_type: str = Field(..., description="e.g. heading_template, schema_hash, deliverable_shape")
    value: str | float | int | list[str] | dict[str, Any] = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_path: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    """Result of parsing a single document/file."""
    source_path: str = Field(..., description="Absolute path")
    artifact_family: str = Field(default="unknown", description="text_document, spreadsheet_table, etc.")
    title: str = Field(default="")
    summary: str = Field(default="", description="Short summary if policy allows")
    sections: list[ParsedSection] = Field(default_factory=list)
    tables: list[ParsedTable] = Field(default_factory=list)
    signals: list[DocumentSignal] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict, description="mtime, size, format, etc.")
    policy_used: ExtractionPolicy = Field(default=ExtractionPolicy.SIGNALS_AND_SUMMARIES)
    error: str = Field(default="", description="If parse failed")
    raw_text_snippet: str = Field(default="", description="Optional bounded snippet; empty by default")
