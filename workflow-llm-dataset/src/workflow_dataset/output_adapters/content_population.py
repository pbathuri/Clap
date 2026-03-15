"""
M14: Content population orchestration. Bridges source content into bundle adapters.

Uses content_extractors for deterministic extraction; produces PopulationResult
for manifest/provenance. No cloud; sandbox-first.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.output_adapters.content_extractors import (
    extract_content,
    get_first_table,
    get_narrative_sections,
    get_checklist_items,
)
from workflow_dataset.output_adapters.population_models import (
    PopulationResult,
    PopulatedSection,
    PopulatedTablePlan,
    SourceContentSlice,
)
from workflow_dataset.output_adapters.base_adapter import read_source_artifact
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def extract_from_artifact(
    source_artifact_path: str | Path,
    source_artifact_ref: str = "",
    source_content: str | None = None,
    max_sections: int = 50,
    max_rows: int = 1000,
) -> list[SourceContentSlice]:
    """
    Load artifact (or use provided content) and extract slices.
    Returns empty list if file missing and content not provided.
    """
    content = source_content
    if content is None:
        content = read_source_artifact(source_artifact_path)
    if not content or not content.strip():
        return []
    ref = source_artifact_ref or str(Path(source_artifact_path).name) if source_artifact_path else "inline"
    return extract_content(
        content,
        source_artifact_ref=ref,
        source_path=source_artifact_path,
        max_sections=max_sections,
        max_rows=max_rows,
    )


def build_population_result(
    adapter_request_id: str,
    populated_sections: list[PopulatedSection],
    populated_tables: list[PopulatedTablePlan],
    fallback_used: bool = False,
) -> PopulationResult:
    """Build a PopulationResult for manifest/provenance."""
    ts = utc_now_iso()
    return PopulationResult(
        population_id=stable_id("pop", adapter_request_id, ts, prefix="pop"),
        adapter_request_id=adapter_request_id,
        populated_sections=populated_sections,
        populated_tables=populated_tables,
        fallback_used=fallback_used,
        created_utc=ts,
    )


def slices_to_table_plans(
    slices: list[SourceContentSlice],
    adapter_type: str,
    target_files: list[str],
) -> list[PopulatedTablePlan]:
    """
    Convert table-like slices into PopulatedTablePlan list.
    target_files: e.g. ["data.csv", "tracker.csv"] — we assign first table to first file, etc.
    """
    ts = utc_now_iso()
    plans: list[PopulatedTablePlan] = []
    table_slices = [s for s in slices if s.section_type == "table" and s.structured_rows]
    for i, slc in enumerate(table_slices):
        target = target_files[i] if i < len(target_files) else target_files[-1] if target_files else "data.csv"
        headers = slc.structured_rows[0]
        rows = slc.structured_rows[1:]
        plans.append(
            PopulatedTablePlan(
                table_id=stable_id("tbl", adapter_type, target, str(i), ts, prefix="tbl"),
                target_file=target,
                headers=headers,
                rows=rows,
                source_refs=slc.provenance_refs,
                created_utc=ts,
            )
        )
    return plans


def slices_to_sections(
    slices: list[SourceContentSlice],
    adapter_type: str,
    target_file: str,
    section_name: str = "content",
) -> list[PopulatedSection]:
    """Turn narrative/checklist slices into one or more PopulatedSection for a single target file."""
    ts = utc_now_iso()
    sections: list[PopulatedSection] = []
    for i, slc in enumerate(slices):
        if slc.section_type in ("narrative", "checklist", "summary") and slc.text:
            sections.append(
                PopulatedSection(
                    section_id=stable_id("sec", adapter_type, target_file, str(i), ts, prefix="sec"),
                    adapter_type=adapter_type,
                    target_file=target_file,
                    section_name=slc.heading or section_name,
                    populated_text=slc.text,
                    source_refs=slc.provenance_refs,
                    created_utc=ts,
                )
            )
    return sections
