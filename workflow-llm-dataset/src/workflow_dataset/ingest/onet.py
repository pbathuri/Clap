"""Ingest all O*NET text tables into interim parquet and register sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.ingest.provenance import make_source_row


def _sanitize_stem(name: str) -> str:
    return name.replace(" ", "_").replace(",", "").replace(".", "_").lower()


def ingest_onet(settings) -> list[dict[str, Any]]:
    root = Path(settings.paths.raw_official) / "onet"
    out = Path(settings.paths.interim)
    out.mkdir(parents=True, exist_ok=True)

    # Discover all .txt files (including in subdirs like db_30_2_text/)
    txt_files = sorted(root.rglob("*.txt"))
    # Skip readme-style files
    skip = {"read me.txt", "readme.txt"}
    sources: list[dict[str, Any]] = []

    for txt in txt_files:
        if txt.name.lower() in skip:
            continue
        rel = txt.relative_to(root)
        try:
            df = pd.read_csv(txt, sep="\t", dtype=str, on_bad_lines="warn")
            if df.empty:
                continue
            stem = _sanitize_stem(txt.stem)
            parquet_name = f"onet__{stem}.parquet"
            parquet_path = out / parquet_name
            df.to_parquet(parquet_path, index=False)
            path_str = str(rel)
            sources.append(
                make_source_row(
                    source_name=txt.name,
                    source_type="occupation_database",
                    source_path_or_url=path_str,
                    publisher="O*NET / National Center for O*NET Development",
                    taxonomy_version="30.2",
                    publication_date="",
                    license="CC BY 4.0",
                    notes="O*NET database tab-delimited text",
                )
            )
        except Exception as exc:
            # Still register the file so QA can flag parse failure
            path_str = str(rel)
            sources.append(
                make_source_row(
                    source_name=txt.name,
                    source_type="occupation_database",
                    source_path_or_url=path_str,
                    publisher="O*NET",
                    taxonomy_version="30.2",
                    notes=f"INGEST_FAILED: {exc!s}",
                )
            )
    return sources
