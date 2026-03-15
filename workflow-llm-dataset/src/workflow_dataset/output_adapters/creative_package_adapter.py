"""
M13: Creative package adapter — brief + storyboard + shotlist package, asset structure, export guide.

Production-ready creative package scaffold; no final video/image asset generation.
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


class CreativePackageAdapter(BaseOutputAdapter):
    adapter_type = "creative_package"

    def create_bundle(
        self,
        request: OutputAdapterRequest,
        workspace_path: Path,
        source_content: str = "",
        style_profile_refs: list[str] | None = None,
        revision_note: str = "",
    ) -> tuple[OutputBundle, OutputBundleManifest]:
        ts = utc_now_iso()
        bundle_id = stable_id("bundle", request.adapter_request_id or "req", self.adapter_type, ts, prefix="bundle")
        bundle_dir = workspace_path / bundle_id
        bundle_dir.mkdir(parents=True, exist_ok=True)
        output_paths: list[str] = []

        (bundle_dir / "brief").mkdir(exist_ok=True)
        brief_md = bundle_dir / "brief" / "creative_brief.md"
        brief_md.write_text(
            "# Creative brief\n\n"
            "(Placeholder: replace with your brief content.)\n\n"
            f"Source: {request.source_artifact_path or 'generated'}\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/brief/creative_brief.md")
        (bundle_dir / "storyboard").mkdir(exist_ok=True)
        (bundle_dir / "storyboard" / "frames").mkdir(exist_ok=True)
        sb_readme = bundle_dir / "storyboard" / "README.md"
        sb_readme.write_text("# Storyboard\n\nAdd frame markdown or images in frames/.\n", encoding="utf-8")
        output_paths.append(f"{bundle_id}/storyboard/README.md")
        shotlist = bundle_dir / "storyboard" / "shotlist.md"
        shotlist.write_text(
            "# Shot list\n\n| # | Shot | Description | Duration |\n|---|------|-------------|----------|\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/storyboard/shotlist.md")
        (bundle_dir / "assets").mkdir(exist_ok=True)
        (bundle_dir / "assets" / "source").mkdir(exist_ok=True)
        (bundle_dir / "assets" / "exports").mkdir(exist_ok=True)
        export_guide = bundle_dir / "export_naming_guide.md"
        export_guide.write_text(
            "# Export naming guide\n\n"
            "Use consistent prefixes: project_shot_v01.png, project_sequence_01.mp4.\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/export_naming_guide.md")
        revision_plan = bundle_dir / "revision_plan.md"
        revision_plan.write_text("# Revision plan\n\n| Version | Date | Changes |\n|---------|------|----------|\n", encoding="utf-8")
        output_paths.append(f"{bundle_id}/revision_plan.md")
        checklist = bundle_dir / "deliverables_checklist.md"
        checklist.write_text(
            "# Deliverables checklist\n\n"
            "- [ ] Brief approved\n"
            "- [ ] Storyboard locked\n"
            "- [ ] Shot list final\n"
            "- [ ] Assets in exports/\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/deliverables_checklist.md")
        readme = bundle_dir / "README.md"
        readme.write_text(
            f"# Creative package: {bundle_id}\n\n"
            "Brief + storyboard + shotlist + asset structure. Production-ready scaffold.\n"
            f"Adapter: {self.adapter_type}\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/README.md")

        manifest_id = stable_id("obm", bundle_id, ts, prefix="obm")
        manifest = OutputBundleManifest(
            manifest_id=manifest_id,
            bundle_id=bundle_id,
            source_artifact_refs=[request.artifact_id or request.review_id] if (request.artifact_id or request.review_id) else [],
            generated_paths=list(output_paths),
            adapter_used=self.adapter_type,
            style_profile_refs=style_profile_refs or [],
            revision_note=revision_note,
            created_utc=ts,
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
