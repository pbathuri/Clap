"""
Detect likely domains (creative, design, finance, ops, etc.) from paths and signals.

Used after parsing/adapters to aggregate discovered domains for a session.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.setup.setup_models import DiscoveredDomain


# Path/keyword hints per domain (lowercase)
CREATIVE_HINTS = {"design", "art", "figma", "sketch", "illustrat", "asset", "export", "ae", "premiere", "after effects", "video", "edit", "motion", "psd", "ai ", ".ai", ".psd", ".fig", "clip studio", "canva"}
DESIGN_HINTS = {"cad", "dwg", "revit", "architect", "layout", "ui", "ux", "prototype", "brand", "asset", "design", "figma", "sketch", "xd"}
FINANCE_HINTS = {"invoice", "ledger", "reconcil", "budget", "forecast", "tax", "quickbooks", "xero", "finance", "accounting", "expense", "report", "fy", "q1", "q2", "monthly", "quarterly"}
OPS_HINTS = {"sop", "runbook", "process", "operations", "logistics", "ship", "inventory", "order", "vendor", "template", "recurring", "weekly", "daily"}


def detect_domains_from_path(path: Path | str) -> list[DiscoveredDomain]:
    """Infer likely domains from a single path (folder/file name)."""
    p = Path(path)
    path_lower = (str(p) + " " + p.name).lower()
    out: list[DiscoveredDomain] = []
    if any(h in path_lower for h in CREATIVE_HINTS):
        out.append(DiscoveredDomain(domain_id="creative", label="Creative / media", confidence=0.6, evidence_count=1, signals=["path_keyword"]))
    if any(h in path_lower for h in DESIGN_HINTS):
        out.append(DiscoveredDomain(domain_id="design", label="Design / CAD / UI", confidence=0.6, evidence_count=1, signals=["path_keyword"]))
    if any(h in path_lower for h in FINANCE_HINTS):
        out.append(DiscoveredDomain(domain_id="finance", label="Finance / accounting", confidence=0.6, evidence_count=1, signals=["path_keyword"]))
    if any(h in path_lower for h in OPS_HINTS):
        out.append(DiscoveredDomain(domain_id="ops", label="Operations / admin", confidence=0.6, evidence_count=1, signals=["path_keyword"]))
    return out


def merge_domains(domain_lists: list[list[DiscoveredDomain]]) -> list[DiscoveredDomain]:
    """Merge multiple domain lists: same domain_id gets confidence and evidence_count summed/merged."""
    by_id: dict[str, DiscoveredDomain] = {}
    for lst in domain_lists:
        for d in lst:
            if d.domain_id in by_id:
                existing = by_id[d.domain_id]
                by_id[d.domain_id] = DiscoveredDomain(
                    domain_id=d.domain_id,
                    label=existing.label or d.label,
                    confidence=min(1.0, existing.confidence + d.confidence * 0.3),
                    evidence_count=existing.evidence_count + d.evidence_count,
                    signals=list(dict.fromkeys(existing.signals + d.signals)),
                )
            else:
                by_id[d.domain_id] = d
    return list(by_id.values())
