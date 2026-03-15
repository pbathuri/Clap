"""
M13: Spreadsheet/workbook adapter — multi-sheet CSV bundle, tab plans, column dicts, tracker templates.

No XLSX dependency by default; multi-file CSV bundle is workflow-native and adoptable.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.output_adapters.base_adapter import BaseOutputAdapter, read_source_artifact
from workflow_dataset.output_adapters.adapter_models import (
    OutputAdapterRequest,
    OutputBundle,
    OutputBundleManifest,
)


class SpreadsheetAdapter(BaseOutputAdapter):
    adapter_type = "spreadsheet"

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

        # Multi-sheet-style CSV bundle: summary sheet + data sheet + tab plan + column dict
        output_paths: list[str] = []
        summary_csv = bundle_dir / "summary.csv"
        summary_csv.write_text(
            "sheet_name,description,row_count_approx\n"
            "summary,Overview and key metrics,10\n"
            "data,Primary data table,0\n"
            "tracker,Task or item tracker,0\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/summary.csv")
        data_csv = bundle_dir / "data.csv"
        data_csv.write_text("id,label,value,notes\n", encoding="utf-8")
        output_paths.append(f"{bundle_id}/data.csv")
        tracker_csv = bundle_dir / "tracker.csv"
        tracker_csv.write_text("item_id,title,status,owner,due_date,notes\n", encoding="utf-8")
        output_paths.append(f"{bundle_id}/tracker.csv")
        tab_plan = bundle_dir / "tab_plan.md"
        tab_plan.write_text(
            "# Tab plan\n\n"
            "| Tab | Purpose | Key columns |\n"
            "|-----|--------|-------------|\n"
            "| summary | Overview | sheet_name, description |\n"
            "| data | Primary data | id, label, value, notes |\n"
            "| tracker | Tasks/items | item_id, title, status, owner, due_date |\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/tab_plan.md")
        column_dict = bundle_dir / "column_dictionary.md"
        column_dict.write_text(
            "# Column dictionary\n\n"
            "- **id**: Unique identifier\n"
            "- **label**: Short label\n"
            "- **value**: Numeric or text value\n"
            "- **notes**: Free-form notes\n"
            "- **item_id**, **title**, **status**, **owner**, **due_date**: Tracker fields\n",
            encoding="utf-8",
        )
        output_paths.append(f"{bundle_id}/column_dictionary.md")
        readme = bundle_dir / "README.md"
        readme.write_text(
            f"# Spreadsheet bundle: {bundle_id}\n\n"
            "Multi-sheet-style CSV bundle. Import summary.csv, data.csv, tracker.csv into your workbook tool.\n"
            f"Source: {request.source_artifact_path or 'generated'}\n"
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
