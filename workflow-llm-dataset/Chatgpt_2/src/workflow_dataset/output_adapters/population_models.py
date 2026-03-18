"""
M14: Models for content-aware bundle population.

Bridges reviewed/refined artifact content into adapter outputs.
Local-only; provenance-aware; deterministic-first.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceContentSlice(BaseModel):
    """Extracted slice of content from a source artifact."""

    slice_id: str = Field(default="")
    source_artifact_ref: str = Field(default="")
    source_type: str = Field(default="", description="markdown, csv, json, text, html")
    heading: str = Field(default="")
    section_type: str = Field(default="", description="heading, table, checklist, narrative, summary")
    text: str = Field(default="")
    structured_rows: list[list[str]] = Field(default_factory=list)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance_refs: list[str] = Field(default_factory=list)


class PopulatedSection(BaseModel):
    """A section in a bundle file that was populated from source content."""

    section_id: str = Field(default="")
    adapter_type: str = Field(default="")
    target_file: str = Field(default="")
    section_name: str = Field(default="")
    populated_text: str = Field(default="")
    source_refs: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")


class PopulatedTablePlan(BaseModel):
    """Table/sheet plan populated from source (headers + rows)."""

    table_id: str = Field(default="")
    target_file: str = Field(default="")
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    created_utc: str = Field(default="")


class PopulationResult(BaseModel):
    """Result of populating a bundle from source content."""

    population_id: str = Field(default="")
    adapter_request_id: str = Field(default="")
    populated_sections: list[PopulatedSection] = Field(default_factory=list)
    populated_tables: list[PopulatedTablePlan] = Field(default_factory=list)
    fallback_used: bool = Field(default=False)
    created_utc: str = Field(default="")
