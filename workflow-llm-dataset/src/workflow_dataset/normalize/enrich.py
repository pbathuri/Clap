"""Second pass: build tasks, DWA, work_context, tools, SKA from O*NET interim. Every row has stable id, occupation_id, source_id, confidence_score, review_status."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.utils.dates import utc_now_iso

TASK_COLUMNS = [
    "task_id", "occupation_id", "task_text", "task_type", "frequency_signal", "importance_signal",
    "source_id", "source_verbatim_excerpt", "extracted_from_dataset", "is_primary_source",
    "confidence_score", "review_status",
]
DWA_COLUMNS = [
    "dwa_id", "occupation_id", "dwa_code", "dwa_title", "category",
    "source_id", "confidence_score", "review_status",
]
WORK_CONTEXT_COLUMNS = [
    "context_id", "occupation_id", "context_code", "context_title", "context_value", "scale_description",
    "source_id", "confidence_score", "review_status",
]
TOOLS_COLUMNS = [
    "tool_id", "occupation_id", "tool_name", "tool_type", "hot_technology_flag", "commodity_code", "commodity_title",
    "source_id", "confidence_score", "review_status",
]
SKA_COLUMNS = [
    "ska_id", "occupation_id", "dimension_type", "dimension_name", "importance", "level",
    "source_id", "confidence_score", "review_status",
]
PROVENANCE_ROW_MAP_COLUMNS = [
    "row_map_id", "entity_table", "entity_row_id", "source_id", "source_locator", "retrieval_date", "extractor_notes",
]

PRIMARY_CONFIDENCE = "1.0"
REVIEW_ACCEPTED = "accepted"


def _get_source_id(sr: pd.DataFrame, name: str) -> str:
    m = sr[sr["source_name"].astype(str) == name]
    return "" if m.empty else str(m.iloc[0]["source_id"])


def _occupation_code_to_id(occ_path: Path) -> pd.Series:
    if not occ_path.exists():
        return pd.Series(dtype=str)
    df = pd.read_parquet(occ_path)
    if "occupation_code" not in df.columns or "occupation_id" not in df.columns:
        return pd.Series(dtype=str)
    return df.set_index(df["occupation_code"].astype(str).str.strip())["occupation_id"]


def _run_tasks(interim: Path, processed: Path, code_to_occ: pd.Series, sr: pd.DataFrame, prov_rows: list) -> None:
    path = interim / "onet__task_statements.parquet"
    if not path.exists():
        return
    df = pd.read_parquet(path)
    src_id = _get_source_id(sr, "Task Statements.txt")
    if not src_id:
        return
    df = df.rename(columns={"O*NET-SOC Code": "code", "Task ID": "task_id_raw", "Task": "task_text", "Task Type": "task_type"})
    df["code"] = df["code"].astype(str).str.strip()
    df["occupation_id"] = df["code"].map(code_to_occ)
    df = df[df["occupation_id"].notna() & df["task_text"].notna() & (df["task_text"].astype(str).str.strip() != "")]
    if df.empty:
        return
    df["task_id_raw"] = df["task_id_raw"].astype(str).str.strip()
    df["task_id"] = df.apply(lambda r: stable_id("task", r["code"], r["task_id_raw"], prefix="task"), axis=1)
    df["task_text"] = df["task_text"].astype(str).str.strip()
    df["task_type"] = df["task_type"].fillna("").astype(str).str.strip().str.lower().replace("", "core")
    out = pd.DataFrame({
        "task_id": df["task_id"],
        "occupation_id": df["occupation_id"],
        "task_text": df["task_text"],
        "task_type": df["task_type"],
        "frequency_signal": "",
        "importance_signal": "",
        "source_id": src_id,
        "source_verbatim_excerpt": df["task_text"],
        "extracted_from_dataset": "O*NET Task Statements",
        "is_primary_source": "1",
        "confidence_score": PRIMARY_CONFIDENCE,
        "review_status": REVIEW_ACCEPTED,
    })[TASK_COLUMNS]
    out.to_parquet(processed / "tasks.parquet", index=False)
    retrieval = utc_now_iso()
    prov_rows.extend([
        {
            "row_map_id": stable_id("prov", "tasks", tid, prefix="prov"),
            "entity_table": "tasks",
            "entity_row_id": tid,
            "source_id": src_id,
            "source_locator": f"Task Statements.txt Task ID {raw}",
            "retrieval_date": retrieval,
            "extractor_notes": "",
        }
        for tid, raw in zip(df["task_id"], df["task_id_raw"])
    ])


def _run_detailed_work_activities(interim: Path, processed: Path, code_to_occ: pd.Series, sr: pd.DataFrame, prov_rows: list) -> None:
    t2d = interim / "onet__tasks_to_dwas.parquet"
    ref = interim / "onet__dwa_reference.parquet"
    if not t2d.exists() or not ref.exists():
        return
    td = pd.read_parquet(t2d)
    dr = pd.read_parquet(ref)
    src_id = _get_source_id(sr, "Tasks to DWAs.txt") or _get_source_id(sr, "DWA Reference.txt")
    if not src_id:
        return
    dwa_title = dr.set_index("DWA ID")["DWA Title"].astype(str)
    iwa_map = dr.set_index("DWA ID")["IWA ID"].astype(str)
    td["code"] = td["O*NET-SOC Code"].astype(str).str.strip()
    td["occupation_id"] = td["code"].map(code_to_occ)
    td = td[td["occupation_id"].notna()]
    td["DWA ID"] = td["DWA ID"].astype(str).str.strip()
    td = td.drop_duplicates(subset=["occupation_id", "DWA ID"])
    td["dwa_title"] = td["DWA ID"].map(dwa_title)
    td["category"] = td["DWA ID"].map(iwa_map).fillna("")
    td["dwa_id"] = td.apply(lambda r: stable_id("dwa", r["occupation_id"], r["DWA ID"], prefix="dwa"), axis=1)
    out = pd.DataFrame({
        "dwa_id": td["dwa_id"],
        "occupation_id": td["occupation_id"],
        "dwa_code": td["DWA ID"],
        "dwa_title": td["dwa_title"],
        "category": td["category"],
        "source_id": src_id,
        "confidence_score": PRIMARY_CONFIDENCE,
        "review_status": REVIEW_ACCEPTED,
    })[DWA_COLUMNS]
    out.to_parquet(processed / "detailed_work_activities.parquet", index=False)
    retrieval = utc_now_iso()
    for did, dwa_code in zip(td["dwa_id"], td["DWA ID"]):
        prov_rows.append({
            "row_map_id": stable_id("prov", "dwa", did, prefix="prov"),
            "entity_table": "detailed_work_activities",
            "entity_row_id": did,
            "source_id": src_id,
            "source_locator": f"Tasks to DWAs.txt + DWA Reference.txt DWA ID {dwa_code}",
            "retrieval_date": retrieval,
            "extractor_notes": "",
        })


def _run_work_context(interim: Path, processed: Path, code_to_occ: pd.Series, sr: pd.DataFrame, prov_rows: list) -> None:
    path = interim / "onet__work_context.parquet"
    if not path.exists():
        return
    df = pd.read_parquet(path)
    src_id = _get_source_id(sr, "Work Context.txt")
    if not src_id:
        return
    df["code"] = df["O*NET-SOC Code"].astype(str).str.strip()
    df["occupation_id"] = df["code"].map(code_to_occ)
    df = df[df["occupation_id"].notna()]
    df["context_code"] = df["Element ID"].astype(str).str.strip()
    df["context_title"] = df["Element Name"].fillna("").astype(str).str.strip()
    df["context_value"] = df["Data Value"].fillna("").astype(str).str.strip()
    df["scale_description"] = (df["Scale ID"].fillna("").astype(str) + " " + df["Category"].fillna("").astype(str)).str.strip()
    df = df.reset_index(drop=True)
    df["context_id"] = df.apply(lambda r: stable_id("ctx", str(r.name), r["code"], r["context_code"], prefix="ctx"), axis=1)
    out = pd.DataFrame({
        "context_id": df["context_id"],
        "occupation_id": df["occupation_id"],
        "context_code": df["context_code"],
        "context_title": df["context_title"],
        "context_value": df["context_value"],
        "scale_description": df["scale_description"],
        "source_id": src_id,
        "confidence_score": PRIMARY_CONFIDENCE,
        "review_status": REVIEW_ACCEPTED,
    })[WORK_CONTEXT_COLUMNS]
    out.to_parquet(processed / "work_context.parquet", index=False)
    retrieval = utc_now_iso()
    for cid, ccode in zip(df["context_id"], df["context_code"]):
        prov_rows.append({
            "row_map_id": stable_id("prov", "work_context", cid, prefix="prov"),
            "entity_table": "work_context",
            "entity_row_id": cid,
            "source_id": src_id,
            "source_locator": f"Work Context.txt Element ID {ccode}",
            "retrieval_date": retrieval,
            "extractor_notes": "",
        })


def _run_tools_and_technology(interim: Path, processed: Path, code_to_occ: pd.Series, sr: pd.DataFrame, prov_rows: list) -> None:
    rows = []
    retrieval = utc_now_iso()
    for path, src_id, hot_default in [
        (interim / "onet__tools_used.parquet", _get_source_id(sr, "Tools Used.txt"), ""),
        (interim / "onet__technology_skills.parquet", _get_source_id(sr, "Technology Skills.txt"), "N"),
    ]:
        if not path.exists() or not src_id:
            continue
        df = pd.read_parquet(path)
        df["code"] = df["O*NET-SOC Code"].astype(str).str.strip()
        df["occupation_id"] = df["code"].map(code_to_occ)
        df = df[df["occupation_id"].notna()]
        df["tool_name"] = df["Example"].fillna("").astype(str).str.strip()
        df = df[df["tool_name"] != ""]
        df["commodity_code"] = df["Commodity Code"].fillna("").astype(str).str.strip()
        df["commodity_title"] = df["Commodity Title"].fillna("").astype(str).str.strip()
        df["hot_technology_flag"] = df["Hot Technology"].fillna(hot_default).astype(str).str.strip() if "Hot Technology" in df.columns else hot_default
        df["tool_type"] = df["commodity_title"].str.lower().apply(lambda x: "software" if "software" in x else "equipment")
        df["tool_id"] = df.apply(lambda r: stable_id("tool", r["occupation_id"], r["tool_name"], r["commodity_code"], src_id, prefix="tool"), axis=1)
        for _, r in df.iterrows():
            rows.append({
                "tool_id": r["tool_id"], "occupation_id": r["occupation_id"], "tool_name": r["tool_name"],
                "tool_type": r["tool_type"], "hot_technology_flag": r["hot_technology_flag"],
                "commodity_code": r["commodity_code"], "commodity_title": r["commodity_title"],
                "source_id": src_id, "confidence_score": PRIMARY_CONFIDENCE, "review_status": REVIEW_ACCEPTED,
            })
        for tid, tname in zip(df["tool_id"], df["tool_name"]):
            prov_rows.append({
                "row_map_id": stable_id("prov", "tools", tid, prefix="prov"),
                "entity_table": "tools_and_technology", "entity_row_id": tid,
                "source_id": src_id, "source_locator": f"{path.name} Example {str(tname)[:50]}",
                "retrieval_date": retrieval, "extractor_notes": "",
            })
    if rows:
        pd.DataFrame(rows)[TOOLS_COLUMNS].to_parquet(processed / "tools_and_technology.parquet", index=False)


def _run_skills_knowledge_abilities(interim: Path, processed: Path, code_to_occ: pd.Series, sr: pd.DataFrame, prov_rows: list) -> None:
    files = [
        ("onet__skills.parquet", "Skills.txt", "skill"),
        ("onet__knowledge.parquet", "Knowledge.txt", "knowledge"),
        ("onet__abilities.parquet", "Abilities.txt", "ability"),
        ("onet__work_styles.parquet", "Work Styles.txt", "work_style"),
    ]
    rows = []
    retrieval = utc_now_iso()
    for stem, source_name, dim_type in files:
        path = interim / stem
        if not path.exists():
            continue
        src_id = _get_source_id(sr, source_name)
        if not src_id:
            continue
        df = pd.read_parquet(path)
        df["code"] = df["O*NET-SOC Code"].astype(str).str.strip()
        df["occupation_id"] = df["code"].map(code_to_occ)
        df = df[df["occupation_id"].notna()]
        df["elem_id"] = df["Element ID"].fillna("").astype(str).str.strip()
        df["dimension_name"] = df["Element Name"].fillna("").astype(str).str.strip()
        df = df[df["dimension_name"] != ""]
        df["data_val"] = df["Data Value"].fillna("").astype(str).str.strip()
        df = df.reset_index(drop=True)
        df["ska_id"] = df.apply(lambda r: stable_id("ska", str(r.name), r["occupation_id"], dim_type, r["elem_id"], prefix="ska"), axis=1)
        for _, r in df.iterrows():
            rows.append({
                "ska_id": r["ska_id"], "occupation_id": r["occupation_id"], "dimension_type": dim_type,
                "dimension_name": r["dimension_name"], "importance": r["data_val"], "level": r["data_val"],
                "source_id": src_id, "confidence_score": PRIMARY_CONFIDENCE, "review_status": REVIEW_ACCEPTED,
            })
        for sid, eid in zip(df["ska_id"], df["elem_id"]):
            prov_rows.append({
                "row_map_id": stable_id("prov", "ska", sid, prefix="prov"),
                "entity_table": "skills_knowledge_abilities", "entity_row_id": sid,
                "source_id": src_id, "source_locator": f"{source_name} Element ID {eid}",
                "retrieval_date": retrieval, "extractor_notes": "",
            })
    if rows:
        pd.DataFrame(rows)[SKA_COLUMNS].to_parquet(processed / "skills_knowledge_abilities.parquet", index=False)


def run_enrichment_normalization(settings: Any) -> None:
    interim = Path(settings.paths.interim)
    processed = Path(settings.paths.processed)
    processed.mkdir(parents=True, exist_ok=True)
    sr_path = interim / "source_register.parquet"
    if not sr_path.exists():
        return
    sr = pd.read_parquet(sr_path)
    occ_path = processed / "occupations.parquet"
    code_to_occ = _occupation_code_to_id(occ_path)
    if code_to_occ.empty:
        return
    prov_rows: list[dict[str, Any]] = []
    _run_tasks(interim, processed, code_to_occ, sr, prov_rows)
    _run_detailed_work_activities(interim, processed, code_to_occ, sr, prov_rows)
    _run_work_context(interim, processed, code_to_occ, sr, prov_rows)
    _run_tools_and_technology(interim, processed, code_to_occ, sr, prov_rows)
    _run_skills_knowledge_abilities(interim, processed, code_to_occ, sr, prov_rows)
    if prov_rows:
        prov_df = pd.DataFrame(prov_rows)
        for col in PROVENANCE_ROW_MAP_COLUMNS:
            if col not in prov_df.columns:
                prov_df[col] = ""
        prov_df[PROVENANCE_ROW_MAP_COLUMNS].to_parquet(processed / "provenance_row_map.parquet", index=False)
