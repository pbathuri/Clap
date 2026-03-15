"""
M13: Ops/handoff adapter — report package, checklist + memo, tracker + README, handoff bundle.

Ready for safe adoption into real project folders.
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


class OpsHandoffAdapter(BaseOutputAdapter):
    adapter_type = "ops_handoff"

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

        report_md = bundle_dir / "report.md"
        report_md.write_text(
            "# Report\n\n"
            "(Placeholder: summary and findings.)\n\n"
            f"Source: {request.source_artifact_path or 'generated'}\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/report.md")
        checklist = bundle_dir / "checklist.md"
        checklist.write_text(
            "# Checklist\n\n"
            "| Item | Done | Notes |\n"
            "|------|------|-------|\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/checklist.md")
        memo = bundle_dir / "memo.md"
        memo.write_text("# Memo\n\n(Handoff memo.)\n", encoding="utf-8")
        output_paths.append(f"{bundle_id}/memo.md")
        tracker = bundle_dir / "tracker.csv"
        tracker.write_text("id,item,status,owner,due,notes\n", encoding="utf-8")
        output_paths.append(f"{bundle_id}/tracker.csv")
        readme = bundle_dir / "README.md"
        readme.write_text(
            f"# Ops handoff bundle: {bundle_id}\n\n"
            "Report + checklist + memo + tracker. Ready for adoption.\n"
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
