"""
Draft structure engine: generate structure outlines and scaffolds from setup outputs,
style profiles, and domain. No final content generation; structure only. Simulate-only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.personal.assistive_models import DraftStructure
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

# Draft type -> (title, outline, sections, naming hints)
DRAFT_TEMPLATES: dict[str, dict[str, Any]] = {
    "project_brief": {
        "title": "Project brief",
        "domain": "general",
        "outline": "# Project brief\n\n## Objective\n## Scope\n## Deliverables\n## Timeline\n## Stakeholders\n## Notes",
        "sections": ["Objective", "Scope", "Deliverables", "Timeline", "Stakeholders", "Notes"],
        "naming": ["project_brief", "brief_v1"],
    },
    "meeting_agenda": {
        "title": "Meeting agenda",
        "domain": "general",
        "outline": "# Meeting agenda\n\n## Attendees\n## Objectives\n## Discussion points\n## Decisions / actions\n## Next steps",
        "sections": ["Attendees", "Objectives", "Discussion points", "Decisions / actions", "Next steps"],
        "naming": ["agenda_YYYYMMDD", "meeting_notes"],
    },
    "weekly_review": {
        "title": "Weekly review",
        "domain": "general",
        "outline": "# Weekly review\n\n## Done\n## In progress\n## Blockers\n## Next week\n## Metrics",
        "sections": ["Done", "In progress", "Blockers", "Next week", "Metrics"],
        "naming": ["weekly_review_YYYYMMDD", "week_summary"],
    },
    "sop_outline": {
        "title": "SOP outline",
        "domain": "ops",
        "outline": "# Standard operating procedure\n\n## Purpose\n## Scope\n## Definitions\n## Procedure\n## Exceptions\n## References",
        "sections": ["Purpose", "Scope", "Definitions", "Procedure", "Exceptions", "References"],
        "naming": ["sop_<topic>", "procedure_v1"],
    },
    "planning_memo": {
        "title": "Planning memo",
        "domain": "general",
        "outline": "# Planning memo\n\n## Context\n## Options\n## Recommendation\n## Implementation\n## Risks",
        "sections": ["Context", "Options", "Recommendation", "Implementation", "Risks"],
        "naming": ["planning_memo", "memo_<topic>"],
    },
    "operating_checklist": {
        "title": "Operating checklist",
        "domain": "ops",
        "outline": "# Operating checklist\n\n## Pre-flight\n## Execution steps\n## Verification\n## Sign-off",
        "sections": ["Pre-flight", "Execution steps", "Verification", "Sign-off"],
        "naming": ["checklist_<name>", "runbook"],
    },
    "reconciliation_checklist": {
        "title": "Reconciliation checklist",
        "domain": "finance",
        "outline": "# Reconciliation checklist\n\n## Sources\n## Match criteria\n## Exceptions log\n## Sign-off",
        "sections": ["Sources", "Match criteria", "Exceptions log", "Sign-off"],
        "naming": ["recon_YYYYMMDD", "reconciliation_v1"],
    },
    "monthly_reporting_workbook": {
        "title": "Monthly reporting workbook structure",
        "domain": "finance",
        "outline": "# Monthly reporting workbook\n\n## Summary sheet\n## Detail sheets (by category)\n## Variance notes\n## Appendix",
        "sections": ["Summary", "Detail by category", "Variance notes", "Appendix"],
        "assets": ["Summary", "Detail_1", "Detail_2", "Variance_notes", "Appendix"],
        "naming": ["monthly_report_YYYYMM", "workbook_structure"],
    },
    "operations_report_outline": {
        "title": "Operations report outline",
        "domain": "ops",
        "outline": "# Operations report\n\n## Executive summary\n## Metrics\n## Issues\n## Actions\n## Forecast",
        "sections": ["Executive summary", "Metrics", "Issues", "Actions", "Forecast"],
        "naming": ["ops_report_YYYYMMDD", "operations_summary"],
    },
    "inventory_sheet_scaffold": {
        "title": "Inventory sheet scaffold",
        "domain": "ops",
        "outline": "# Inventory sheet\n\nColumns: Item ID | Description | Quantity | Unit | Location | Last count | Notes",
        "sections": ["Item list", "Summary", "Adjustments log"],
        "assets": ["Sheet1_Items", "Summary", "Adjustments"],
        "naming": ["inventory_YYYYMMDD", "stock_sheet"],
    },
    "vendor_order_tracking_scaffold": {
        "title": "Vendor/order tracking scaffold",
        "domain": "ops",
        "outline": "# Vendor/order tracking\n\nSheets: Vendors | Orders | Line items | Status log",
        "sections": ["Vendors", "Orders", "Line items", "Status log"],
        "assets": ["Vendors", "Orders", "Line_items", "Status_log"],
        "naming": ["orders_YYYYMM", "vendor_tracking"],
    },
    "creative_brief_outline": {
        "title": "Creative brief outline",
        "domain": "creative",
        "outline": "# Creative brief\n\n## Brand / client\n## Objective\n## Target audience\n## Key message\n## Tone and style\n## Deliverables\n## Timeline\n## Success criteria",
        "sections": ["Brand / client", "Objective", "Target audience", "Key message", "Tone and style", "Deliverables", "Timeline", "Success criteria"],
        "naming": ["creative_brief", "brief_<project>"],
    },
    "storyboard_shotlist_scaffold": {
        "title": "Storyboard / shotlist scaffold",
        "domain": "creative",
        "outline": "# Storyboard / shotlist\n\n## Scene / shot list\n- Shot ID | Description | Duration | Notes | Assets\n## Sequence overview\n## Key frames / thumbnails refs\n## Audio / dialogue column\n## Revision log",
        "sections": ["Scene / shot list", "Sequence overview", "Key frames refs", "Audio / dialogue", "Revision log"],
        "assets": ["Shot_01", "Shot_02", "Sequence_overview"],
        "naming": ["storyboard_v1", "shotlist_YYYYMMDD", "boards_<project>"],
    },
    "creative_project_folder_scaffold": {
        "title": "Creative project folder scaffold",
        "domain": "creative",
        "outline": "# Creative project folder\n\n/source\n/exports\n/reviews\n/assets\n/references\n/docs",
        "sections": ["source", "exports", "reviews", "assets", "references", "docs"],
        "naming": ["project_name", "v1", "final"],
    },
    "export_package_scaffold": {
        "title": "Export package scaffold",
        "domain": "creative",
        "outline": "# Export package\n\n/deliverables\n  /print\n  /web\n  /source\n/revisions",
        "sections": ["deliverables", "print", "web", "source", "revisions"],
        "naming": ["export_v1", "final", "client_review"],
    },
    "revision_naming_scaffold": {
        "title": "Revision naming scaffold",
        "domain": "creative",
        "outline": "# Revision naming convention\n\n<name>_v<N>_<stage>.ext\nStages: draft | review | final | archive",
        "sections": ["draft", "review", "final", "archive"],
        "naming": ["_v1", "_v2", "_final", "_archive"],
    },
    "deliverable_set_outline": {
        "title": "Deliverable set outline",
        "domain": "creative",
        "outline": "# Deliverable set\n\n## Primary deliverables\n## Supporting assets\n## Specs\n## Handoff checklist",
        "sections": ["Primary deliverables", "Supporting assets", "Specs", "Handoff checklist"],
        "naming": ["deliverable_set", "handoff_package"],
    },
    "asset_bundle_checklist": {
        "title": "Asset bundle checklist",
        "domain": "creative",
        "outline": "# Asset bundle checklist\n\n## Source files\n## Exports (resolutions/formats)\n## Metadata\n## Approval",
        "sections": ["Source files", "Exports", "Metadata", "Approval"],
        "naming": ["bundle_<name>", "assets_v1"],
    },
    "design_brief_structure": {
        "title": "Design brief structure",
        "domain": "design",
        "outline": "# Design brief\n\n## Project overview\n## Goals\n## Audience\n## Constraints\n## Deliverables\n## Timeline",
        "sections": ["Project overview", "Goals", "Audience", "Constraints", "Deliverables", "Timeline"],
        "naming": ["design_brief", "brief_<client>"],
    },
    "architecture_package_structure": {
        "title": "Architecture package / drawing issue scaffold",
        "domain": "design",
        "outline": "# Architecture package\n\n## Issue log\n## Drawings list\n## Revisions\n## Sign-off sheet",
        "sections": ["Issue log", "Drawings list", "Revisions", "Sign-off sheet"],
        "assets": ["Issue_log", "Drawings", "Revisions", "Sign-off"],
        "naming": ["issue_01", "revision_A", "final"],
    },
}


def generate_draft_structures(
    context: dict[str, Any],
    style_profiles: list[Any],
    draft_types: list[str] | None = None,
    project_id: str = "",
    domain_hint: str = "",
) -> list[DraftStructure]:
    """
    Generate draft structures (outlines/scaffolds) from context and style profiles.
    draft_types: subset of DRAFT_TEMPLATES keys; None = all applicable by domain.
    """
    drafts: list[DraftStructure] = []
    ts = utc_now_iso()
    domains = [d.get("label", "") for d in context.get("domains") or []]
    domain_set = set(domains) if domains else set()
    if domain_hint:
        domain_set.add(domain_hint)
    # Infer primary domain from parsed artifacts
    parsed = context.get("parsed_artifacts") or []
    for a in parsed:
        fam = a.get("artifact_family", "")
        if "spreadsheet" in fam or "tabular" in fam:
            domain_set.add("ops")
            domain_set.add("finance")
        if "text_document" in fam:
            domain_set.add("general")
        if "media" in fam or "image" in fam or "creative" in fam:
            domain_set.add("creative")
            domain_set.add("design")

    types_to_emit = draft_types or list(DRAFT_TEMPLATES.keys())
    for key in types_to_emit:
        if key not in DRAFT_TEMPLATES:
            continue
        t = DRAFT_TEMPLATES[key]
        t_domain = t.get("domain", "general")
        if t_domain != "general" and domain_set and t_domain not in domain_set:
            continue
        draft_id = stable_id("draft", key, project_id or "default", ts, prefix="draft")
        sections = t.get("sections", [])
        assets = t.get("assets", [])
        naming = t.get("naming", [])
        outline = t.get("outline", "")
        profile_refs = [p.profile_id for p in style_profiles if hasattr(p, "profile_id") and getattr(p, "domain", "") in (t_domain, "")][:3]
        drafts.append(DraftStructure(
            draft_id=draft_id,
            draft_type=key,
            project_id=project_id,
            domain=t_domain,
            title=t.get("title", key),
            structure_outline=outline,
            recommended_sections=sections,
            suggested_naming=naming,
            suggested_assets_or_tables=assets,
            style_profile_refs=profile_refs,
            confidence_score=0.75,
            created_utc=ts,
        ))
    return drafts


def persist_draft_structures(
    drafts: list[DraftStructure],
    out_dir: Path | str,
) -> Path:
    """Write draft structures to out_dir/draft_structures.json."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "draft_structures.json"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps([d.model_dump() for d in drafts], indent=2))
    return path


def load_draft_structures(out_dir: Path | str) -> list[DraftStructure]:
    """Load draft structures from out_dir/draft_structures.json."""
    path = Path(out_dir) / "draft_structures.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [DraftStructure.model_validate(d) for d in data]
