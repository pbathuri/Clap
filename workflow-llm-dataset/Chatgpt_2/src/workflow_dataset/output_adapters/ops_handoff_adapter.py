"""
M13/M14: Ops/handoff adapter — report, checklist, memo, tracker + README.
M14: Content-aware population for report, checklist, memo, tracker.
"""

from __future__ import annotations

import csv
from pathlib import Path

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.output_adapters.base_adapter import BaseOutputAdapter
from workflow_dataset.output_adapters.adapter_models import (
    OutputAdapterRequest,
    OutputBundle,
    OutputBundleManifest,
)
from workflow_dataset.output_adapters.content_extractors import (
    extract_content,
    get_narrative_sections,
    get_checklist_items,
    get_first_table,
)
from workflow_dataset.output_adapters.content_population import build_population_result


def _report_from_sections(sections: list[tuple[str, str]], source_note: str) -> str:
    lines = ["# Report", ""]
    for heading, text in sections[:20]:
        if heading and text:
            lines.append(f"## {heading}")
            lines.append("")
            lines.append(text[:4000])
            lines.append("")
    if not any(s[1] for s in sections):
        lines.append("(Placeholder: summary and findings.)")
        lines.append("")
    lines.append(f"Source: {source_note}")
    return "\n".join(lines)


def _checklist_from_items(items: list[str], default_header: str) -> str:
    lines = ["# Checklist", "", "| Item | Done | Notes |", "|------|------|-------|"]
    if items:
        for item in items[:40]:
            clean = item.replace("- [ ] ", "").replace("- [x] ", "").strip()
            lines.append(f"| {clean} | | |")
    return "\n".join(lines)


def _memo_from_sections(sections: list[tuple[str, str]]) -> str:
    lines = ["# Memo", ""]
    if sections:
        for heading, text in sections[:5]:
            lines.append(f"## {heading}")
            lines.append("")
            lines.append(text[:2000])
            lines.append("")
    else:
        lines.append("(Handoff memo.)")
    return "\n".join(lines)


class OpsHandoffAdapter(BaseOutputAdapter):
    adapter_type = "ops_handoff"

    def create_bundle(
        self,
        request: OutputAdapterRequest,
        workspace_path: Path,
        source_content: str = "",
        style_profile_refs: list[str] | None = None,
        revision_note: str = "",
        populate: bool = False,
        allow_xlsx: bool = False,
        population_max_rows: int = 1000,
        population_max_sections: int = 50,
    ) -> tuple[OutputBundle, OutputBundleManifest]:
        ts = utc_now_iso()
        bundle_id = stable_id("bundle", request.adapter_request_id or "req", self.adapter_type, ts, prefix="bundle")
        bundle_dir = workspace_path / bundle_id
        bundle_dir.mkdir(parents=True, exist_ok=True)
        output_paths: list[str] = []
        populated_paths: list[str] = []
        scaffold_only_paths: list[str] = []
        fallback_used = True
        source_ref = request.artifact_id or request.review_id or (Path(request.source_artifact_path).name if request.source_artifact_path else "")
        source_note = request.source_artifact_path or "generated"

        slices: list = []
        narrative_sections: list[tuple[str, str]] = []
        checklist_items: list[str] = []
        if populate and source_content and source_content.strip():
            slices = extract_content(
                source_content,
                source_artifact_ref=source_ref,
                source_path=request.source_artifact_path,
                max_sections=population_max_sections,
                max_rows=population_max_rows,
            )
            if slices:
                fallback_used = False
                narrative_sections = get_narrative_sections(slices)
                checklist_items = get_checklist_items(slices)

        report_md = bundle_dir / "report.md"
        if narrative_sections:
            report_md.write_text(_report_from_sections(narrative_sections, source_note), encoding="utf-8")
            populated_paths.append(f"{bundle_id}/report.md")
        else:
            report_md.write_text("# Report\n\n(Placeholder: summary and findings.)\n\nSource: " + source_note + "\n", encoding="utf-8")
            scaffold_only_paths.append(f"{bundle_id}/report.md")
        output_paths.append(f"{bundle_id}/report.md")

        checklist = bundle_dir / "checklist.md"
        checklist.write_text(_checklist_from_items(checklist_items, "Item"), encoding="utf-8")
        if checklist_items:
            populated_paths.append(f"{bundle_id}/checklist.md")
        else:
            scaffold_only_paths.append(f"{bundle_id}/checklist.md")
        output_paths.append(f"{bundle_id}/checklist.md")

        memo = bundle_dir / "memo.md"
        memo.write_text(_memo_from_sections(narrative_sections), encoding="utf-8")
        if narrative_sections:
            populated_paths.append(f"{bundle_id}/memo.md")
        else:
            scaffold_only_paths.append(f"{bundle_id}/memo.md")
        output_paths.append(f"{bundle_id}/memo.md")

        tracker = bundle_dir / "tracker.csv"
        tracker_headers = ["id", "item", "status", "owner", "due", "notes"]
        table = get_first_table(slices) if slices else None
        if table:
            headers, rows = table
            with tracker.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(headers if len(headers) >= 3 else tracker_headers)
                w.writerows(rows[:200])
            populated_paths.append(f"{bundle_id}/tracker.csv")
        else:
            tracker.write_text("id,item,status,owner,due,notes\n", encoding="utf-8")
            scaffold_only_paths.append(f"{bundle_id}/tracker.csv")
        output_paths.append(f"{bundle_id}/tracker.csv")

        readme = bundle_dir / "README.md"
        readme_text = f"# Ops handoff bundle: {bundle_id}\n\nReport + checklist + memo + tracker. Ready for adoption.\nAdapter: {self.adapter_type}\n"
        if populated_paths:
            readme_text += "\nContent-populated from source artifact.\n"
        readme.write_text(readme_text, encoding="utf-8")
        scaffold_only_paths.append(f"{bundle_id}/README.md")
        output_paths.append(f"{bundle_id}/README.md")

        population_result_ref = ""
        if populate and (narrative_sections or checklist_items or (table is not None)):
            pop_result = build_population_result(request.adapter_request_id, [], [], fallback_used=fallback_used)
            population_result_ref = pop_result.population_id

        manifest_id = stable_id("obm", bundle_id, ts, prefix="obm")
        manifest = OutputBundleManifest(
            manifest_id=manifest_id,
            bundle_id=bundle_id,
            source_artifact_refs=[source_ref] if source_ref else [],
            generated_paths=list(output_paths),
            adapter_used=self.adapter_type,
            style_profile_refs=style_profile_refs or [],
            revision_note=revision_note,
            created_utc=ts,
            populated_paths=populated_paths,
            scaffold_only_paths=scaffold_only_paths,
            fallback_used=fallback_used,
            xlsx_created=False,
            population_result_ref=population_result_ref,
        )
        manifest_path = bundle_dir / "BUNDLE_MANIFEST.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        output_paths.append(f"{bundle_id}/BUNDLE_MANIFEST.json")

        bundle = OutputBundle(
            bundle_id=bundle_id,
            adapter_request_id=request.adapter_request_id,
            bundle_type=self.adapter_type,
            workspace_path=str(workspace_path.resolve()),
            output_paths=output_paths,
            manifest_path=str(manifest_path),
            created_utc=ts,
        )
        return bundle, manifest
