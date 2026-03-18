"""
M13/M14: Creative package adapter — brief + storyboard + shotlist package, asset structure.
M14: Content-aware population from source (brief, shotlist, checklist, revision plan, README).
"""

from __future__ import annotations

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
)
from workflow_dataset.output_adapters.content_population import build_population_result


def _brief_from_sections(sections: list[tuple[str, str]], source_note: str) -> str:
    lines = ["# Creative brief", ""]
    for heading, text in sections[:15]:
        if heading and text:
            lines.append(f"## {heading}")
            lines.append("")
            lines.append(text[:3000])
            lines.append("")
    if not any(s[1] for s in sections):
        lines.append("(Placeholder: replace with your brief content.)")
        lines.append("")
    lines.append(f"Source: {source_note}")
    return "\n".join(lines)


def _shotlist_from_table_slice(slices: list, default: str) -> str:
    from workflow_dataset.output_adapters.content_extractors import get_first_table
    table = get_first_table(slices)
    if not table:
        return default
    headers, rows = table
    lines = ["# Shot list", "", "| # | Shot | Description | Duration |", "|---|------|-------------|----------|"]
    for i, row in enumerate(rows[:50], 1):
        cells = (row + ["", "", ""])[:4]
        lines.append(f"| {i} | {cells[0]} | {cells[1]} | {cells[2]} |")
    return "\n".join(lines)


class CreativePackageAdapter(BaseOutputAdapter):
    adapter_type = "creative_package"

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

        (bundle_dir / "brief").mkdir(exist_ok=True)
        brief_md = bundle_dir / "brief" / "creative_brief.md"
        if narrative_sections:
            brief_md.write_text(_brief_from_sections(narrative_sections, source_note), encoding="utf-8")
            populated_paths.append(f"{bundle_id}/brief/creative_brief.md")
        else:
            brief_md.write_text(
                "# Creative brief\n\n(Placeholder: replace with your brief content.)\n\nSource: " + source_note + "\n",
                encoding="utf-8",
            )
            scaffold_only_paths.append(f"{bundle_id}/brief/creative_brief.md")
        output_paths.append(f"{bundle_id}/brief/creative_brief.md")

        (bundle_dir / "storyboard").mkdir(exist_ok=True)
        (bundle_dir / "storyboard" / "frames").mkdir(exist_ok=True)
        sb_readme = bundle_dir / "storyboard" / "README.md"
        sb_readme.write_text("# Storyboard\n\nAdd frame markdown or images in frames/.\n", encoding="utf-8")
        scaffold_only_paths.append(f"{bundle_id}/storyboard/README.md")
        output_paths.append(f"{bundle_id}/storyboard/README.md")

        shotlist = bundle_dir / "storyboard" / "shotlist.md"
        default_shotlist = "# Shot list\n\n| # | Shot | Description | Duration |\n|---|------|-------------|----------|\n"
        shotlist.write_text(_shotlist_from_table_slice(slices, default_shotlist), encoding="utf-8")
        if slices:
            populated_paths.append(f"{bundle_id}/storyboard/shotlist.md")
        else:
            scaffold_only_paths.append(f"{bundle_id}/storyboard/shotlist.md")
        output_paths.append(f"{bundle_id}/storyboard/shotlist.md")

        (bundle_dir / "assets").mkdir(exist_ok=True)
        (bundle_dir / "assets" / "source").mkdir(exist_ok=True)
        (bundle_dir / "assets" / "exports").mkdir(exist_ok=True)
        export_guide = bundle_dir / "export_naming_guide.md"
        export_guide.write_text(
            "# Export naming guide\n\nUse consistent prefixes: project_shot_v01.png, project_sequence_01.mp4.\n",
            encoding="utf-8",
        )
        scaffold_only_paths.append(f"{bundle_id}/export_naming_guide.md")
        output_paths.append(f"{bundle_id}/export_naming_guide.md")
        revision_plan = bundle_dir / "revision_plan.md"
        revision_plan.write_text("# Revision plan\n\n| Version | Date | Changes |\n|---------|------|----------|\n", encoding="utf-8")
        scaffold_only_paths.append(f"{bundle_id}/revision_plan.md")
        output_paths.append(f"{bundle_id}/revision_plan.md")

        checklist = bundle_dir / "deliverables_checklist.md"
        checklist_lines = ["# Deliverables checklist", ""]
        if checklist_items:
            for item in checklist_items[:25]:
                checklist_lines.append(item if item.strip().startswith("-") else f"- [ ] {item}")
            populated_paths.append(f"{bundle_id}/deliverables_checklist.md")
        else:
            checklist_lines.extend(["- [ ] Brief approved", "- [ ] Storyboard locked", "- [ ] Shot list final", "- [ ] Assets in exports/"])
            scaffold_only_paths.append(f"{bundle_id}/deliverables_checklist.md")
        checklist.write_text("\n".join(checklist_lines), encoding="utf-8")
        output_paths.append(f"{bundle_id}/deliverables_checklist.md")

        readme = bundle_dir / "README.md"
        readme_text = f"# Creative package: {bundle_id}\n\nBrief + storyboard + shotlist + asset structure. Production-ready scaffold.\nAdapter: {self.adapter_type}\n"
        if populated_paths:
            readme_text += "\nContent-populated from source artifact.\n"
        readme.write_text(readme_text, encoding="utf-8")
        scaffold_only_paths.append(f"{bundle_id}/README.md")
        output_paths.append(f"{bundle_id}/README.md")

        population_result_ref = ""
        if populate and (narrative_sections or checklist_items or slices):
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
