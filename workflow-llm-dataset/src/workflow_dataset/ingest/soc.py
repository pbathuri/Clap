"""Ingest SOC hierarchy files into interim parquet and register sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.ingest.provenance import make_source_row


def ingest_soc(settings) -> list[dict[str, Any]]:
    root = Path(settings.paths.raw_official) / "soc"
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
            parquet_path = out / f"soc__{stem}.parquet"
            df.to_parquet(parquet_path, index=False)
            sources.append(
                make_source_row(
                    source_name=f.name,
                    source_type="taxonomy",
                    source_path_or_url=str(rel),
                    publisher="BLS",
                    taxonomy_version="2018",
                    notes="SOC",
                )
            )
        except Exception as exc:
            sources.append(
                make_source_row(
                    source_name=f.name,
                    source_type="taxonomy",
                    source_path_or_url=str(rel),
                    publisher="BLS",
                    notes=f"INGEST_FAILED: {exc!s}",
                )
            )
    return sources
