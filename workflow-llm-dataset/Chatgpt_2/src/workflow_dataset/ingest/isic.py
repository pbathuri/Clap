"""Ingest ISIC hierarchy files into interim parquet and register sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.ingest.provenance import make_source_row


def ingest_isic(settings) -> list[dict[str, Any]]:
    root = Path(settings.paths.raw_official) / "isic"
    out = Path(settings.paths.interim)
    out.mkdir(parents=True, exist_ok=True)
    sources: list[dict[str, Any]] = []
    for f in root.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in (".csv", ".xlsx", ".xls"):
            continue
        try:
            if f.suffix.lower() == ".csv":
                df = pd.read_csv(f, dtype=str)
            else:
                df = pd.read_excel(f, dtype=str)
            if df.empty:
                continue
            rel = f.relative_to(root)
            stem = f.stem.replace(" ", "_").replace(".", "_")
            parquet_path = out / f"isic__{stem}.parquet"
            df.to_parquet(parquet_path, index=False)
            sources.append(
                make_source_row(
                    source_name=f.name,
                    source_type="taxonomy",
                    source_path_or_url=str(rel),
                    publisher="UNSD",
                    taxonomy_version="Rev.4",
                    notes="ISIC",
                )
            )
        except Exception as exc:
            sources.append(
                make_source_row(
                    source_name=f.name,
                    source_type="taxonomy",
                    source_path_or_url=str(f.relative_to(root)),
                    publisher="UNSD",
                    notes=f"INGEST_FAILED: {exc!s}",
                )
            )
    return sources
