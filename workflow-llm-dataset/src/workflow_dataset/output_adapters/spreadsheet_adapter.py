"""
M13/M14: Spreadsheet/workbook adapter — multi-sheet CSV bundle, tab plans, column dicts.
M14: Content-aware population from source; optional XLSX workbook when allow_xlsx.
"""

from __future__ import annotations

import csv
from pathlib import Path

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.output_adapters.base_adapter import BaseOutputAdapter, read_source_artifact
from workflow_dataset.output_adapters.adapter_models import (
    OutputAdapterRequest,
    OutputBundle,
    OutputBundleManifest,
)
from workflow_dataset.output_adapters.content_extractors import (
    extract_content,
    get_first_table,
    get_narrative_sections,
)
from workflow_dataset.output_adapters.content_population import build_population_result
from workflow_dataset.output_adapters.population_models import PopulatedTablePlan


def _write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def _write_xlsx_workbook(path: Path, sheets: list[tuple[str, list[str], list[list[str]]]]) -> bool:
    """Write multi-sheet XLSX. Returns True if successful. Uses xlsxwriter (no styling)."""
    try:
        import xlsxwriter
    except ImportError:
        return False
    try:
        with xlsxwriter.Workbook(str(path)) as workbook:
            for sheet_name, headers, rows in sheets:
                safe_name = sheet_name[:31]  # Excel limit
                ws = workbook.add_worksheet(safe_name)
                for col, h in enumerate(headers):
                    ws.write(0, col, h)
                for r, row in enumerate(rows, start=1):
                    for c, val in enumerate(row):
                        if c < len(headers):
                            ws.write(r, c, val)
        return True
    except Exception:
        return False


class SpreadsheetAdapter(BaseOutputAdapter):
    adapter_type = "spreadsheet"

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
        population_result_ref = ""
        source_ref = request.artifact_id or request.review_id or (Path(request.source_artifact_path).name if request.source_artifact_path else "")

        # Extract content when populating
        slices: list = []
        table_plans: list[PopulatedTablePlan] = []
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
                table_result = get_first_table(slices)
                narrative_sections = get_narrative_sections(slices)
                if table_result:
                    headers, rows = table_result
                    table_plans = [
                        PopulatedTablePlan(
                            table_id=stable_id("tbl", bundle_id, "data", ts, prefix="tbl"),
                            target_file="data.csv",
                            headers=headers,
                            rows=rows,
                            source_refs=[source_ref] if source_ref else [],
                            created_utc=ts,
                        )
                    ]

        # Summary sheet
        summary_csv = bundle_dir / "summary.csv"
        if table_plans or narrative_sections:
            summary_rows = [
                ["sheet_name", "description", "row_count_approx"],
                ["summary", "Overview and key metrics", str(len(narrative_sections) or 10)],
                ["data", "Primary data table", str(len(table_plans[0].rows) if table_plans else 0)],
                ["tracker", "Task or item tracker", "0"],
            ]
            _write_csv(summary_csv, summary_rows[0], summary_rows[1:])
            populated_paths.append(f"{bundle_id}/summary.csv")
        else:
            summary_csv.write_text(
                "sheet_name,description,row_count_approx\n"
                "summary,Overview and key metrics,10\n"
                "data,Primary data table,0\n"
                "tracker,Task or item tracker,0\n",
                encoding="utf-8",
            )
            scaffold_only_paths.append(f"{bundle_id}/summary.csv")
        output_paths.append(f"{bundle_id}/summary.csv")

        # Data sheet
        data_csv = bundle_dir / "data.csv"
        if table_plans:
            plan = table_plans[0]
            _write_csv(data_csv, plan.headers, plan.rows)
            populated_paths.append(f"{bundle_id}/data.csv")
        else:
            data_csv.write_text("id,label,value,notes\n", encoding="utf-8")
            scaffold_only_paths.append(f"{bundle_id}/data.csv")
        output_paths.append(f"{bundle_id}/data.csv")

        # Tracker: optional second table or default headers
        tracker_csv = bundle_dir / "tracker.csv"
        tracker_headers = ["item_id", "title", "status", "owner", "due_date", "notes"]
        if len(table_plans) > 1:
            plan = table_plans[1]
            _write_csv(tracker_csv, plan.headers, plan.rows)
            populated_paths.append(f"{bundle_id}/tracker.csv")
        else:
            _write_csv(tracker_csv, tracker_headers, [])
            scaffold_only_paths.append(f"{bundle_id}/tracker.csv")
        output_paths.append(f"{bundle_id}/tracker.csv")

        # Tab plan markdown
        tab_plan = bundle_dir / "tab_plan.md"
        tab_lines = [
            "# Tab plan",
            "",
            "| Tab | Purpose | Key columns |",
            "|-----|--------|-------------|",
        ]
        if table_plans:
            tab_lines.append(f"| summary | Overview | sheet_name, description, row_count_approx |")
            tab_lines.append(f"| data | Primary data | {', '.join(table_plans[0].headers[:6])} |")
        else:
            tab_lines.append("| summary | Overview | sheet_name, description |")
            tab_lines.append("| data | Primary data | id, label, value, notes |")
        tab_lines.append("| tracker | Tasks/items | item_id, title, status, owner, due_date |")
        tab_plan.write_text("\n".join(tab_lines), encoding="utf-8")
        if table_plans or narrative_sections:
            populated_paths.append(f"{bundle_id}/tab_plan.md")
        else:
            scaffold_only_paths.append(f"{bundle_id}/tab_plan.md")
        output_paths.append(f"{bundle_id}/tab_plan.md")

        # Column dictionary
        column_dict = bundle_dir / "column_dictionary.md"
        col_lines = ["# Column dictionary", ""]
        if table_plans:
            for h in table_plans[0].headers:
                col_lines.append(f"- **{h}**: (from source)")
            col_lines.append("")
            col_lines.append("- **item_id**, **title**, **status**, **owner**, **due_date**: Tracker fields")
        else:
            col_lines.append("- **id**: Unique identifier")
            col_lines.append("- **label**: Short label")
            col_lines.append("- **value**: Numeric or text value")
            col_lines.append("- **notes**: Free-form notes")
            col_lines.append("- **item_id**, **title**, **status**, **owner**, **due_date**: Tracker fields")
        column_dict.write_text("\n".join(col_lines), encoding="utf-8")
        if table_plans:
            populated_paths.append(f"{bundle_id}/column_dictionary.md")
        else:
            scaffold_only_paths.append(f"{bundle_id}/column_dictionary.md")
        output_paths.append(f"{bundle_id}/column_dictionary.md")

        # README
        readme = bundle_dir / "README.md"
        readme_text = (
            f"# Spreadsheet bundle: {bundle_id}\n\n"
            "Multi-sheet-style CSV bundle. Import summary.csv, data.csv, tracker.csv into your workbook tool.\n"
            f"Source: {request.source_artifact_path or 'generated'}\n"
            f"Adapter: {self.adapter_type}\n"
        )
        if populated_paths:
            readme_text += "\nContent-populated from source artifact.\n"
        readme.write_text(readme_text, encoding="utf-8")
        scaffold_only_paths.append(f"{bundle_id}/README.md")
        output_paths.append(f"{bundle_id}/README.md")

        # Optional XLSX
        xlsx_created = False
        if allow_xlsx:
            xlsx_path = bundle_dir / "workbook.xlsx"
            data_headers = table_plans[0].headers if table_plans else ["id", "label", "value", "notes"]
            data_rows = table_plans[0].rows if table_plans else []
            sheets = [
                ("Summary", ["sheet_name", "description", "row_count_approx"], [["summary", "Overview", "10"], ["data", "Primary data", str(len(data_rows))], ["tracker", "Tracker", "0"]]),
                ("Data", data_headers, data_rows),
                ("Tracker", tracker_headers, []),
            ]
            if _write_xlsx_workbook(xlsx_path, sheets):
                output_paths.append(f"{bundle_id}/workbook.xlsx")
                xlsx_created = True

        # Population result ref for audit
        if populate and (table_plans or narrative_sections):
            pop_result = build_population_result(
                request.adapter_request_id,
                populated_sections=[],
                populated_tables=table_plans,
                fallback_used=fallback_used,
            )
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
            xlsx_created=xlsx_created,
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
