"""
M50L.1: Roadmap carry-forward pack — work intentionally left beyond v1 (experimental, deferred, roadmap).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from workflow_dataset.stable_v1_gate.models import RoadmapCarryForwardPack, RoadmapCarryForwardItem

if TYPE_CHECKING:
    from workflow_dataset.stable_v1_gate.models import StableV1Report


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_roadmap_carry_forward_pack(
    report: StableV1Report | None = None,
    repo_root: Path | str | None = None,
) -> RoadmapCarryForwardPack:
    """
    Build roadmap carry-forward pack: items intentionally left beyond v1 (experimental, deferred, roadmap).
    Sources: production cut quarantined/excluded, gate warnings as deferred, release known limitations, static roadmap.
    """
    now = datetime.now(timezone.utc)
    at_iso = now.isoformat()[:19] + "Z"
    items: list[RoadmapCarryForwardItem] = []

    if report is None:
        from workflow_dataset.stable_v1_gate.report import build_stable_v1_report
        root = _root(repo_root)
        report = build_stable_v1_report(root)

    gate = report.gate
    root = _root(repo_root)

    # Gate warnings -> deferred items
    for i, w in enumerate(gate.warnings):
        items.append(RoadmapCarryForwardItem(
            item_id=f"gate_warning_{w.id}",
            label=w.summary[:80],
            category="deferred",
            rationale="Gate warning at stable-v1; revisit after v1 watch period.",
            when_to_revisit="Next stability review or when evidence strengthens.",
            source=w.source or "stable_v1_gate",
        ))

    # Production cut: quarantined -> experimental, excluded -> deferred
    try:
        from workflow_dataset.production_cut import get_active_cut
        cut = get_active_cut(root)
        if cut:
            for sid in getattr(cut, "quarantined_surface_ids", [])[:20]:
                items.append(RoadmapCarryForwardItem(
                    item_id=f"experimental_{sid}",
                    label=f"Surface {sid} (experimental)",
                    category="experimental",
                    rationale="Quarantined in production cut; not production-default.",
                    when_to_revisit="When ready to promote to optional or core.",
                    source="production_cut",
                ))
            for sid in getattr(cut, "excluded_surface_ids", [])[:15]:
                items.append(RoadmapCarryForwardItem(
                    item_id=f"excluded_{sid}",
                    label=f"Surface {sid} (excluded)",
                    category="deferred",
                    rationale="Excluded from production cut; out of v1 scope.",
                    when_to_revisit="When scope is expanded or policy changes.",
                    source="production_cut",
                ))
    except Exception:
        pass

    # Release readiness known limitations -> deferred
    try:
        from workflow_dataset.release_readiness.readiness import build_release_readiness
        rr = build_release_readiness(root)
        lims = getattr(rr, "known_limitations", []) or []
        for i, lim in enumerate(lims[:10]):
            lid = getattr(lim, "id", f"limitation_{i}")
            summary = getattr(lim, "summary", str(lim))[:100]
            items.append(RoadmapCarryForwardItem(
                item_id=f"limitation_{lid}",
                label=summary,
                category="deferred",
                rationale="Known limitation at first-user release; intentionally left beyond v1.",
                when_to_revisit="Roadmap or when addressing scope expansion.",
                source="release_readiness",
            ))
    except Exception:
        pass

    # Static roadmap items (first-draft: manual approval, local-first)
    items.append(RoadmapCarryForwardItem(
        item_id="roadmap_manual_approval",
        label="Unattended real execution / full automation",
        category="roadmap",
        rationale="Approval and trust gates require operator action in v1.",
        when_to_revisit="When trust and approval policy supports unattended flows.",
        source="roadmap",
    ))
    items.append(RoadmapCarryForwardItem(
        item_id="roadmap_cloud_sync",
        label="Cloud sync / ticketing integration",
        category="roadmap",
        rationale="All state is local-first in v1; no built-in cloud sync.",
        when_to_revisit="When cloud or ticketing is in scope.",
        source="roadmap",
    ))

    experimental_count = sum(1 for i in items if i.category == "experimental")
    deferred_count = sum(1 for i in items if i.category == "deferred")
    roadmap_count = sum(1 for i in items if i.category == "roadmap")
    summary = f"{experimental_count} experimental, {deferred_count} deferred, {roadmap_count} roadmap item(s) carried forward beyond v1."

    return RoadmapCarryForwardPack(
        pack_id="roadmap_carry_forward_pack",
        generated_at_iso=at_iso,
        items=items,
        experimental_count=experimental_count,
        deferred_count=deferred_count,
        summary=summary,
    )
