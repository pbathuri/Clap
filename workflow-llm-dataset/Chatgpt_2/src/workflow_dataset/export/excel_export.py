"""Write Excel workbook from processed tables; real sheets with data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.utils.dates import utc_now_iso

SHEET_ORDER = [
    "README",
    "Taxonomy_ISIC",
    "Taxonomy_NAICS",
    "Taxonomy_SOC",
    "Taxonomy_ONET",
    "Industry_Occupation_Map",
    "Occupations_Master",
    "Occupation_Aliases",
    "Tasks",
    "Detailed_Work_Activities",
    "Work_Context",
    "Tools_Technology",
    "Skills_Knowledge_Abilities",
    "Workflow_Steps",
    "Pain_Points",
    "KPI_Library",
    "Labor_Market",
    "Source_Register",
    "Provenance_Row_Map",
    "QA_Issues",
    "Ambiguities_Review",
]

# Map sheet name -> processed parquet filename (stem)
SHEET_TO_TABLE: dict[str, str] = {
    "Taxonomy_ISIC": "industries",  # filter taxonomy_system == ISIC
    "Taxonomy_NAICS": "industries",  # filter taxonomy_system == NAICS
    "Taxonomy_SOC": "taxonomy_soc",
    "Taxonomy_ONET": "occupations",  # filter taxonomy_system == O*NET
    "Industry_Occupation_Map": "industry_occupation_map",
    "Occupations_Master": "occupations",
    "Occupation_Aliases": "occupation_aliases",
    "Tasks": "tasks",
    "Detailed_Work_Activities": "detailed_work_activities",
    "Work_Context": "work_context",
    "Tools_Technology": "tools_and_technology",
    "Skills_Knowledge_Abilities": "skills_knowledge_abilities",
    "Workflow_Steps": "workflow_steps",
    "Pain_Points": "pain_points",
    "KPI_Library": "kpis",
    "Labor_Market": "labor_market",
    "Source_Register": "source_register",
    "Provenance_Row_Map": "provenance_row_map",
    "QA_Issues": "qa_issues",
    "Ambiguities_Review": "ambiguities_review",
}


# Cap rows per sheet so the workbook stays openable; full data is in parquet/csv
EXCEL_MAX_ROWS_PER_SHEET = 100_000


def _read_processed_table(processed: Path, table_stem: str, max_rows: int | None = EXCEL_MAX_ROWS_PER_SHEET) -> pd.DataFrame | None:
    p = processed / f"{table_stem}.parquet"
    if not p.exists():
        return None
    try:
        df = pd.read_parquet(p)
        if max_rows is not None and len(df) > max_rows:
            df = df.head(max_rows)
        return df
    except Exception:
        return None


def export_excel(settings) -> None:
    output_path = Path(settings.project.output_excel)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed = Path(settings.paths.processed)

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        for sheet in SHEET_ORDER:
            df: pd.DataFrame | None = None
            table = SHEET_TO_TABLE.get(sheet)

            if sheet == "README":
                df = pd.DataFrame({
                    "Item": [
                        "Purpose",
                        "Build timestamp",
                        "Source versions",
                        "Methodology",
                        "Limitations",
                        "Sheet descriptions",
                        "Refresh instructions",
                    ],
                    "Content": [
                        "Primary-source-first occupational workflow dataset (global work priors for personal agent) and LLM development.",
                        utc_now_iso(),
                        "O*NET 30.2; ISIC Rev.4; NAICS 2022; SOC 2018 when present.",
                        "Ingest -> normalize (taxonomies + occupations) -> export. Every row retains source_id.",
                        "Workflow steps inferred from tasks/DWA (global priors). Large sheets capped at 100k rows; full data in parquet/csv.",
                        "Taxonomy sheets = industry/SOC hierarchy. Occupations_Master = canonical occupations. Source_Register = ingested files.",
                        "Re-run: python -m workflow_dataset.cli build --config configs/settings.yaml",
                    ],
                })
            elif table == "industries" and sheet in ("Taxonomy_ISIC", "Taxonomy_NAICS"):
                full = _read_processed_table(processed, "industries")
                if full is not None and not full.empty and "taxonomy_system" in full.columns:
                    sys_val = "ISIC" if sheet == "Taxonomy_ISIC" else "NAICS"
                    df = full[full["taxonomy_system"].astype(str) == sys_val].copy()
                else:
                    df = pd.DataFrame()
            elif table == "occupations" and sheet == "Taxonomy_ONET":
                full = _read_processed_table(processed, "occupations")
                if full is not None and not full.empty and "taxonomy_system" in full.columns:
                    df = full[full["taxonomy_system"].astype(str) == "O*NET"].copy()
                else:
                    df = pd.DataFrame()
            elif table:
                df = _read_processed_table(processed, table)

            if df is None or df.empty:
                df = pd.DataFrame()
            df.to_excel(writer, sheet_name=sheet[:31], index=False)
            ws = writer.sheets[sheet[:31]]
            ws.freeze_panes(1, 0)
