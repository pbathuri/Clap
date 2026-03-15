"""
M13: Design/architecture package adapter — design brief, issue checklist, deliverable structure.

Package-level scaffold; no proprietary CAD/design file generation.
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


class DesignPackageAdapter(BaseOutputAdapter):
    adapter_type = "design_package"

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
        design_brief = bundle_dir / "brief" / "design_brief.md"
        design_brief.write_text(
            "# Design brief\n\n"
            "(Placeholder: scope, constraints, deliverables.)\n\n"
            f"Source: {request.source_artifact_path or 'generated'}\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/brief/design_brief.md")
        issues = bundle_dir / "issue_revision_checklist.md"
        issues.write_text(
            "# Issue / revision checklist\n\n"
            "| ID | Description | Status | Assigned |\n"
            "|----|-------------|--------|----------|\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/issue_revision_checklist.md")
        (bundle_dir / "deliverables").mkdir(exist_ok=True)
        (bundle_dir / "deliverables" / "presentation").mkdir(exist_ok=True)
        (bundle_dir / "deliverables" / "drawings").mkdir(exist_ok=True)
        (bundle_dir / "deliverables" / "references").mkdir(exist_ok=True)
        deliv_readme = bundle_dir / "deliverables" / "README.md"
        deliv_readme.write_text(
            "# Deliverables\n\n"
            "- presentation/: Decks, renders\n"
            "- drawings/: Drawing issue scaffold\n"
            "- references/: Reference bundle\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/deliverables/README.md")
        handoff = bundle_dir / "handoff_note.md"
        handoff.write_text(
            "# Handoff note\n\n"
            "Package prepared for adoption. Review brief and issue checklist before apply.\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/handoff_note.md")
        readme = bundle_dir / "README.md"
        readme.write_text(
            f"# Design package: {bundle_id}\n\n"
            "Design brief + issue checklist + deliverable folder structure.\n"
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
