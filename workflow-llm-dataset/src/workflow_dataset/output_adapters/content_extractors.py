"""
M14: Deterministic content extraction from reviewed/refined artifacts.

Extracts headings, section text, tables, checklists, and structured rows
from markdown, text, CSV, and JSON. No LLM dependency; fallback to empty when weak.
"""

from __future__ import annotations

import csv
import json
import re
from io import StringIO
from pathlib import Path
from typing import Any

from workflow_dataset.output_adapters.population_models import SourceContentSlice
from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.utils.dates import utc_now_iso


def _infer_source_type(content: str, path: str | Path = "") -> str:
    p = Path(path) if path else None
    if p and p.suffix:
        ext = p.suffix.lower()
        if ext == ".csv":
            return "csv"
        if ext == ".json":
            return "json"
        if ext in (".md", ".markdown"):
            return "markdown"
        if ext == ".html":
            return "html"
    if content.strip().startswith("{"):
        return "json"
    if "\t" in content[:500] or ("," in content[:200] and "\n" in content):
        try:
            list(csv.reader(StringIO(content.split("\n")[0])))
            return "csv"
        except Exception:
            pass
    return "markdown"  # default for narrative text


def extract_from_markdown(
    content: str,
    source_artifact_ref: str = "",
    max_sections: int = 50,
    max_rows_per_table: int = 500,
) -> list[SourceContentSlice]:
    """Extract headings, sections, tables, and checklist items from markdown."""
    slices: list[SourceContentSlice] = []
    ts = utc_now_iso()
    lines = content.split("\n")
    current_heading = ""
    current_text: list[str] = []
    table_rows: list[list[str]] = []
    in_table = False

    def flush_narrative() -> None:
        nonlocal current_text
        if current_text and current_heading:
            text = "\n".join(current_text).strip()
            if text and len(slices) < max_sections:
                slices.append(
                    SourceContentSlice(
                        slice_id=stable_id("slice", source_artifact_ref, current_heading[:50], ts, prefix="slice"),
                        source_artifact_ref=source_artifact_ref,
                        source_type="markdown",
                        heading=current_heading,
                        section_type="narrative",
                        text=text[:10000],
                        confidence_score=0.9,
                        provenance_refs=[source_artifact_ref] if source_artifact_ref else [],
                    )
                )
        current_text = []

    def flush_table() -> None:
        nonlocal table_rows
        if table_rows and len(slices) < max_sections:
            headers = table_rows[0]
            rows = table_rows[1:max_rows_per_table + 1]
            slices.append(
                SourceContentSlice(
                    slice_id=stable_id("slice", source_artifact_ref, "table", str(len(slices)), ts, prefix="slice"),
                    source_artifact_ref=source_artifact_ref,
                    source_type="markdown",
                    heading=current_heading or "Table",
                    section_type="table",
                    structured_rows=[headers] + rows,
                    confidence_score=0.85,
                    provenance_refs=[source_artifact_ref] if source_artifact_ref else [],
                )
            )
        table_rows = []

    for line in lines:
        stripped = line.strip()
        if re.match(r"^#+\s", line):
            flush_table()
            in_table = False
            flush_narrative()
            current_heading = re.sub(r"^#+\s*", "", stripped).strip()
            current_text = []
            continue
        if stripped.startswith("|") and "|" in stripped[1:]:
            in_table = True
            cells = [c.strip() for c in re.split(r"\s*\|\s*", stripped) if c.strip() or "|" in stripped]
            if cells:
                table_rows.append(cells)
            continue
        if in_table and not stripped:
            flush_table()
            in_table = False
            continue
        if in_table:
            flush_table()
            in_table = False
        if stripped.startswith("- [ ]") or stripped.startswith("- [x]") or stripped.startswith("* [ ]") or stripped.startswith("* [x]"):
            if current_heading and len(slices) < max_sections:
                slices.append(
                    SourceContentSlice(
                        slice_id=stable_id("slice", source_artifact_ref, "checklist", str(len(slices)), ts, prefix="slice"),
                        source_artifact_ref=source_artifact_ref,
                        source_type="markdown",
                        heading=current_heading or "Checklist",
                        section_type="checklist",
                        text=stripped[:2000],
                        confidence_score=0.9,
                        provenance_refs=[source_artifact_ref] if source_artifact_ref else [],
                    )
                )
            continue
        if current_heading:
            current_text.append(line)
    flush_table()
    flush_narrative()
    return slices


def extract_from_csv(
    content: str,
    source_artifact_ref: str = "",
    max_rows: int = 1000,
) -> list[SourceContentSlice]:
    """Parse CSV into a single table slice."""
    slices: list[SourceContentSlice] = []
    try:
        reader = csv.reader(StringIO(content))
        rows = list(reader)
    except Exception:
        return slices
    if not rows:
        return slices
    headers = rows[0]
    data_rows = rows[1:max_rows + 1]
    ts = utc_now_iso()
    slices.append(
        SourceContentSlice(
            slice_id=stable_id("slice", source_artifact_ref, "csv", ts, prefix="slice"),
            source_artifact_ref=source_artifact_ref,
            source_type="csv",
            heading="Data",
            section_type="table",
            structured_rows=[headers] + data_rows,
            confidence_score=1.0,
            provenance_refs=[source_artifact_ref] if source_artifact_ref else [],
        )
    )
    return slices


def extract_from_json(
    content: str,
    source_artifact_ref: str = "",
    max_rows: int = 500,
) -> list[SourceContentSlice]:
    """Extract array-of-objects or key-value structure from JSON."""
    slices: list[SourceContentSlice] = []
    try:
        data = json.loads(content)
    except Exception:
        return slices
    ts = utc_now_iso()
    if isinstance(data, list) and data and isinstance(data[0], dict):
        keys = list(data[0].keys())
        rows = [keys] + [[str(o.get(k, "")) for k in keys] for o in data[:max_rows]]
        slices.append(
            SourceContentSlice(
                slice_id=stable_id("slice", source_artifact_ref, "json_table", ts, prefix="slice"),
                source_artifact_ref=source_artifact_ref,
                source_type="json",
                heading="Data",
                section_type="table",
                structured_rows=rows,
                confidence_score=0.95,
                provenance_refs=[source_artifact_ref] if source_artifact_ref else [],
            )
        )
    elif isinstance(data, dict):
        summary_parts = []
        for k, v in list(data.items())[:30]:
            if isinstance(v, (str, int, float, bool)):
                summary_parts.append(f"- **{k}**: {v}")
            elif isinstance(v, list) and len(v) < 20:
                summary_parts.append(f"- **{k}**: {v}")
        if summary_parts:
            slices.append(
                SourceContentSlice(
                    slice_id=stable_id("slice", source_artifact_ref, "json_summary", ts, prefix="slice"),
                    source_artifact_ref=source_artifact_ref,
                    source_type="json",
                    heading="Summary",
                    section_type="narrative",
                    text="\n".join(summary_parts)[:5000],
                    confidence_score=0.9,
                    provenance_refs=[source_artifact_ref] if source_artifact_ref else [],
                )
            )
    return slices


def extract_content(
    content: str,
    source_artifact_ref: str = "",
    source_path: str | Path = "",
    max_sections: int = 50,
    max_rows: int = 1000,
) -> list[SourceContentSlice]:
    """
    Extract structured content from artifact text. Deterministic.
    Chooses parser by inferred type (csv, json, markdown). Returns empty list on failure.
    """
    if not content or not content.strip():
        return []
    source_type = _infer_source_type(content, source_path)
    if source_type == "csv":
        return extract_from_csv(content, source_artifact_ref, max_rows=max_rows)
    if source_type == "json":
        return extract_from_json(content, source_artifact_ref, max_rows=max_rows)
    return extract_from_markdown(
        content,
        source_artifact_ref,
        max_sections=max_sections,
        max_rows_per_table=max_rows,
    )


def get_first_table(slices: list[SourceContentSlice]) -> tuple[list[str], list[list[str]]] | None:
    """Return (headers, rows) from first table-like slice, or None."""
    for s in slices:
        if s.section_type == "table" and s.structured_rows:
            headers = s.structured_rows[0]
            rows = s.structured_rows[1:]
            return (headers, rows)
    return None


def get_narrative_sections(slices: list[SourceContentSlice]) -> list[tuple[str, str]]:
    """Return list of (heading, text) for narrative/checklist sections."""
    out: list[tuple[str, str]] = []
    for s in slices:
        if s.section_type in ("narrative", "checklist", "summary") and s.text:
            out.append((s.heading or "Section", s.text))
    return out


def get_checklist_items(slices: list[SourceContentSlice]) -> list[str]:
    """Return checklist item lines from slices."""
    out: list[str] = []
    for s in slices:
        if s.section_type == "checklist" and s.text:
            for line in s.text.split("\n"):
                line = line.strip()
                if line:
                    out.append(line)
    return out
