"""Ingest BLS files with workbook-type detection and BLS-style header detection. Register every file in source_register."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.ingest.provenance import make_source_row

logger = logging.getLogger(__name__)

# Strict naming: filename -> parquet stem. Do NOT alias occupation.xlsx as matrix (it is projections).
BLS_FILE_TO_STEM = {
    "bls_matrix_by_occupation.xlsx": "matrix_by_occupation",
    "bls_matrix_by_industry.xlsx": "matrix_by_industry",
    "bls_national_employment_matrix.xlsx": "national_employment_matrix",
    "bls_occupational_projections_table_1_2.xlsx": "occupational_projections_table_1_2",
    "bls_industry_employment_directory.xlsx": "industry_employment_directory",
    "bls_occupational_employment_directory.xlsx": "occupational_employment_directory",
    "bls_onet_soc_to_nem_crosswalk.xlsx": "onet_soc_to_nem_crosswalk",
}

# occupation.xlsx is the occupational projections workbook (Table 1.1, 1.2, etc.) — not the matrix.
# Use distinct stem so we don't overwrite bls_occupational_projections_table_1_2.xlsx if both exist.
OCCUPATION_XLSX_PROJECTIONS_STEM = "occupation_xlsx_table_1_2"

# Sheet names to skip (no data)
SKIP_SHEET_NAMES = {"index", "index sheet", "contents", "toc"}

# Expected label substrings for header detection (lowercase)
MATRIX_LABELS = ["naics", "industry code", "soc", "occupation code", "employment", "emp "]
PROJECTIONS_LABELS = ["soc", "occupation", "employment", "median", "wage", "growth", "openings", "annual"]


def _normalize_column_name(c: Any) -> str:
    s = str(c).strip() if c is not None and pd.notna(c) else ""
    return re.sub(r"\s+", " ", s).strip()


def _row_matches_labels(row: pd.Series, labels: list[str], min_matches: int = 2) -> bool:
    """True if at least min_matches of labels appear in the row (cell values, case-insensitive)."""
    row_str = " ".join(_normalize_column_name(v).lower() for v in row.dropna().astype(str))
    return sum(1 for L in labels if L in row_str) >= min_matches


def _detect_header_row(df_raw: pd.DataFrame, expected_labels: list[str], min_matches: int = 2) -> int:
    """Scan first 15 rows for a row that looks like a header (contains expected labels). Returns 0-based row index or 0."""
    n_scan = min(15, len(df_raw))
    for i in range(n_scan):
        if _row_matches_labels(df_raw.iloc[i], expected_labels, min_matches):
            return i
    return 0


def _read_excel_sheets(
    path: Path,
    sheet_name: str | int | None = None,
    expected_labels: list[str] | None = None,
) -> tuple[pd.DataFrame | None, str, int]:
    """
    Read Excel with BLS-style header detection. Skips Index sheets.
    Returns (dataframe or None, chosen_sheet_name, header_row_index).
    """
    try:
        xl = pd.ExcelFile(path)
        sheet_names = [s for s in xl.sheet_names if s.strip() and s.strip().lower() not in SKIP_SHEET_NAMES]
        if not sheet_names:
            logger.debug("BLS %s: no data sheets after skipping Index etc.", path.name)
            return None, "", 0

        labels = expected_labels or (PROJECTIONS_LABELS + MATRIX_LABELS)

        # If specific sheet requested, use it; else iterate
        to_try: list[str] = []
        if sheet_name is not None:
            if isinstance(sheet_name, int):
                if 0 <= sheet_name < len(xl.sheet_names):
                    to_try = [xl.sheet_names[sheet_name]]
            elif sheet_name in xl.sheet_names:
                to_try = [sheet_name]
        if not to_try:
            to_try = sheet_names

        for name in to_try:
            if name.strip().lower() in SKIP_SHEET_NAMES:
                continue
            try:
                df_raw = pd.read_excel(xl, sheet_name=name, header=None, dtype=str)
            except Exception as e:
                logger.debug("BLS %s sheet %s read error: %s", path.name, name, e)
                continue
            if df_raw.empty or len(df_raw) < 2:
                continue
            header_row = _detect_header_row(df_raw, labels)
            df = pd.read_excel(xl, sheet_name=name, header=header_row, dtype=str)
            df.columns = [_normalize_column_name(c) for c in df.columns]
            df = df.dropna(how="all").reset_index(drop=True)
            if df.empty or len(df.columns) < 2:
                continue
            return df, name, header_row
        # Fallback: first data sheet with header=0
        for name in sheet_names:
            try:
                df = pd.read_excel(xl, sheet_name=name, header=0, dtype=str)
                df.columns = [_normalize_column_name(c) for c in df.columns]
                df = df.dropna(how="all").reset_index(drop=True)
                if not df.empty and len(df.columns) >= 2:
                    return df, name, 0
            except Exception:
                continue
        return None, "", 0
    except Exception as e:
        logger.debug("BLS _read_excel_sheets %s: %s", path.name, e)
        return None, "", 0


def _classify_workbook_by_sheets(path: Path) -> str:
    """Return 'projections' | 'matrix' | 'directory' | 'other' based on sheet names."""
    try:
        xl = pd.ExcelFile(path)
        names_lower = " ".join(s.lower() for s in xl.sheet_names)
        if "table 1.2" in names_lower or "table 1.1" in names_lower or "occupational projections" in names_lower:
            return "projections"
        if "matrix" in names_lower or "employment matrix" in names_lower:
            return "matrix"
        if "directory" in names_lower or "index" in names_lower:
            return "directory"
        return "other"
    except Exception:
        return "other"


def _classify_workbook_by_content(df: pd.DataFrame) -> str:
    """Return 'matrix' if columns look like industry-occupation matrix (NAICS + SOC + employment)."""
    cols_lower = " ".join(str(c).lower() for c in df.columns)
    has_naics = "naics" in cols_lower or "industry code" in cols_lower
    has_soc = "soc" in cols_lower or "occupation code" in cols_lower
    has_emp = "employment" in cols_lower or "emp " in cols_lower
    if has_naics and has_soc and has_emp:
        return "matrix"
    return "other"


def _find_table_1_2_sheet(path: Path) -> str | None:
    """Return sheet name that contains 'Table 1.2' or similar, else None."""
    try:
        xl = pd.ExcelFile(path)
        for name in xl.sheet_names:
            if "1.2" in name or "table 1.2" in name.lower():
                return name
        for name in xl.sheet_names:
            if "occupational" in name.lower() and "projection" in name.lower():
                return name
        return None
    except Exception:
        return None


# Header-like substrings that indicate the first data row is actually the real header (BLS Table 1.2)
TABLE_1_2_HEADER_MARKERS = [
    "national employment matrix code",
    "national employment matrix title",
    "employment, 2024",
    "employment change, percent",
    "occupational openings",
    "median annual wage",
]


def _first_row_looks_like_header(df: pd.DataFrame) -> bool:
    """True if first row contains header-like values (e.g. '2024 National Employment Matrix code')."""
    if df.empty or len(df) < 1:
        return False
    row_str = " ".join(str(v).lower() for v in df.iloc[0].dropna().astype(str))
    return any(m in row_str for m in TABLE_1_2_HEADER_MARKERS)


def _count_unnamed_columns(df: pd.DataFrame) -> int:
    return sum(1 for c in df.columns if str(c).strip().startswith("Unnamed") or str(c).strip() == "")


def _parse_occupation_xlsx_table_1_2(path: Path) -> tuple[pd.DataFrame | None, str, int]:
    """Parse occupation.xlsx from Table 1.2 sheet. Returns (df, chosen_sheet_name, header_row)."""
    sheet = _find_table_1_2_sheet(path)
    if not sheet:
        logger.debug("BLS %s: no Table 1.2 sheet found; sheets: %s", path.name, pd.ExcelFile(path).sheet_names)
        df, chosen, header_row = _read_excel_sheets(path, expected_labels=PROJECTIONS_LABELS)
    else:
        df, chosen, header_row = _read_excel_sheets(path, sheet_name=sheet, expected_labels=PROJECTIONS_LABELS)
    if df is None or df.empty:
        return None, chosen if df is None else "", header_row

    # Promote first data row to column headers if BLS put the real header there
    many_unnamed = _count_unnamed_columns(df) >= 3
    first_row_header_like = _first_row_looks_like_header(df)
    if many_unnamed or first_row_header_like:
        new_columns = [_normalize_column_name(v) for v in df.iloc[0].values]
        # Ensure unique column names (append _1, _2 for duplicates)
        seen: dict[str, int] = {}
        unique_cols = []
        for c in new_columns:
            if not c:
                c = "unnamed"
            if c in seen:
                seen[c] += 1
                c = f"{c}_{seen[c]}"
            else:
                seen[c] = 0
            unique_cols.append(c)
        df = df.iloc[1:].copy()
        df.columns = unique_cols
        df = df.reset_index(drop=True)
        df = df.dropna(how="all").reset_index(drop=True)

    return df, chosen, header_row


def ingest_bls(settings: Any) -> list[dict[str, Any]]:
    root = Path(settings.paths.raw_official) / "bls"
    out = Path(settings.paths.interim)
    out.mkdir(parents=True, exist_ok=True)
    sources: list[dict[str, Any]] = []

    discovered = list(root.glob("*.xlsx")) + list(root.glob("*.xls"))
    logger.info("BLS discovered files: %s", [f.name for f in discovered])

    def process_file(f: Path, parquet_stem: str, force_type: str | None = None) -> None:
        rel = f.relative_to(root)
        try:
            if f.suffix.lower() not in (".xlsx", ".xls"):
                return
            sheet_type = _classify_workbook_by_sheets(f)
            logger.info("BLS %s: sheet_names=%s -> classified_by_sheets=%s", f.name, pd.ExcelFile(f).sheet_names, sheet_type)

            df = None
            chosen_sheet = ""
            header_row = 0

            # occupation.xlsx: treat as projections only; parse Table 1.2
            if f.name.lower() == "occupation.xlsx":
                df, chosen_sheet, header_row = _parse_occupation_xlsx_table_1_2(f)
                logger.info("BLS occupation.xlsx: parsed Table 1.2 -> chosen_sheet=%s header_row=%s rows=%s", chosen_sheet, header_row, len(df) if df is not None else 0)
            else:
                df, chosen_sheet, header_row = _read_excel_sheets(f, expected_labels=MATRIX_LABELS + PROJECTIONS_LABELS)
                logger.info("BLS %s: chosen_sheet=%s header_row=%s columns=%s", f.name, chosen_sheet, header_row, list(df.columns) if df is not None else [])

            if df is None or df.empty:
                sources.append(
                    make_source_row(
                        source_name=f.name,
                        source_type="labor_market",
                        source_path_or_url=str(rel),
                        publisher="BLS",
                        notes="BLS; no data rows extracted",
                    )
                )
                return

            # Classify by content so we don't write projections data to matrix stems
            content_type = _classify_workbook_by_content(df)
            if force_type:
                content_type = force_type
            logger.info("BLS %s: normalized columns=%s -> classified_by_content=%s row_count=%s", f.name, list(df.columns), content_type, len(df))

            # Only write to matrix stem if content is actually matrix
            if parquet_stem in ("matrix_by_occupation", "matrix_by_industry", "national_employment_matrix") and content_type != "matrix":
                # Write to a generic stem so we don't overwrite a real matrix; note in register
                parquet_stem = f.stem.replace(" ", "_").replace(".", "_") + "_ingested"
                notes = f"BLS; classified as {content_type} (not matrix); do not use for industry_occupation_map"
            else:
                notes = "BLS labor/occupation/matrix data"

            parquet_path = out / f"bls__{parquet_stem}.parquet"
            df.to_parquet(parquet_path, index=False)
            logger.info("BLS wrote interim parquet: %s (%s rows)", parquet_path.name, len(df))

            sources.append(
                make_source_row(
                    source_name=f.name,
                    source_type="labor_market",
                    source_path_or_url=str(rel),
                    publisher="BLS",
                    notes=notes,
                )
            )
        except Exception as exc:
            logger.exception("BLS ingest failed for %s: %s", f.name, exc)
            sources.append(
                make_source_row(
                    source_name=f.name,
                    source_type="labor_market",
                    source_path_or_url=str(rel),
                    publisher="BLS",
                    notes=f"INGEST_FAILED: {exc!s}",
                )
            )

    # 1) Strictly named files (no alias for occupation.xlsx)
    for basename, stem in BLS_FILE_TO_STEM.items():
        f = root / basename
        if f.is_file():
            process_file(f, stem)

    # 2) occupation.xlsx -> projections Table 1.2 only (separate from matrix)
    occ_xlsx = root / "occupation.xlsx"
    if occ_xlsx.is_file():
        process_file(occ_xlsx, OCCUPATION_XLSX_PROJECTIONS_STEM, force_type="projections")

    # 3) Other Excel in bls/
    for f in root.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in (".xlsx", ".xls"):
            continue
        if f.name in BLS_FILE_TO_STEM or f.name == "occupation.xlsx":
            continue
        stem = f.stem.replace(" ", "_").replace(".", "_")
        process_file(f, stem)

    return sources
