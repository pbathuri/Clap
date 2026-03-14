"""Ingest ESCO CSV files into interim parquet and register sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.ingest.provenance import make_source_row


def ingest_esco(settings) -> list[dict[str, Any]]:
    root = Path(settings.paths.raw_official) / "esco"
    out = Path(settings.paths.interim)
    out.mkdir(parents=True, exist_ok=True)
    sources: list[dict[str, Any]] = []
    if not root.exists():
        return sources
    for f in root.rglob("*.csv"):
        try:
            df = pd.read_csv(f, dtype=str, on_bad_lines="warn")
            if df.empty:
                continue
            rel = f.relative_to(root)
            stem = f.stem.replace(" ", "_").replace(".", "_")
            parquet_path = out / f"esco__{stem}.parquet"
            df.to_parquet(parquet_path, index=False)
            sources.append(
                make_source_row(
                    source_name=f.name,
                    source_type="skills_graph",
                    source_path_or_url=str(rel),
                    publisher="European Commission",
                    taxonomy_version="1.2.1",
                    notes="ESCO",
                )
            )
        except Exception as exc:
            sources.append(
                make_source_row(
                    source_name=f.name,
                    source_type="skills_graph",
                    source_path_or_url=str(f.relative_to(root)),
                    publisher="European Commission",
                    notes=f"INGEST_FAILED: {exc!s}",
                )
            )
    return sources
