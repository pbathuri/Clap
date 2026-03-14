from __future__ import annotations

from pathlib import Path

import pandas as pd

from workflow_dataset.ingest.isic import ingest_isic
from workflow_dataset.ingest.naics import ingest_naics
from workflow_dataset.ingest.soc import ingest_soc
from workflow_dataset.ingest.onet import ingest_onet
from workflow_dataset.ingest.bls import ingest_bls
from workflow_dataset.ingest.esco import ingest_esco
from workflow_dataset.ingest.private_docs import ingest_private_docs
from workflow_dataset.ingest.provenance import SOURCE_REGISTER_COLUMNS, write_source_register


def run_ingestion(settings) -> None:
    all_sources: list[dict] = []
    all_sources.extend(ingest_isic(settings))
    all_sources.extend(ingest_naics(settings))
    all_sources.extend(ingest_soc(settings))
    all_sources.extend(ingest_onet(settings))
    all_sources.extend(ingest_bls(settings))
    all_sources.extend(ingest_esco(settings))
    all_sources.extend(ingest_private_docs(settings))

    interim = Path(settings.paths.interim)
    interim.mkdir(parents=True, exist_ok=True)
    if all_sources:
        # Deduplicate by source_id (keep first)
        df = pd.DataFrame(all_sources)
        for col in SOURCE_REGISTER_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[SOURCE_REGISTER_COLUMNS].drop_duplicates(subset=["source_id"], keep="first")
        write_source_register(df.to_dict("records"), interim / "source_register.parquet")
