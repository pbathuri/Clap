"""Build canonical industry (ISIC/NAICS) and SOC hierarchy tables; every row has source_id."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.normalize.occupations import run_occupation_normalization
from workflow_dataset.normalize.enrich import run_enrichment_normalization
from workflow_dataset.normalize.labor_market import run_labor_market_normalization

INDUSTRY_COLUMNS = [
    "industry_id",
    "taxonomy_system",
    "section_code",
    "division_code",
    "group_code",
    "class_code",
    "title",
    "description",
    "parent_id",
    "taxonomy_level",
    "taxonomy_version",
    "source_id",
]


def _get_source_id_for_file(source_register: pd.DataFrame, name_substr: str) -> str | None:
    m = source_register[source_register["source_name"].astype(str).str.contains(name_substr, case=False, na=False)]
    if m.empty:
        return None
    return str(m.iloc[0]["source_id"])


def run_normalization(settings: Any) -> None:
    run_taxonomy_normalization(settings)
    run_occupation_normalization(settings)
    run_enrichment_normalization(settings)
    run_labor_market_normalization(settings)


def run_taxonomy_normalization(settings: Any) -> None:
    interim = Path(settings.paths.interim)
    processed = Path(settings.paths.processed)
    processed.mkdir(parents=True, exist_ok=True)

    # Copy source_register to processed so exports have canonical source list
    sr_interim = interim / "source_register.parquet"
    if sr_interim.exists():
        pd.read_parquet(sr_interim).to_parquet(processed / "source_register.parquet", index=False)

    if not (interim / "source_register.parquet").exists():
        return
    source_register = pd.read_parquet(interim / "source_register.parquet")

    industry_rows: list[dict[str, Any]] = []

    # ISIC: any interim isic__*.parquet
    for f in interim.glob("isic__*.parquet"):
        try:
            df = pd.read_parquet(f)
            if df.empty:
                continue
            src_id = _get_source_id_for_file(source_register, f.stem) or stable_id("src", str(f.name), prefix="source")
            # Map common column names to schema; preserve originals
            for _, r in df.iterrows():
                row = {k: str(v) if pd.notna(v) else "" for k, v in r.items()}
                code = (row.get("Code") or row.get("code") or row.get("ISIC") or "") or ""
                title = (row.get("Title") or row.get("title") or row.get("Description") or "") or ""
                desc = (row.get("Description") or row.get("description") or "") or ""
                if not code and not title:
                    continue
                section = (row.get("Section") or row.get("section") or "") or (code[:1] if len(code) >= 1 else "")
                division = (row.get("Division") or row.get("division") or "") or (code[:2] if len(code) >= 2 else "")
                group = (row.get("Group") or row.get("group") or "") or (code[:3] if len(code) >= 3 else "")
                class_code = (row.get("Class") or row.get("class") or "") or code
                industry_id = stable_id("ind", "ISIC", code, prefix="ind")
                parent_id = ""
                if len(code) == 1:
                    taxonomy_level = "section"
                elif len(code) == 2:
                    taxonomy_level = "division"
                    parent_id = stable_id("ind", "ISIC", code[:1], prefix="ind")
                elif len(code) == 3:
                    taxonomy_level = "group"
                    parent_id = stable_id("ind", "ISIC", code[:2], prefix="ind")
                else:
                    taxonomy_level = "class"
                    parent_id = stable_id("ind", "ISIC", code[:3], prefix="ind") if len(code) >= 3 else ""
                industry_rows.append({
                    "industry_id": industry_id,
                    "taxonomy_system": "ISIC",
                    "section_code": section,
                    "division_code": division[:2] if len(division) >= 2 else division,
                    "group_code": group[:3] if len(group) >= 3 else group,
                    "class_code": class_code[:4] if len(class_code) >= 4 else class_code,
                    "title": title,
                    "description": desc,
                    "parent_id": parent_id,
                    "taxonomy_level": taxonomy_level,
                    "taxonomy_version": "Rev.4",
                    "source_id": src_id,
                })
        except Exception:
            continue

    # NAICS: any interim naics__*.parquet
    for f in interim.glob("naics__*.parquet"):
        try:
            df = pd.read_parquet(f)
            if df.empty:
                continue
            src_id = _get_source_id_for_file(source_register, f.stem) or stable_id("src", str(f.name), prefix="source")
            for _, r in df.iterrows():
                row = {k: str(v) if pd.notna(v) else "" for k, v in r.items()}
                code = (row.get("Code") or row.get("code") or row.get("NAICS") or row.get("naics_code") or "") or ""
                title = (row.get("Title") or row.get("title") or row.get("title_description") or "") or ""
                desc = (row.get("Description") or row.get("description") or "") or ""
                if not code and not title:
                    continue
                industry_id = stable_id("ind", "NAICS", code, prefix="ind")
                code_len = len(code.replace("-", "").replace(".", ""))
                if code_len <= 2:
                    taxonomy_level = "sector"
                    parent_id = ""
                elif code_len <= 3:
                    taxonomy_level = "subsector"
                    parent_id = stable_id("ind", "NAICS", code[:2], prefix="ind") if len(code) >= 2 else ""
                elif code_len <= 4:
                    taxonomy_level = "industry_group"
                    parent_id = stable_id("ind", "NAICS", code[:3], prefix="ind") if len(code) >= 3 else ""
                elif code_len <= 5:
                    taxonomy_level = "naics_industry"
                    parent_id = stable_id("ind", "NAICS", code[:4], prefix="ind") if len(code) >= 4 else ""
                else:
                    taxonomy_level = "national_industry"
                    parent_id = stable_id("ind", "NAICS", code[:5], prefix="ind") if len(code) >= 5 else ""
                industry_rows.append({
                    "industry_id": industry_id,
                    "taxonomy_system": "NAICS",
                    "section_code": "",
                    "division_code": code[:2] if len(code) >= 2 else "",
                    "group_code": code[:4] if len(code) >= 4 else "",
                    "class_code": code,
                    "title": title,
                    "description": desc,
                    "parent_id": parent_id,
                    "taxonomy_level": taxonomy_level,
                    "taxonomy_version": "2022",
                    "source_id": src_id,
                })
        except Exception:
            continue

    if industry_rows:
        ind_df = pd.DataFrame(industry_rows)
        for col in INDUSTRY_COLUMNS:
            if col not in ind_df.columns:
                ind_df[col] = ""
        ind_df = ind_df[INDUSTRY_COLUMNS]
        ind_df.to_parquet(processed / "industries.parquet", index=False)

    # SOC hierarchy: if we have soc__*.parquet, build taxonomy_soc (for Excel Taxonomy_SOC)
    soc_rows: list[dict[str, Any]] = []
    for f in interim.glob("soc__*.parquet"):
        try:
            df = pd.read_parquet(f)
            if df.empty:
                continue
            src_id = _get_source_id_for_file(source_register, f.stem) or stable_id("src", str(f.name), prefix="source")
            for _, r in df.iterrows():
                row = {k: str(v) if pd.notna(v) else "" for k, v in r.items()}
                code = (row.get("Code") or row.get("code") or row.get("SOC") or "") or ""
                title = (row.get("Title") or row.get("title") or "") or ""
                if not code and not title:
                    continue
                soc_rows.append({
                    "soc_code": code,
                    "title": title,
                    "parent_code": (row.get("Parent") or row.get("parent") or "") or "",
                    "source_id": src_id,
                })
        except Exception:
            continue
    if soc_rows:
        soc_df = pd.DataFrame(soc_rows)
        soc_df.to_parquet(processed / "taxonomy_soc.parquet", index=False)
