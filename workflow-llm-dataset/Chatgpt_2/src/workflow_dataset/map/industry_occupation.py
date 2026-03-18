"""Build industry_occupation_map from official BLS matrix only. Use O*NET-SOC to NEM crosswalk to link to occupation_id."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.map.bls_crosswalk import bls_code_to_occupation_id

MAP_COLUMNS = [
    "map_id",
    "industry_id",
    "occupation_id",
    "mapping_basis",
    "strength_score",
    "source_id",
    "confidence_score",
    "review_status",
]

MAPPING_BASIS_OFFICIAL_MATRIX = "official_matrix"

# Interim parquet stems to use (in order of preference) for matrix data
MATRIX_STEMS = [
    "matrix_by_occupation",
    "national_employment_matrix",
    "matrix_by_industry",
]


def _normalize_soc_for_match(code: str) -> str:
    if not code or not isinstance(code, str):
        return ""
    s = re.sub(r"\s+", "", str(code).strip())
    if not s:
        return ""
    if re.match(r"^\d{2}-\d{4}\.\d{2}$", s):
        return s
    if re.match(r"^\d{2}-\d{4}$", s):
        return s + ".00"
    if len(s) >= 6 and s.isdigit():
        return s[:2] + "-" + s[2:6] + ".00"
    return s


def _get_source_id_for_file(sr: pd.DataFrame, path: Path) -> str:
    name = path.stem.replace("bls__", "").replace("_", " ")
    m = sr[sr["source_name"].astype(str).str.contains(name, case=False, na=False)]
    if not m.empty:
        return str(m.iloc[0]["source_id"])
    m = sr[sr["source_path_or_url"].astype(str).str.contains(path.name, na=False)]
    return "" if m.empty else str(m.iloc[0]["source_id"])


def _detect_bls_matrix_columns(df: pd.DataFrame) -> tuple[str | None, str | None, str | None]:
    """Return (naics_col, soc_col, emp_col)."""
    cols_lower = {c.lower(): c for c in df.columns}
    naics_col = None
    for k in ("naics", "industry code", "industry_code", "naics code", "industry"):
        if k in cols_lower:
            naics_col = cols_lower[k]
            break
    if not naics_col:
        for c in df.columns:
            if "industry" in c.lower() and "code" in c.lower():
                naics_col = c
                break
    soc_col = None
    for k in ("soc", "occupation code", "occupation_code", "soc code", "occupation"):
        if k in cols_lower:
            soc_col = cols_lower[k]
            break
    if not soc_col:
        for c in df.columns:
            if "occupation" in c.lower() and "code" in c.lower():
                soc_col = c
                break
    emp_col = None
    for k in ("emp", "employment", "jobs", "employment 2022", "emp_2022", "employment 2024", "employment 2034"):
        if k in cols_lower:
            emp_col = cols_lower[k]
            break
    if not emp_col and "employment" in str(cols_lower.keys()).lower():
        for c in df.columns:
            if "employment" in c.lower() or "emp" in c.lower():
                emp_col = c
                break
    return naics_col, soc_col, emp_col


def run_mapping(settings: Any) -> None:
    interim = Path(settings.paths.interim)
    processed = Path(settings.paths.processed)
    processed.mkdir(parents=True, exist_ok=True)

    # If none of the matrix parquets exist, write diagnostic and keep map empty
    matrix_paths = [interim / f"bls__{s}.parquet" for s in MATRIX_STEMS]
    if not any(p.exists() for p in matrix_paths):
        _write_empty_map(processed)
        pd.DataFrame([{"reason": "no_matrix_source", "message": "None of bls__matrix_by_occupation, bls__national_employment_matrix, bls__matrix_by_industry found."}]).to_parquet(
            processed / "bls_no_matrix_source.parquet", index=False
        )
        return

    sr_path = interim / "source_register.parquet"
    occ_path = processed / "occupations.parquet"
    ind_path = processed / "industries.parquet"
    if not sr_path.exists() or not occ_path.exists():
        _write_empty_map(processed)
        return

    source_register = pd.read_parquet(sr_path)
    occupations = pd.read_parquet(occ_path)
    occ_code_to_id = occupations.set_index(occupations["occupation_code"].astype(str).str.strip())["occupation_id"].to_dict()

    # Crosswalk: BLS occupation code -> occupation_id (and to O*NET-SOC)
    bls_to_occ_id, _ = bls_code_to_occupation_id(interim, processed)
    # Fallback: direct O*NET-SOC match
    for code, oid in occ_code_to_id.items():
        bls_to_occ_id.setdefault(code, oid)
        bls_to_occ_id.setdefault(_normalize_soc(code), oid)

    naics_to_industry_id: dict[str, str] = {}
    if ind_path.exists():
        ind = pd.read_parquet(ind_path)
        if not ind.empty and "taxonomy_system" in ind.columns:
            naics_df = ind[ind["taxonomy_system"].astype(str) == "NAICS"]
            for _, r in naics_df.iterrows():
                for col in ("class_code", "division_code", "group_code"):
                    code = str(r.get(col, "")).strip() if pd.notna(r.get(col)) else ""
                    if code:
                        naics_to_industry_id[code] = str(r["industry_id"])

    map_rows: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    unmapped_occ_codes: set[str] = set()
    unmapped_naics: set[str] = set()
    found_matrix_with_columns = False

    for stem in MATRIX_STEMS:
        path = interim / f"bls__{stem}.parquet"
        if not path.exists():
            continue
        try:
            df = pd.read_parquet(path)
            if df.empty or len(df.columns) < 2:
                continue
            naics_col, soc_col, emp_col = _detect_bls_matrix_columns(df)
            if not naics_col or not soc_col:
                continue
            found_matrix_with_columns = True
            src_id = _get_source_id_for_file(source_register, path)
            if not src_id:
                src_id = stable_id("src", str(path), prefix="source")

            for _, r in df.iterrows():
                naics_raw = str(r.get(naics_col, "")).strip() if pd.notna(r.get(naics_col)) else ""
                soc_raw = str(r.get(soc_col, "")).strip() if pd.notna(r.get(soc_col)) else ""
                if not soc_raw:
                    continue
                soc_norm = _normalize_soc_for_match(soc_raw)
                occ_id = bls_to_occ_id.get(soc_norm) or bls_to_occ_id.get(soc_raw)
                if not occ_id:
                    unmapped_occ_codes.add(soc_raw)
                    unmapped_occ_codes.add(soc_norm)
                    continue
                if not naics_raw:
                    continue
                industry_id = naics_to_industry_id.get(naics_raw)
                if not industry_id:
                    industry_id = stable_id("ind", "NAICS", naics_raw, prefix="ind")
                    unmapped_naics.add(naics_raw)
                key = (industry_id, occ_id)
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                try:
                    strength = float(r.get(emp_col, 1.0)) if emp_col and pd.notna(r.get(emp_col)) else 1.0
                except (TypeError, ValueError):
                    strength = 1.0
                map_id = stable_id("map", industry_id, occ_id, prefix="map")
                map_rows.append({
                    "map_id": map_id,
                    "industry_id": industry_id,
                    "occupation_id": occ_id,
                    "mapping_basis": MAPPING_BASIS_OFFICIAL_MATRIX,
                    "strength_score": strength,
                    "source_id": src_id,
                    "confidence_score": "1.0",
                    "review_status": "accepted",
                })
        except Exception:
            continue

    if map_rows:
        out = pd.DataFrame(map_rows)[MAP_COLUMNS]
        out.to_parquet(processed / "industry_occupation_map.parquet", index=False)
    else:
        _write_empty_map(processed)

    # When no real matrix workbook was used, emit marker for QA
    if not found_matrix_with_columns:
        pd.DataFrame([{"reason": "no_real_bls_matrix_source", "message": "No BLS workbook with industry-occupation matrix columns found; industry_occupation_map is empty."}]).to_parquet(
            processed / "bls_no_matrix_source.parquet", index=False
        )

    # Write unmapped codes for QA
    if unmapped_occ_codes:
        pd.DataFrame({"code": sorted(unmapped_occ_codes)}).to_parquet(
            processed / "bls_unmapped_occupation_codes.parquet", index=False
        )
    if unmapped_naics:
        pd.DataFrame({"code": sorted(unmapped_naics)}).to_parquet(
            processed / "bls_unmapped_industry_codes.parquet", index=False
        )


def _write_empty_map(processed: Path) -> None:
    pd.DataFrame(columns=MAP_COLUMNS).to_parquet(processed / "industry_occupation_map.parquet", index=False)
