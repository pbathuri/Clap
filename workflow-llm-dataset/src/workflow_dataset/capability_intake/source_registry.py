"""
M21: Load/save source registry (JSON). Local-only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.capability_intake.source_models import ExternalSourceCandidate


def _default_registry_path() -> Path:
    return Path("data/local/capability_intake/source_registry.json")


def load_source_registry(registry_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Load registry as list of dicts. Creates dir if missing; returns [] if file missing."""
    path = Path(registry_path) if registry_path else _default_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_source_registry(
    entries: list[dict[str, Any]] | list[ExternalSourceCandidate],
    registry_path: Path | str | None = None,
) -> Path:
    """Save registry. Accepts dicts or ExternalSourceCandidate; normalizes to dict list."""
    path = Path(registry_path) if registry_path else _default_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    out: list[dict[str, Any]] = []
    for e in entries:
        if isinstance(e, ExternalSourceCandidate):
            out.append(e.model_dump())
        else:
            out.append(dict(e))
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return path


def list_sources(
    registry_path: Path | str | None = None,
    unresolved_only: bool = False,
    adoption_filter: str | None = None,
) -> list[ExternalSourceCandidate]:
    """List all sources, optionally filter by unresolved or adoption_recommendation."""
    raw = load_source_registry(registry_path)
    candidates = [ExternalSourceCandidate.model_validate(e) for e in raw]
    if unresolved_only:
        candidates = [c for c in candidates if c.unresolved_reason]
    if adoption_filter:
        candidates = [c for c in candidates if c.adoption_recommendation == adoption_filter]
    return candidates


def get_source(source_id: str, registry_path: Path | str | None = None) -> ExternalSourceCandidate | None:
    """Get single source by source_id."""
    for c in list_sources(registry_path):
        if c.source_id == source_id:
            return c
    return None
