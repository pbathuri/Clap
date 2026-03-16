"""
Build style packs from generation context (style profiles + imitation candidates).

Converts observed user patterns into a reusable generation-facing profile.
Evidence-based only; no fabricated visual details.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

from workflow_dataset.generate.generate_models import StylePack


def build_style_pack_from_context(
    context: dict[str, Any],
    project_id: str = "",
    domain: str = "",
) -> StylePack:
    """
    Build a StylePack from generation context. Aggregates naming, layout,
    export, revision, and deliverable patterns from profiles and candidates.
    """
    profiles = context.get("style_profiles") or []
    candidates = context.get("imitation_candidates") or []
    proj_id = project_id or context.get("project_id", "")
    dom = domain or (context.get("domain_filter") or "")
    if not dom and profiles:
        dom = getattr(profiles[0], "domain", "") if profiles else ""
    if not dom and candidates:
        dom = getattr(candidates[0], "domain", "") if candidates else ""

    profile_refs = [getattr(p, "profile_id", "") for p in profiles if getattr(p, "profile_id", "")]
    candidate_refs = [getattr(c, "candidate_id", "") for c in candidates if getattr(c, "candidate_id", "")]

    naming_patterns: list[str] = []
    layout_patterns: list[str] = []
    artifact_bundle_patterns: list[str] = []
    export_patterns: list[str] = []
    revision_patterns: list[str] = []
    deliverable_shapes: list[str] = []
    provenance_refs: list[str] = []

    for p in profiles:
        naming_patterns.extend(getattr(p, "naming_patterns", None) or [])
        layout_patterns.extend(getattr(p, "folder_patterns", None) or [])
        artifact_bundle_patterns.extend(getattr(p, "artifact_bundle_patterns", None) or [])
        export_patterns.extend(getattr(p, "export_patterns", None) or [])
        provenance_refs.extend(getattr(p, "provenance_refs", None) or [])
    for c in candidates:
        ct = getattr(c, "candidate_type", "")
        if "naming" in ct or "export" in ct:
            revision_patterns.extend(getattr(c, "evidence", None) or [])
        if "deliverable" in ct or "media" in ct or "report" in ct or "spreadsheet" in ct:
            deliverable_shapes.append(ct)
        provenance_refs.extend(getattr(c, "supporting_artifacts", None) or [])

    # Dedupe and cap
    def dedupe(lst: list[str], cap: int = 30) -> list[str]:
        seen: set[str] = set()
        out = []
        for x in lst:
            if x and x not in seen and len(out) < cap:
                seen.add(x)
                out.append(x[:200])
        return out

    naming_patterns = dedupe(naming_patterns)
    layout_patterns = dedupe(layout_patterns)
    artifact_bundle_patterns = dedupe(artifact_bundle_patterns)
    export_patterns = dedupe(export_patterns)
    revision_patterns = dedupe(revision_patterns)
    deliverable_shapes = dedupe(deliverable_shapes, 20)
    provenance_refs = dedupe(provenance_refs, 25)

    # Tone/visual hints only from evidence (e.g. pattern_type labels), not fabricated
    tone_or_visual_hints: list[str] = []
    for p in profiles:
        for s in (getattr(p, "signals", None) or [])[:10]:
            if isinstance(s, dict):
                pt = s.get("pattern_type") or s.get("description", "")
                if pt and pt not in tone_or_visual_hints:
                    tone_or_visual_hints.append(str(pt)[:80])
    tone_or_visual_hints = tone_or_visual_hints[:15]

    ts = utc_now_iso()
    style_pack_id = stable_id("stylepack", proj_id, dom, ts, prefix="sp")

    return StylePack(
        style_pack_id=style_pack_id,
        project_id=proj_id,
        domain=dom,
        style_profile_refs=profile_refs[:20],
        imitation_candidate_refs=candidate_refs[:20],
        naming_patterns=naming_patterns,
        layout_patterns=layout_patterns,
        artifact_bundle_patterns=artifact_bundle_patterns,
        export_patterns=export_patterns,
        revision_patterns=revision_patterns,
        tone_or_visual_hints=tone_or_visual_hints,
        deliverable_shapes=deliverable_shapes,
        provenance_refs=provenance_refs,
        created_utc=ts,
    )
