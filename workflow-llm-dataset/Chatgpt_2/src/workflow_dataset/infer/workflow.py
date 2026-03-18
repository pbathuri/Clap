"""Infer ordered workflow steps from tasks and detailed work activities. Output: workflow_steps.parquet."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from workflow_dataset.utils.hashes import stable_id

logger = logging.getLogger(__name__)

WORKFLOW_STEP_COLUMNS = [
    "workflow_step_id",
    "occupation_id",
    "workflow_name",
    "step_order",
    "step_name",
    "step_description",
    "input_objects",
    "output_objects",
    "systems_used",
    "human_role_type",
    "automation_candidate",
    "automation_reason",
    "inference_method",
    "source_id",
    "confidence_score",
]

WORKFLOW_NAME = "Inferred Occupational Workflow"
INFERENCE_METHOD = "task_dwa_sequence"
DEFAULT_CONFIDENCE = 0.7
STEP_NAME_MAX_LEN = 80
MAX_STEPS_PER_OCCUPATION = 1000
AUTOMATION_REASON = "first-pass workflow inference only; automation not yet classified"


def _read_processed_table(processed: Path, table_stem: str) -> pd.DataFrame | None:
    p = processed / f"{table_stem}.parquet"
    if not p.exists():
        return None
    try:
        return pd.read_parquet(p)
    except Exception:
        return None


def _truncate_step_name(text: str, max_len: int = STEP_NAME_MAX_LEN) -> str:
    s = (text or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 3].rstrip() + "..."


def _tools_for_occupation(tools_df: pd.DataFrame | None, occupation_id: str, max_tools: int = 10) -> str:
    if tools_df is None or tools_df.empty or "occupation_id" not in tools_df.columns:
        return ""
    subset = tools_df[tools_df["occupation_id"].astype(str) == str(occupation_id)]
    if subset.empty:
        return ""
    names = subset["tool_name"].dropna().astype(str).str.strip().unique()[:max_tools]
    return "; ".join(n for n in names if n)


def run_workflow_inference(settings: Any) -> None:
    processed = Path(settings.paths.processed)
    processed.mkdir(parents=True, exist_ok=True)

    tasks_path = processed / "tasks.parquet"
    dwa_path = processed / "detailed_work_activities.parquet"
    tools_path = processed / "tools_and_technology.parquet"

    tasks_df = _read_processed_table(processed, "tasks") if tasks_path.exists() else None
    dwa_df = _read_processed_table(processed, "detailed_work_activities") if dwa_path.exists() else None
    tools_df = _read_processed_table(processed, "tools_and_technology") if tools_path.exists() else None

    has_tasks = tasks_df is not None and not tasks_df.empty and "occupation_id" in tasks_df.columns and "task_text" in tasks_df.columns
    has_dwa = dwa_df is not None and not dwa_df.empty and "occupation_id" in dwa_df.columns and "dwa_title" in dwa_df.columns

    if not has_tasks and not has_dwa:
        empty = pd.DataFrame(columns=WORKFLOW_STEP_COLUMNS)
        empty.to_parquet(processed / "workflow_steps.parquet", index=False)
        logger.info("workflow_inference: no task or DWA evidence; wrote empty workflow_steps.parquet")
        return

    occupation_ids: set[str] = set()
    if has_tasks:
        occupation_ids.update(tasks_df["occupation_id"].dropna().astype(str).str.strip().unique())
    if has_dwa:
        occupation_ids.update(dwa_df["occupation_id"].dropna().astype(str).str.strip().unique())

    rows: list[dict[str, Any]] = []
    skipped = 0

    for occ_id in sorted(occupation_ids):
        occ_steps: list[dict[str, Any]] = []

        if has_tasks:
            occ_tasks = tasks_df[tasks_df["occupation_id"].astype(str) == occ_id].copy()
            occ_tasks = occ_tasks.sort_values("task_id")
            for i, (_, r) in enumerate(occ_tasks.iterrows()):
                if len(occ_steps) >= MAX_STEPS_PER_OCCUPATION:
                    break
                task_text = (r.get("task_text") or "").strip()
                if not task_text:
                    continue
                step_id = stable_id("wf", occ_id, "task", r.get("task_id", i), str(i), prefix="wf")
                occ_steps.append({
                    "workflow_step_id": step_id,
                    "occupation_id": occ_id,
                    "workflow_name": WORKFLOW_NAME,
                    "step_order": len(occ_steps) + 1,
                    "step_name": _truncate_step_name(task_text),
                    "step_description": task_text,
                    "input_objects": "",
                    "output_objects": "",
                    "systems_used": "",
                    "human_role_type": "occupation-level",
                    "automation_candidate": "unknown",
                    "automation_reason": AUTOMATION_REASON,
                    "inference_method": INFERENCE_METHOD,
                    "source_id": str(r.get("source_id", "")),
                    "confidence_score": DEFAULT_CONFIDENCE,
                })

        if not occ_steps and has_dwa:
            occ_dwa = dwa_df[dwa_df["occupation_id"].astype(str) == occ_id].copy()
            occ_dwa = occ_dwa.sort_values("dwa_id")
            for i, (_, r) in enumerate(occ_dwa.iterrows()):
                if len(occ_steps) >= MAX_STEPS_PER_OCCUPATION:
                    break
                dwa_title = (r.get("dwa_title") or "").strip()
                if not dwa_title:
                    continue
                step_id = stable_id("wf", occ_id, "dwa", r.get("dwa_id", i), str(i), prefix="wf")
                occ_steps.append({
                    "workflow_step_id": step_id,
                    "occupation_id": occ_id,
                    "workflow_name": WORKFLOW_NAME,
                    "step_order": len(occ_steps) + 1,
                    "step_name": _truncate_step_name(dwa_title),
                    "step_description": dwa_title,
                    "input_objects": "",
                    "output_objects": "",
                    "systems_used": "",
                    "human_role_type": "occupation-level",
                    "automation_candidate": "unknown",
                    "automation_reason": AUTOMATION_REASON,
                    "inference_method": INFERENCE_METHOD,
                    "source_id": str(r.get("source_id", "")),
                    "confidence_score": DEFAULT_CONFIDENCE,
                })

        if not occ_steps:
            skipped += 1
            continue

        systems_used = _tools_for_occupation(tools_df, occ_id)
        if systems_used:
            for s in occ_steps:
                s["systems_used"] = systems_used

        rows.extend(occ_steps)

    if not rows:
        empty = pd.DataFrame(columns=WORKFLOW_STEP_COLUMNS)
        empty.to_parquet(processed / "workflow_steps.parquet", index=False)
        logger.info("workflow_inference: no steps generated; wrote empty workflow_steps.parquet (occupations with evidence: %s, skipped: %s)", len(occupation_ids), skipped)
        return

    out = pd.DataFrame(rows)
    for col in WORKFLOW_STEP_COLUMNS:
        if col not in out.columns:
            out[col] = "" if col != "confidence_score" else DEFAULT_CONFIDENCE
    out = out[WORKFLOW_STEP_COLUMNS]
    out.to_parquet(processed / "workflow_steps.parquet", index=False)

    n_occ = out["occupation_id"].nunique()
    logger.info(
        "workflow_inference: occupations processed=%s, total steps=%s, occupations skipped (no evidence)=%s",
        n_occ,
        len(out),
        skipped,
    )
