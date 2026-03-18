"""Catalog private example documents; no parsing yet."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.ingest.provenance import make_source_row


def ingest_private_docs(settings) -> list[dict[str, Any]]:
    root = Path(settings.paths.raw_private)
    sources: list[dict[str, Any]] = []
    if not root.exists():
        return sources
    exts = (".pdf", ".doc", ".docx", ".xlsx", ".csv", ".txt")
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            sources.append(
                make_source_row(
                    source_name=f.name,
                    source_type="private_documents",
                    source_path_or_url=str(f.relative_to(root)),
                    publisher="",
                    notes="Catalog only; not parsed",
                )
            )
    return sources
