"""Build source_register from ingested files; used by ingest base."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

SOURCE_REGISTER_COLUMNS = [
    "source_id",
    "source_name",
    "source_type",
    "source_path_or_url",
    "publisher",
    "taxonomy_version",
    "publication_date",
    "retrieval_date",
    "license",
    "notes",
]


def make_source_row(
    *,
    source_name: str,
    source_type: str,
    source_path_or_url: str,
    publisher: str = "",
    taxonomy_version: str = "",
    publication_date: str = "",
    retrieval_date: str | None = None,
    license: str = "",
    notes: str = "",
) -> dict[str, Any]:
    source_id = stable_id("src", source_path_or_url, prefix="source")
    return {
        "source_id": source_id,
        "source_name": source_name,
        "source_type": source_type,
        "source_path_or_url": source_path_or_url,
        "publisher": publisher,
        "taxonomy_version": taxonomy_version,
        "publication_date": publication_date or "",
        "retrieval_date": retrieval_date or utc_now_iso(),
        "license": license,
        "notes": notes,
    }


def write_source_register(rows: list[dict[str, Any]], out_path: Path) -> None:
    if not rows:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    for col in SOURCE_REGISTER_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[SOURCE_REGISTER_COLUMNS]
    df.to_parquet(out_path, index=False)
