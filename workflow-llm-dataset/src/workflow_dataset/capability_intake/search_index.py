"""
M21: Local search index for source summaries. Offline; stores candidate summaries for role/fit/recommendation search.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.capability_intake.source_models import ExternalSourceCandidate
from workflow_dataset.capability_intake.source_registry import load_source_registry, list_sources
from workflow_dataset.capability_intake.manifest_builder import candidate_to_manifest


def _index_path(base_path: Path | str | None = None) -> Path:
    base = Path(base_path) if base_path else Path("data/local/capability_intake")
    return base / "search_index.json"


def build_search_index(registry_path: Path | str | None = None, index_path: Path | str | None = None) -> Path:
    """
    Build a local index of source summaries (manifest-like) for search/listing.
    Does not fetch from network; uses registry only.
    """
    sources = list_sources(registry_path)
    index: list[dict[str, Any]] = [candidate_to_manifest(c) for c in sources]
    path = _index_path(Path(index_path).parent if index_path else None)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return path


def load_search_index(index_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Load search index; return list of manifest-like dicts. Empty if missing."""
    path = Path(index_path) if index_path else _index_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def search_by_role(role: str, index_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Return index entries whose recommended_role matches (local index only)."""
    index = load_search_index(index_path)
    return [e for e in index if e.get("recommended_role") == role]


def search_by_adoption(adoption: str, index_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Return index entries whose adoption_recommendation matches."""
    index = load_search_index(index_path)
    return [e for e in index if e.get("adoption_recommendation") == adoption]
