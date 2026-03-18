"""Build QA_Issues: missing source files/tables, ingest failures, missing provenance, duplicate IDs, empty text."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.utils.dates import utc_now_iso

QA_ISSUES_COLUMNS = [
    "qa_id",
    "issue_type",
    "entity_table",
    "entity_id",
    "description",
    "severity",
    "source_id",
    "retrieval_date",
]

EXPECTED_ONET_FILES = [
    "Occupation Data.txt",
    "Task Statements.txt",
    "Tools Used.txt",
    "Technology Skills.txt",
    "Skills.txt",
    "Knowledge.txt",
    "Abilities.txt",
    "Work Context.txt",
]

# Interim parquet stems required for second-pass (tasks, DWA, work context, tools, SKA)
EXPECTED_ONET_INTERIM_TABLES = [
    "onet__task_statements",
    "onet__work_context",
    "onet__tools_used",
    "onet__technology_skills",
    "onet__skills",
    "onet__knowledge",
    "onet__abilities",
    "onet__tasks_to_dwas",
    "onet__dwa_reference",
]

ENRICH_TABLES = [
    "tasks",
    "detailed_work_activities",
    "work_context",
    "tools_and_technology",
    "skills_knowledge_abilities",
]

ID_COLUMNS = {
    "tasks": "task_id",
    "detailed_work_activities": "dwa_id",
    "work_context": "context_id",
    "tools_and_technology": "tool_id",
    "skills_knowledge_abilities": "ska_id",
}

TEXT_COLUMNS = {
    "tasks": "task_text",
    "tools_and_technology": "tool_name",
    "work_context": "context_title",  # or context_value
}


def build_qa_issues(settings: Any) -> None:
    processed = Path(settings.paths.processed)
    interim = Path(settings.paths.interim)
    processed.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    qa_id = 0

    def add(issue_type: str, entity_table: str, entity_id: str, description: str, severity: str = "medium", source_id: str = ""):
        nonlocal qa_id
        qa_id += 1
        rows.append({
            "qa_id": f"qa_{qa_id}",
            "issue_type": issue_type,
            "entity_table": entity_table,
            "entity_id": entity_id,
            "description": description,
            "severity": severity,
            "source_id": source_id,
            "retrieval_date": utc_now_iso(),
        })

    # 1. Missing expected O*NET source files
    onet_dir = Path(settings.paths.raw_official) / "onet"
    found_names = {p.name for p in onet_dir.rglob("*.txt")}
    for expected in EXPECTED_ONET_FILES:
        if expected not in found_names:
            add(
                issue_type="missing_expected_source_file",
                entity_table="source_register",
                entity_id="",
                description=f"Expected O*NET file not found: {expected}",
                severity="high",
            )

    # 2. Missing expected O*NET interim tables (second pass)
    for stem in EXPECTED_ONET_INTERIM_TABLES:
        if not (interim / f"{stem}.parquet").exists():
            add(
                issue_type="missing_expected_source_table",
                entity_table="interim",
                entity_id=stem,
                description=f"Expected O*NET interim table not found: {stem}.parquet",
                severity="medium",
            )

    # 3. Source register rows with INGEST_FAILED (parse failure)
    sr_path = interim / "source_register.parquet"
    if sr_path.exists():
        sr = pd.read_parquet(sr_path)
        if "notes" in sr.columns:
            failed = sr[sr["notes"].astype(str).str.contains("INGEST_FAILED", na=False)]
            for _, r in failed.iterrows():
                add(
                    issue_type="ingest_failed",
                    entity_table="source_register",
                    entity_id=str(r.get("source_id", "")),
                    description=str(r.get("notes", "")),
                    severity="high",
                    source_id=str(r.get("source_id", "")),
                )

    # 4. Rows missing source_id in key processed tables
    tables_with_provenance = ["occupations", "industries", "industry_occupation_map", "labor_market"] + ENRICH_TABLES
    for table in tables_with_provenance:
        path = processed / f"{table}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        if "source_id" not in df.columns:
            add(
                issue_type="missing_source_id",
                entity_table=table,
                entity_id="",
                description=f"Table {table} has no source_id column",
                severity="high",
            )
            continue
        missing = df[df["source_id"].isna() | (df["source_id"].astype(str).str.strip() == "")]
        if len(missing) > 0:
            add(
                issue_type="missing_source_id",
                entity_table=table,
                entity_id="",
                description=f"Table {table}: {len(missing)} rows with missing or blank source_id",
                severity="high",
            )

    # 5. Rows missing occupation_id in enrich tables
    for table in ENRICH_TABLES:
        path = processed / f"{table}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        if "occupation_id" not in df.columns:
            add(
                issue_type="missing_occupation_id",
                entity_table=table,
                entity_id="",
                description=f"Table {table} has no occupation_id column",
                severity="high",
            )
            continue
        missing = df[df["occupation_id"].isna() | (df["occupation_id"].astype(str).str.strip() == "")]
        if len(missing) > 0:
            add(
                issue_type="missing_occupation_id",
                entity_table=table,
                entity_id="",
                description=f"Table {table}: {len(missing)} rows with missing or blank occupation_id",
                severity="high",
            )

    # 6. Duplicate IDs in each processed table
    for table, id_col in (list(ID_COLUMNS.items()) + [("occupations", "occupation_id"), ("industries", "industry_id")]):
        path = processed / f"{table}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        if id_col not in df.columns:
            continue
        dupes = df[df.duplicated(subset=[id_col], keep=False)]
        if len(dupes) > 0:
            n_dup = dupes[id_col].nunique()
            add(
                issue_type="duplicate_id",
                entity_table=table,
                entity_id="",
                description=f"Table {table}: {n_dup} duplicate values in {id_col} ({len(dupes)} rows)",
                severity="high",
            )

    # 7. Empty raw task/tool/context text
    for table, text_col in TEXT_COLUMNS.items():
        path = processed / f"{table}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        if text_col not in df.columns:
            continue
        empty = df[df[text_col].isna() | (df[text_col].astype(str).str.strip() == "")]
        if len(empty) > 0:
            add(
                issue_type="empty_raw_text",
                entity_table=table,
                entity_id="",
                description=f"Table {table}: {len(empty)} rows with empty or blank {text_col}",
                severity="medium",
            )

    # 8. Industry_occupation_map: missing source_id, duplicate map_id
    iom_path = processed / "industry_occupation_map.parquet"
    if iom_path.exists():
        iom = pd.read_parquet(iom_path)
        if not iom.empty:
            if "source_id" not in iom.columns:
                add("missing_source_id", "industry_occupation_map", "", "Table industry_occupation_map has no source_id column", "high")
            else:
                missing_src = iom[iom["source_id"].isna() | (iom["source_id"].astype(str).str.strip() == "")]
                if len(missing_src) > 0:
                    add("missing_source_id", "industry_occupation_map", "", f"industry_occupation_map: {len(missing_src)} rows with missing or blank source_id", "high")
            if "map_id" in iom.columns:
                dupes = iom[iom.duplicated(subset=["map_id"], keep=False)]
                if len(dupes) > 0:
                    add("duplicate_map_id", "industry_occupation_map", "", f"industry_occupation_map: {dupes['map_id'].nunique()} duplicate map_id ({len(dupes)} rows)", "high")

    # 9. Labor_market: rows without occupation_id
    lm_path = processed / "labor_market.parquet"
    if lm_path.exists():
        lm = pd.read_parquet(lm_path)
        if not lm.empty and "occupation_id" in lm.columns:
            missing_occ = lm[lm["occupation_id"].isna() | (lm["occupation_id"].astype(str).str.strip() == "")]
            if len(missing_occ) > 0:
                add("missing_occupation_id", "labor_market", "", f"labor_market: {len(missing_occ)} rows with missing or blank occupation_id", "high")

    # 10. Occupations with no industry mapping
    occ_path = processed / "occupations.parquet"
    if occ_path.exists() and iom_path.exists():
        occ = pd.read_parquet(occ_path)
        iom = pd.read_parquet(iom_path)
        if not occ.empty and not iom.empty and "occupation_id" in occ.columns and "occupation_id" in iom.columns:
            mapped_occ = set(iom["occupation_id"].dropna().astype(str).str.strip().unique())
            all_occ = set(occ["occupation_id"].dropna().astype(str).str.strip().unique())
            unmapped = all_occ - mapped_occ
            if unmapped:
                add("occupation_with_no_industry_mapping", "occupations", "", f"{len(unmapped)} occupations have no row in industry_occupation_map", "medium")

    # 11. Industries with no mapped occupations (industry_ids in map not in industries table, or industries with zero map rows)
    ind_path = processed / "industries.parquet"
    if iom_path.exists():
        iom = pd.read_parquet(iom_path)
        if not iom.empty and "industry_id" in iom.columns:
            mapped_ind = set(iom["industry_id"].dropna().astype(str).str.strip().unique())
            if ind_path.exists():
                ind = pd.read_parquet(ind_path)
                if not ind.empty and "industry_id" in ind.columns:
                    known_ind = set(ind["industry_id"].dropna().astype(str).str.strip().unique())
                    unmapped_ind = mapped_ind - known_ind
                    if unmapped_ind:
                        add("industry_with_no_mapped_occupations", "industries", "", f"{len(unmapped_ind)} industry_id(s) in map not in industries table (e.g. from BLS NAICS-only)", "low")
                else:
                    add("industry_with_no_mapped_occupations", "industries", "", "industries table empty; all map industry_id are unmapped", "low")
            else:
                if mapped_ind:
                    add("industry_with_no_mapped_occupations", "industries", "", f"industries.parquet missing; {len(mapped_ind)} industry_id(s) in map have no industries table", "medium")

    # 12. BLS unmapped occupation codes (from industry_occupation map and labor_market steps)
    for name, entity_table in [
        ("bls_unmapped_occupation_codes.parquet", "industry_occupation_map"),
        ("labor_unmapped_occupation_codes.parquet", "labor_market"),
    ]:
        path = processed / name
        if path.exists():
            df = pd.read_parquet(path)
            if not df.empty and "code" in df.columns:
                n = len(df)
                add(
                    issue_type="unmapped_occupation_codes",
                    entity_table=entity_table,
                    entity_id="",
                    description=f"BLS: {n} occupation code(s) could not be mapped to occupation_id (see {name})",
                    severity="medium",
                )

    # 13. BLS unmapped industry codes
    bls_ind_path = processed / "bls_unmapped_industry_codes.parquet"
    if bls_ind_path.exists():
        df = pd.read_parquet(bls_ind_path)
        if not df.empty and "code" in df.columns:
            n = len(df)
            add(
                issue_type="unmapped_industry_codes",
                entity_table="industry_occupation_map",
                entity_id="",
                description=f"BLS: {n} industry/NAICS code(s) not in industries table (see bls_unmapped_industry_codes.parquet)",
                severity="medium",
            )

    # 14. Empty BLS output tables (high severity)
    for table, path_key in [
        ("industry_occupation_map", "industry_occupation_map.parquet"),
        ("labor_market", "labor_market.parquet"),
    ]:
        path = processed / path_key
        if path.exists():
            df = pd.read_parquet(path)
            if df.empty:
                add(
                    issue_type="empty_output_table",
                    entity_table=table,
                    entity_id="",
                    description=f"Processed table {table} is empty; BLS pipeline may have no inputs or all rows unmapped",
                    severity="high",
                )

    # 15. No real BLS matrix source (reported by mapper when no matrix workbook had NAICS+SOC+employment columns)
    no_matrix_path = processed / "bls_no_matrix_source.parquet"
    if no_matrix_path.exists():
        add(
            issue_type="no_bls_matrix_source",
            entity_table="industry_occupation_map",
            entity_id="",
            description="No real BLS industry-occupation matrix workbook found (occupation.xlsx is projections, not matrix). Map left empty; add bls_matrix_by_occupation.xlsx or national_employment_matrix.xlsx for mapping.",
            severity="high",
        )

    if rows:
        out_df = pd.DataFrame(rows)
        for col in QA_ISSUES_COLUMNS:
            if col not in out_df.columns:
                out_df[col] = ""
        out_df = out_df[QA_ISSUES_COLUMNS]
        out_df.to_parquet(processed / "qa_issues.parquet", index=False)
