"""Build canonical occupations from O*NET and SOC; every row has source_id."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.ingest.provenance import make_source_row

OCCUPATION_COLUMNS = [
    "occupation_id",
    "taxonomy_system",
    "occupation_code",
    "title",
    "description",
    "parent_group",
    "job_zone",
    "education_level",
    "source_id",
]


def _get_source_id_for_file(source_register: pd.DataFrame, source_name: str) -> str | None:
    """Resolve source_id from source_register by source_name (e.g. 'Occupation Data.txt')."""
    match = source_register[source_register["source_name"] == source_name]
    if match.empty:
        return None
    return str(match.iloc[0]["source_id"])


def _parent_group_from_onet_soc(code: str) -> str:
    """Derive parent group from O*NET-SOC code (e.g. 11-1011.00 -> 11-1011)."""
    if not code or not isinstance(code, str):
        return ""
    s = code.strip()
    if len(s) >= 7 and s[-3:] == ".00":
        return s[:-3]  # 11-1011.00 -> 11-1011
    return ""


def run_occupation_normalization(settings: Any) -> None:
    interim = Path(settings.paths.interim)
    processed = Path(settings.paths.processed)
    processed.mkdir(parents=True, exist_ok=True)

    # Load source_register to resolve source_id for each source file
    sr_path = interim / "source_register.parquet"
    if not sr_path.exists():
        return
    source_register = pd.read_parquet(sr_path)

    # O*NET Occupation Data
    occ_path = interim / "onet__occupation_data.parquet"
    jobzone_path = interim / "onet__job_zones.parquet"

    if not occ_path.exists():
        return

    occ_df = pd.read_parquet(occ_path)
    # Normalize column names (O*NET uses "O*NET-SOC Code", "Title", "Description")
    code_col = "O*NET-SOC Code" if "O*NET-SOC Code" in occ_df.columns else "onet_soc_code"
    title_col = "Title" if "Title" in occ_df.columns else "title"
    desc_col = "Description" if "Description" in occ_df.columns else "description"
    if code_col not in occ_df.columns:
        return

    source_id_occ = _get_source_id_for_file(source_register, "Occupation Data.txt")
    if source_id_occ is None:
        source_id_occ = stable_id("src", "onet/db_30_2_text/Occupation Data.txt", prefix="source")

    job_zone_map: dict[str, str] = {}
    if jobzone_path.exists():
        jz_df = pd.read_parquet(jobzone_path)
        jz_code = "O*NET-SOC Code" if "O*NET-SOC Code" in jz_df.columns else "onet_soc_code"
        jz_col = "Job Zone" if "Job Zone" in jz_df.columns else "job_zone"
        if jz_code in jz_df.columns and jz_col in jz_df.columns:
            for _, row in jz_df.iterrows():
                job_zone_map[str(row[jz_code]).strip()] = str(row[jz_col]).strip()

    rows: list[dict[str, Any]] = []
    for _, row in occ_df.iterrows():
        code = str(row[code_col]).strip() if pd.notna(row.get(code_col)) else ""
        if not code:
            continue
        title = str(row.get(title_col, "")).strip() if pd.notna(row.get(title_col)) else ""
        description = str(row.get(desc_col, "")).strip() if pd.notna(row.get(desc_col)) else ""
        occupation_id = stable_id("occ", code, prefix="occ")
        rows.append({
            "occupation_id": occupation_id,
            "taxonomy_system": "O*NET",
            "occupation_code": code,
            "title": title,
            "description": description,
            "parent_group": _parent_group_from_onet_soc(code),
            "job_zone": job_zone_map.get(code, ""),
            "education_level": "",
            "source_id": source_id_occ,
        })

    if not rows:
        return
    out_df = pd.DataFrame(rows)
    for col in OCCUPATION_COLUMNS:
        if col not in out_df.columns:
            out_df[col] = ""
    out_df = out_df[OCCUPATION_COLUMNS]
    out_df.to_parquet(processed / "occupations.parquet", index=False)
