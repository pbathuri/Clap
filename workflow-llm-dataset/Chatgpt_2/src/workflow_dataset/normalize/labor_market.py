"""Build labor_market.parquet from BLS occupational projections Table 1.2 (and related BLS). Use O*NET-SOC to NEM crosswalk for occupation_id."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.map.bls_crosswalk import bls_code_to_occupation_id

logger = logging.getLogger(__name__)

LABOR_COLUMNS = [
    "labor_id",
    "occupation_id",
    "employment",
    "median_pay",
    "projected_growth",
    "openings",
    "geography",
    "year",
    "source_id",
]


def _normalize_soc(code: str) -> str:
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


def _get_source_id(sr: pd.DataFrame, path: Path) -> str:
    name = path.stem.replace("_", " ")
    m = sr[sr["source_name"].astype(str).str.contains(name, case=False, na=False)]
    if not m.empty:
        return str(m.iloc[0]["source_id"])
    m = sr[sr["source_path_or_url"].astype(str).str.contains(path.name, na=False)]
    return "" if m.empty else str(m.iloc[0]["source_id"])


def _normalized_lower(col_name: str) -> str:
    """Case-insensitive normalized string for substring matching."""
    return " ".join(str(col_name).lower().split())


def _column_contains(col_name: str, substring: str) -> bool:
    """True if col_name (normalized, lower) contains the substring."""
    return substring in _normalized_lower(col_name)


def _column_contains_any(col_name: str, substrings: list[str]) -> bool:
    """True if col_name (normalized, lower) contains any of the substrings."""
    n = _normalized_lower(col_name)
    return any(s in n for s in substrings)


def _detect_columns(df: pd.DataFrame) -> dict[str, str | None]:
    """Explicit column matching for Table 1.2-like files, with exclusions. Never use 'title' or 'distribution' as employment."""
    cols = list(df.columns)
    out = {"soc": None, "employment": None, "wage": None, "median": None, "growth": None, "openings": None, "year": None}

    # soc -> only column containing "national employment matrix code"
    for c in cols:
        if _column_contains(c, "national employment matrix code"):
            out["soc"] = c
            break

    # employment -> column containing "employment, 2024"; exclude columns containing "title" or "distribution"
    for c in cols:
        if _column_contains(c, "employment, 2024"):
            if not _column_contains_any(c, ["title", "distribution"]):
                out["employment"] = c
                break

    # median_pay -> column containing "median annual wage"
    for c in cols:
        if _column_contains(c, "median annual wage"):
            out["wage"] = c
            out["median"] = c
            break

    # projected_growth -> column containing "employment change, percent"
    for c in cols:
        if _column_contains(c, "employment change, percent"):
            out["growth"] = c
            break

    # openings -> column containing "occupational openings"
    for c in cols:
        if _column_contains(c, "occupational openings"):
            out["openings"] = c
            break

    # year
    for c in cols:
        if _column_contains_any(c, ["year", "data year"]):
            out["year"] = c
            break

    return out


# Only these Table 1.2 sources; do not scan other bls__*.parquet files
LABOR_TABLE_1_2_STEMS = ["occupational_projections_table_1_2", "occupation_xlsx_table_1_2"]

OCCUPATION_TYPE_COLUMN = "Occupation type"
LINE_ITEM_VALUE = "Line item"


def run_labor_market_normalization(settings: Any) -> None:
    interim = Path(settings.paths.interim)
    processed = Path(settings.paths.processed)
    processed.mkdir(parents=True, exist_ok=True)
    sr_path = interim / "source_register.parquet"
    occ_path = processed / "occupations.parquet"
    if not sr_path.exists() or not occ_path.exists():
        pd.DataFrame(columns=LABOR_COLUMNS).to_parquet(processed / "labor_market.parquet", index=False)
        return

    sr = pd.read_parquet(sr_path)
    occ = pd.read_parquet(occ_path)
    occ_code_to_id = occ.set_index(occ["occupation_code"].astype(str).str.strip())["occupation_id"].to_dict()

    # Crosswalk: BLS occupation code -> occupation_id
    bls_to_occ_id, _ = bls_code_to_occupation_id(interim, processed)
    for code, oid in occ_code_to_id.items():
        bls_to_occ_id.setdefault(code, oid)
        bls_to_occ_id.setdefault(_normalize_soc(code), oid)

    rows: list[dict[str, Any]] = []
    unmapped_occ_codes: set[str] = set()

    # Restrict to Table 1.2 parquets only (do not scan every bls__*.parquet)
    paths_to_scan = [interim / f"bls__{s}.parquet" for s in LABOR_TABLE_1_2_STEMS if (interim / f"bls__{s}.parquet").exists()]
    logger.info("labor_market: scanned source stems=%s", [p.stem.replace("bls__", "") for p in paths_to_scan])

    for path in paths_to_scan:
        if not path.exists():
            continue
        try:
            df = pd.read_parquet(path)
            if df.empty:
                continue
            rows_before_filter = len(df)

            det = _detect_columns(df)
            soc_col = det["soc"]
            if not soc_col:
                logger.debug("labor_market: skip %s (no soc column detected)", path.name)
                continue

            logger.info("labor_market: %s selected_columns=%s", path.name, {k: v for k, v in det.items() if v is not None})

            # Keep only rows where Occupation type == "Line item" if column exists
            occ_type_col = None
            if OCCUPATION_TYPE_COLUMN in df.columns:
                occ_type_col = OCCUPATION_TYPE_COLUMN
            else:
                for c in df.columns:
                    if _normalized_lower(c) == "occupation type":
                        occ_type_col = c
                        break
            if occ_type_col is not None:
                df = df[df[occ_type_col].astype(str).str.strip().str.lower() == LINE_ITEM_VALUE.lower()].copy()
                df = df.reset_index(drop=True)
            rows_after_filter = len(df)
            logger.info("labor_market: %s rows before line-item filter=%s after=%s", path.name, rows_before_filter, rows_after_filter)

            src_id = _get_source_id(sr, path)
            if not src_id:
                src_id = stable_id("src", str(path), prefix="source")
            emp_col = det["employment"]
            wage_col = det["wage"] or det["median"]
            growth_col = det["growth"]
            openings_col = det["openings"]
            year_col = det["year"]

            stem = path.stem.replace("bls__", "")
            default_year = "2024" if (not year_col and stem in LABOR_TABLE_1_2_STEMS) else ""

            rows_before_mapping = len(rows)
            for _, r in df.iterrows():
                soc_raw = str(r.get(soc_col, "")).strip() if pd.notna(r.get(soc_col)) else ""
                if not soc_raw:
                    continue
                soc_norm = _normalize_soc(soc_raw)
                occ_id = bls_to_occ_id.get(soc_norm) or bls_to_occ_id.get(soc_raw)
                if not occ_id:
                    unmapped_occ_codes.add(soc_raw)
                    unmapped_occ_codes.add(soc_norm)
                    continue
                # Preserve decimal strings for employment and openings (do not cast to int)
                try:
                    v = r.get(emp_col)
                    employment = str(float(v)) if emp_col and v is not None and pd.notna(v) and str(v).strip() != "" else ""
                except (TypeError, ValueError):
                    employment = ""
                try:
                    median_pay = str(float(r.get(wage_col, 0) or 0)) if wage_col and r.get(wage_col) is not None else ""
                except (TypeError, ValueError):
                    median_pay = ""
                try:
                    projected_growth = str(float(r.get(growth_col, 0) or 0)) if growth_col and r.get(growth_col) is not None else ""
                except (TypeError, ValueError):
                    projected_growth = ""
                try:
                    v = r.get(openings_col)
                    openings = str(float(v)) if openings_col and v is not None and pd.notna(v) and str(v).strip() != "" else ""
                except (TypeError, ValueError):
                    openings = ""
                year = str(r.get(year_col, "")).strip() if year_col and pd.notna(r.get(year_col)) else default_year
                labor_id = stable_id("labor", occ_id, path.stem, employment or year, prefix="labor")
                rows.append({
                    "labor_id": labor_id,
                    "occupation_id": occ_id,
                    "employment": employment,
                    "median_pay": median_pay,
                    "projected_growth": projected_growth,
                    "openings": openings,
                    "geography": "US",
                    "year": year,
                    "source_id": src_id,
                })
            rows_after_mapping = len(rows)
            logger.info("labor_market: %s rows after occupation_id mapping=%s", path.name, rows_after_mapping - rows_before_mapping)
        except Exception:
            continue

    logger.info("labor_market: total rows=%s unmapped_occupation_codes=%s", len(rows), len(unmapped_occ_codes))

    if rows:
        out = pd.DataFrame(rows)
        for col in LABOR_COLUMNS:
            if col not in out.columns:
                out[col] = ""
        out = out[LABOR_COLUMNS]
        out.to_parquet(processed / "labor_market.parquet", index=False)
    else:
        pd.DataFrame(columns=LABOR_COLUMNS).to_parquet(processed / "labor_market.parquet", index=False)

    if unmapped_occ_codes:
        pd.DataFrame({"code": sorted(unmapped_occ_codes)}).to_parquet(
            processed / "labor_unmapped_occupation_codes.parquet", index=False
        )
