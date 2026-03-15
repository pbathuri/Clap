"""
M13/M14: Design/architecture package adapter — design brief, issue checklist, deliverable structure.
M14: Content-aware population for brief, issue checklist, handoff note.
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
    get_first_table,
)
from workflow_dataset.output_adapters.content_population import build_population_result


def _brief_from_sections(sections: list[tuple[str, str]], source_note: str) -> str:
    lines = ["# Design brief", ""]
    for heading, text in sections[:15]:
        if heading and text:
            lines.append(f"## {heading}")
            lines.append("")
            lines.append(text[:3000])
            lines.append("")
    if not any(s[1] for s in sections):
        lines.append("(Placeholder: scope, constraints, deliverables.)")
        lines.append("")
    lines.append(f"Source: {source_note}")
    return "\n".join(lines)


def _issues_table_from_slices(slices: list) -> str:
    from workflow_dataset.output_adapters.content_extractors import get_first_table
    table = get_first_table(slices)
    lines = ["# Issue / revision checklist", "", "| ID | Description | Status | Assigned |", "|----|-------------|--------|----------|"]
    if table:
        headers, rows = table
        for i, row in enumerate(rows[:30], 1):
            cells = (row + ["", "", "", ""])[:4]
            lines.append(f"| {i} | {cells[0]} | {cells[1]} | {cells[2]} |")
    return "\n".join(lines)


class DesignPackageAdapter(BaseOutputAdapter):
    adapter_type = "design_package"

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

        (bundle_dir / "brief").mkdir(exist_ok=True)
        design_brief = bundle_dir / "brief" / "design_brief.md"
        if narrative_sections:
            design_brief.write_text(_brief_from_sections(narrative_sections, source_note), encoding="utf-8")
            populated_paths.append(f"{bundle_id}/brief/design_brief.md")
        else:
            design_brief.write_text(
                "# Design brief\n\n(Placeholder: scope, constraints, deliverables.)\n\nSource: " + source_note + "\n",
                encoding="utf-8",
            )
            scaffold_only_paths.append(f"{bundle_id}/brief/design_brief.md")
        output_paths.append(f"{bundle_id}/brief/design_brief.md")

        issues = bundle_dir / "issue_revision_checklist.md"
        issues_content = _issues_table_from_slices(slices)
        issues.write_text(issues_content, encoding="utf-8")
        if slices:
            populated_paths.append(f"{bundle_id}/issue_revision_checklist.md")
        else:
            scaffold_only_paths.append(f"{bundle_id}/issue_revision_checklist.md")
        output_paths.append(f"{bundle_id}/issue_revision_checklist.md")

        (bundle_dir / "deliverables").mkdir(exist_ok=True)
        (bundle_dir / "deliverables" / "presentation").mkdir(exist_ok=True)
        (bundle_dir / "deliverables" / "drawings").mkdir(exist_ok=True)
        (bundle_dir / "deliverables" / "references").mkdir(exist_ok=True)
        deliv_readme = bundle_dir / "deliverables" / "README.md"
        deliv_readme.write_text(
            "# Deliverables\n\n- presentation/: Decks, renders\n- drawings/: Drawing issue scaffold\n- references/: Reference bundle\n",
            encoding="utf-8",
        )
        scaffold_only_paths.append(f"{bundle_id}/deliverables/README.md")
        output_paths.append(f"{bundle_id}/deliverables/README.md")

        handoff = bundle_dir / "handoff_note.md"
        handoff_text = "# Handoff note\n\nPackage prepared for adoption. Review brief and issue checklist before apply.\n"
        if narrative_sections:
            handoff_text += "\n## Summary from source\n\n" + "\n\n".join(
                f"**{h}**: {t[:500]}" for h, t in narrative_sections[:3]
            )
            populated_paths.append(f"{bundle_id}/handoff_note.md")
        else:
            scaffold_only_paths.append(f"{bundle_id}/handoff_note.md")
        handoff.write_text(handoff_text, encoding="utf-8")
        output_paths.append(f"{bundle_id}/handoff_note.md")

        readme = bundle_dir / "README.md"
        readme_text = f"# Design package: {bundle_id}\n\nDesign brief + issue checklist + deliverable folder structure.\nAdapter: {self.adapter_type}\n"
        if populated_paths:
            readme_text += "\nContent-populated from source artifact.\n"
        readme.write_text(readme_text, encoding="utf-8")
        scaffold_only_paths.append(f"{bundle_id}/README.md")
        output_paths.append(f"{bundle_id}/README.md")

        population_result_ref = ""
        if populate and (narrative_sections or slices):
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
