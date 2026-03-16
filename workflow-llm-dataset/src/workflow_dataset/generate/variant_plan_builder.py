"""
Build variant plans for report, dashboard, workbook, presentation variants.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

from workflow_dataset.generate.generate_models import VariantPlan, DesignVariant, StylePack


def build_variant_plan(
    generation_id: str,
    context: dict[str, Any],
    variant_type: str = "report",
    style_pack: StylePack | None = None,
) -> VariantPlan:
    """
    Build a VariantPlan for document/report/dashboard/workbook/presentation variants.
    """
    ts = utc_now_iso()
    plan_id = stable_id("varplan", generation_id, variant_type, ts, prefix="vp")

    summary = context.get("summary") or {}
    drafts = context.get("drafts") or []
    domain = context.get("domain_filter") or (style_pack.domain if style_pack else "")

    variants: list[DesignVariant] = []
    narrative_outline: list[str] = []

    if variant_type == "report":
        narrative_outline = ["Summary", "Detail", "Appendix", "References"]
        for d in drafts[:5]:
            dtype = getattr(d, "draft_type", "")
            sections = getattr(d, "recommended_sections", None) or []
            variants.append(DesignVariant(
                variant_id=stable_id("var", plan_id, dtype, prefix="var"),
                name=dtype or "report_variant",
                description="Report variant from draft structure",
                output_family="report",
                constraints=[f"Sections: {', '.join(sections[:5])}" if sections else ""],
            ))
    elif variant_type == "dashboard":
        narrative_outline = ["Overview", "Metrics", "Drill-down", "Filters"]
        variants.append(DesignVariant(
            variant_id=stable_id("var", plan_id, "dashboard", prefix="var"),
            name="dashboard",
            description="Dashboard layout variant",
            output_family="dashboard",
            constraints=[],
        ))
    elif variant_type == "workbook":
        narrative_outline = ["Summary sheet", "Detail sheets", "Variance", "Appendix"]
        variants.append(DesignVariant(
            variant_id=stable_id("var", plan_id, "workbook", prefix="var"),
            name="workbook",
            description="Workbook structure variant",
            output_family="workbook",
            constraints=[],
        ))
    elif variant_type == "presentation":
        narrative_outline = ["Title", "Context", "Main points", "Details", "Conclusion", "Next steps"]
        variants.append(DesignVariant(
            variant_id=stable_id("var", plan_id, "presentation", prefix="var"),
            name="presentation",
            description="Presentation narrative variant",
            output_family="presentation",
            constraints=[],
        ))
    else:
        narrative_outline = ["Section 1", "Section 2", "Section 3"]
        variants.append(DesignVariant(
            variant_id=stable_id("var", plan_id, variant_type, prefix="var"),
            name=variant_type,
            description=f"{variant_type} variant",
            output_family=variant_type,
            constraints=[],
        ))

    if style_pack and style_pack.revision_patterns:
        narrative_outline.extend(style_pack.revision_patterns[:3])

    return VariantPlan(
        variant_plan_id=plan_id,
        generation_id=generation_id,
        variant_type=variant_type,
        variants=variants[:15],
        narrative_outline=dedupe(narrative_outline, 20),
        created_utc=ts,
    )


def dedupe(lst: list[str], cap: int = 50) -> list[str]:
    seen: set[str] = set()
    out = []
    for x in lst:
        if x and x not in seen and len(out) < cap:
            seen.add(x)
            out.append(x[:200])
    return out
