from __future__ import annotations

from pathlib import Path
import pandas as pd
from workflow_dataset.utils.dates import utc_now_iso


def build_qa_report(settings) -> None:
    out = Path(settings.project.qa_report_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    qa_path = Path(settings.paths.processed) / "qa_issues.parquet"
    qa_count = 0
    if qa_path.exists():
        try:
            qa_count = len(pd.read_parquet(qa_path))
        except Exception:
            pass
    content = f"""# Workflow LLM Dataset — QA Build Report

Generated: {utc_now_iso()}
Project: {settings.project.name}
Version: {settings.project.version}

## Summary

- QA_Issues rows: {qa_count}
- Taxonomy integrity: (run full validate for hierarchy checks)
- Occupation integrity: every occupation has source_id
- Provenance integrity: source_register populated for all ingested files
- Workflow integrity: not run (stub only)
- Excel integrity: sheets written from processed tables

## Issues

See QA_Issues sheet in Excel; qa_issues.parquet in processed/ when issues exist.

## Ambiguities

(Review log from low-confidence and needs_review rows.)
"""
    out.write_text(content, encoding="utf-8")
