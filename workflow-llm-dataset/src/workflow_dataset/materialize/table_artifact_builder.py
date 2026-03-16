"""
Generate real .csv (and optionally .xlsx) table scaffolds in the sandbox.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from workflow_dataset.materialize.materialize_models import MaterializedArtifact
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


# Draft type -> (csv_headers, artifact_type)
TABLE_SCAFFOLDS: dict[str, tuple[list[str], str]] = {
    "inventory_sheet_scaffold": (
        ["Item ID", "Description", "Quantity", "Unit", "Location", "Last count", "Notes"],
        "csv_inventory",
    ),
    "vendor_order_tracking_scaffold": (
        ["Vendor ID", "Name", "Contact", "Notes"],
        "csv_vendors",
    ),
    "monthly_reporting_workbook": (
        ["Category", "Value", "Variance", "Notes"],
        "csv_report",
    ),
    "reconciliation_checklist": (
        ["Source", "Match criteria", "Status", "Exceptions", "Sign-off"],
        "csv_reconciliation",
    ),
}


def build_csv_artifact(
    workspace_path: Path | str,
    draft_type: str,
    title: str,
    headers: list[str] | None = None,
    request_id: str = "",
    project_id: str = "",
    draft_ref: str = "",
    extra_sheets: list[tuple[str, list[str]]] | None = None,
) -> MaterializedArtifact | None:
    """
    Write a CSV file (and optionally more CSV files for "sheets") into the workspace.
    extra_sheets: list of (sheet_name, headers) for multi-sheet-style output (separate CSV files).
    """
    workspace_path = Path(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    if headers is None:
        tup = TABLE_SCAFFOLDS.get(draft_type)
        if tup:
            headers, art_type = tup
        else:
            headers = ["Column 1", "Column 2", "Notes"]
            art_type = "csv_sheet"
    else:
        art_type = "csv_sheet"
    safe_title = "".join(c for c in title.replace(" ", "_") if c.isalnum() or c in "_-")[:80] or "sheet"
    filename = f"{safe_title}.csv"
    out_path = workspace_path / filename
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerow([])  # placeholder row
    artifact_id = stable_id("art", "csv", request_id or filename, utc_now_iso(), prefix="art")
    return MaterializedArtifact(
        artifact_id=artifact_id,
        request_id=request_id,
        project_id=project_id,
        artifact_type=art_type,
        sandbox_path=filename,
        title=title,
        summary=f"CSV with headers: {', '.join(headers[:5])}{'...' if len(headers) > 5 else ''}",
        provenance_refs=[draft_ref] if draft_ref else [],
        created_utc=utc_now_iso(),
    )


def build_tracker_csv_files(
    workspace_path: Path | str,
    draft_type: str,
    title: str,
    request_id: str = "",
    project_id: str = "",
    draft_ref: str = "",
) -> list[MaterializedArtifact]:
    """
    Build one or more CSV files for trackers (e.g. vendor + orders + line_items).
    Returns list of MaterializedArtifact.
    """
    workspace_path = Path(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    artifacts: list[MaterializedArtifact] = []
    if draft_type == "vendor_order_tracking_scaffold":
        sheets = [
            ("Vendors", ["Vendor ID", "Name", "Contact", "Notes"]),
            ("Orders", ["Order ID", "Vendor ID", "Date", "Status"]),
            ("Line_items", ["Order ID", "Item", "Quantity", "Unit"]),
            ("Status_log", ["Order ID", "Timestamp", "Status", "Notes"]),
        ]
    else:
        tup = TABLE_SCAFFOLDS.get(draft_type)
        if tup:
            sheets = [(title, tup[0])]
        else:
            sheets = [(title, ["Column 1", "Column 2", "Notes"])]
    for sheet_name, headers in sheets:
        safe = "".join(c for c in sheet_name.replace(" ", "_") if c.isalnum() or c in "_-")[:40]
        filename = f"{safe}.csv"
        out_path = workspace_path / filename
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerow([])
        artifact_id = stable_id("art", "csv", request_id or filename, utc_now_iso(), prefix="art")
        artifacts.append(MaterializedArtifact(
            artifact_id=artifact_id,
            request_id=request_id,
            project_id=project_id,
            artifact_type="csv_tracker",
            sandbox_path=filename,
            title=sheet_name,
            summary=f"CSV: {', '.join(headers[:4])}",
            provenance_refs=[draft_ref] if draft_ref else [],
            created_utc=utc_now_iso(),
        ))
    return artifacts
