"""
Style-aware suggestion engine: generate explainable suggestions from setup outputs,
style profiles, domain detection, and graph. No execution; simulate-only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.personal.assistive_models import StyleAwareSuggestion
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def generate_style_aware_suggestions(
    context: dict[str, Any],
    style_profiles: list[Any],
    imitation_candidates: list[Any],
    routines: list[dict[str, Any]] | None = None,
    max_per_category: int = 5,
) -> list[StyleAwareSuggestion]:
    """
    Generate style-aware suggestions from context, profiles, and candidates.
    Categories: organization, workflow, style, draft_creation.
    Every suggestion includes rationale, evidence, confidence, and pattern type.
    """
    suggestions: list[StyleAwareSuggestion] = []
    ts = utc_now_iso()
    projects = context.get("projects") or []
    domains = context.get("domains") or []
    style_signals = context.get("style_signals") or []
    parsed = context.get("parsed_artifacts") or []
    routines = routines or []

    # ---- A. Organization suggestions ----
    if len(projects) >= 2 and style_signals:
        proj_labels = [p.get("label", p.get("node_id", "")) for p in projects[:5]]
        sug_id = stable_id("style_sug", "org", "template", ts, prefix="sug")
        suggestions.append(StyleAwareSuggestion(
            suggestion_id=sug_id,
            suggestion_type="organization",
            project_id=proj_labels[0] if proj_labels else "",
            domain=domains[0].get("label", "") if domains else "",
            title="Formalize project structure as reusable template",
            description=f"Project structure appears to repeat across {len(projects)} projects. Consider formalizing as a reusable project template.",
            rationale="Observed multiple projects with similar structure; style signals suggest consistent folder/naming patterns.",
            supporting_signals=[f"projects: {len(projects)}", f"style_signals: {len(style_signals)}"],
            style_profile_refs=[p.profile_id for p in style_profiles[:3] if hasattr(p, "profile_id")],
            confidence_score=min(0.85, 0.5 + 0.05 * len(style_signals)),
            priority=1,
            created_utc=ts,
            status="pending",
        ))
    if style_signals and any("export" in str(s.get("pattern_type", "")) or "revision" in str(s.get("pattern_type", "")) for s in style_signals):
        sug_id = stable_id("style_sug", "org", "export_standard", ts, prefix="sug")
        suggestions.append(StyleAwareSuggestion(
            suggestion_id=sug_id,
            suggestion_type="organization",
            domain="",
            title="Standardize export naming convention",
            description="Export names follow a consistent convention. Standardize future outputs to this pattern.",
            rationale="Style signals show recurring export/revision naming; formalizing reduces inconsistency.",
            supporting_signals=[str(s.get("pattern_type", "")) for s in style_signals[:5]],
            confidence_score=0.75,
            priority=2,
            created_utc=ts,
            status="pending",
        ))
    for r in routines[:max_per_category]:
        if r.get("routine_type") == "frequent_project" and r.get("project"):
            sug_id = stable_id("style_sug", "org", "pin", r.get("project", ""), prefix="sug")
            suggestions.append(StyleAwareSuggestion(
                suggestion_id=sug_id,
                suggestion_type="organization",
                project_id=r.get("project", ""),
                title=f"Pin '{r.get('project', '')}' as primary working context",
                description="This project cluster looks active; pin it as a primary working context.",
                rationale="Routine detection shows frequent activity in this project.",
                supporting_signals=r.get("supporting_signals", [])[:5],
                confidence_score=float(r.get("confidence", 0.7)),
                priority=0,
                created_utc=ts,
                status="pending",
            ))

    # ---- B. Workflow suggestions ----
    if parsed:
        families = {}
        for a in parsed:
            fam = a.get("artifact_family", "unknown")
            families[fam] = families.get(fam, 0) + 1
        if families.get("spreadsheet_table", 0) >= 2 or families.get("tabular", 0) >= 2:
            sug_id = stable_id("style_sug", "workflow", "reporting", ts, prefix="sug")
            suggestions.append(StyleAwareSuggestion(
                suggestion_id=sug_id,
                suggestion_type="workflow",
                domain="ops",
                title="Recurring reporting workflow",
                description="This appears to be a recurring reporting workflow (multiple spreadsheet/tabular artifacts).",
                rationale="Parsed artifacts show repeated spreadsheet/table usage; consistent with reporting or reconciliation cycles.",
                supporting_signals=[f"spreadsheet_table: {families.get('spreadsheet_table', 0)}", f"parsed: {len(parsed)}"],
                confidence_score=0.7,
                priority=1,
                created_utc=ts,
                status="pending",
            ))
        if families.get("text_document", 0) >= 2 and any("export" in str(s.get("pattern_type", "")) for s in style_signals):
            sug_id = stable_id("style_sug", "workflow", "creative_loop", ts, prefix="sug")
            suggestions.append(StyleAwareSuggestion(
                suggestion_id=sug_id,
                suggestion_type="workflow",
                domain="creative",
                title="Creative export–review–revision loop",
                description="Artifacts and export patterns suggest a creative export-review-revision loop.",
                rationale="Documents plus export/revision style signals indicate a recurring creative workflow.",
                supporting_signals=[f"text_document: {families.get('text_document', 0)}"] + [str(s.get("pattern_type")) for s in style_signals[:3]],
                confidence_score=0.65,
                priority=1,
                created_utc=ts,
                status="pending",
            ))

    # ---- C. Style suggestions ----
    for p in style_profiles[:max_per_category]:
        if not hasattr(p, "profile_id"):
            continue
        profile = p
        if getattr(profile, "profile_type", "") == "naming_style":
            sug_id = stable_id("style_sug", "style", "naming", profile.profile_id, prefix="sug")
            suggestions.append(StyleAwareSuggestion(
                suggestion_id=sug_id,
                suggestion_type="style",
                project_id=getattr(profile, "project_id", ""),
                domain=getattr(profile, "domain", ""),
                title="Consistent revision/naming style",
                description="You consistently use a particular revision/naming style. Future outputs can match this pattern.",
                rationale="Aggregated naming style profile from onboarding; high consistency.",
                supporting_signals=getattr(profile, "naming_patterns", [])[:5] or [str(s.get("value", "")) for s in getattr(profile, "signals", [])[:5]],
                style_profile_refs=[profile.profile_id],
                confidence_score=profile.confidence,
                priority=1,
                created_utc=ts,
                status="pending",
            ))
        if getattr(profile, "profile_type", "") == "folder_structure_style":
            sug_id = stable_id("style_sug", "style", "folder", profile.profile_id, prefix="sug")
            suggestions.append(StyleAwareSuggestion(
                suggestion_id=sug_id,
                suggestion_type="style",
                project_id=getattr(profile, "project_id", ""),
                domain=getattr(profile, "domain", ""),
                title="Recurring folder hierarchy style",
                description="Folder layout follows a recurring structure. New projects can mirror this hierarchy.",
                rationale="Folder structure style profile built from onboarding signals.",
                supporting_signals=getattr(profile, "folder_patterns", [])[:5] or [str(s.get("value", "")) for s in getattr(profile, "signals", [])[:5]],
                style_profile_refs=[profile.profile_id],
                confidence_score=profile.confidence,
                priority=1,
                created_utc=ts,
                status="pending",
            ))
        if "spreadsheet" in getattr(profile, "profile_type", ""):
            sug_id = stable_id("style_sug", "style", "spreadsheet", profile.profile_id, prefix="sug")
            suggestions.append(StyleAwareSuggestion(
                suggestion_id=sug_id,
                suggestion_type="style",
                domain=getattr(profile, "domain", "tabular"),
                title="Recurring spreadsheet schema style",
                description="Spreadsheets in this project repeatedly use similar tab/column patterns. New workbooks can follow this scaffold.",
                rationale="Spreadsheet schema style inferred from parsed artifacts and style signals.",
                supporting_signals=getattr(profile, "spreadsheet_patterns", [])[:5],
                style_profile_refs=[profile.profile_id],
                confidence_score=profile.confidence,
                priority=1,
                created_utc=ts,
                status="pending",
            ))

    # ---- D. Draft-creation suggestions ----
    if domains or parsed:
        sug_id = stable_id("style_sug", "draft", "report_outline", ts, prefix="sug")
        suggestions.append(StyleAwareSuggestion(
            suggestion_id=sug_id,
            suggestion_type="draft_creation",
            domain=domains[0].get("label", "general") if domains else "general",
            title="Reusable report outline",
            description="Suggest a reusable report outline based on observed document structure.",
            rationale="Parsed documents and domains suggest report-like workflows; a draft outline can be generated.",
            supporting_signals=[f"parsed: {len(parsed)}", f"domains: {len(domains)}"],
            confidence_score=0.7,
            priority=2,
            created_utc=ts,
            status="pending",
        ))
    if any(p.get("artifact_family") == "spreadsheet_table" for p in parsed):
        sug_id = stable_id("style_sug", "draft", "workbook_scaffold", ts, prefix="sug")
        suggestions.append(StyleAwareSuggestion(
            suggestion_id=sug_id,
            suggestion_type="draft_creation",
            domain="ops",
            title="Spreadsheet workbook scaffold",
            description="Suggest a spreadsheet workbook structure (tabs/sections) matching observed patterns.",
            rationale="Spreadsheet artifacts detected; scaffold can mirror observed schema style.",
            supporting_signals=[a.get("artifact_family", "") for a in parsed if a.get("artifact_family") == "spreadsheet_table"][:3],
            confidence_score=0.65,
            priority=2,
            created_utc=ts,
            status="pending",
        ))
    if style_signals and len(projects) >= 1:
        sug_id = stable_id("style_sug", "draft", "project_brief", ts, prefix="sug")
        suggestions.append(StyleAwareSuggestion(
            suggestion_id=sug_id,
            suggestion_type="draft_creation",
            project_id=projects[0].get("label", "") if projects else "",
            title="Project brief template",
            description="Suggest a project brief template aligned with your project and style patterns.",
            rationale="Project and style context available; template can reflect observed structure.",
            supporting_signals=[f"projects: {len(projects)}", f"style_signals: {len(style_signals)}"],
            confidence_score=0.7,
            priority=1,
            created_utc=ts,
            status="pending",
        ))

    return suggestions


def persist_style_aware_suggestions(
    suggestions: list[StyleAwareSuggestion],
    out_dir: Path | str,
) -> Path:
    """Write style-aware suggestions to out_dir/suggestions.json."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "suggestions.json"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps([s.model_dump() for s in suggestions], indent=2))
    return path


def load_style_aware_suggestions(out_dir: Path | str) -> list[StyleAwareSuggestion]:
    """Load style-aware suggestions from out_dir/suggestions.json."""
    path = Path(out_dir) / "suggestions.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [StyleAwareSuggestion.model_validate(d) for d in data]
