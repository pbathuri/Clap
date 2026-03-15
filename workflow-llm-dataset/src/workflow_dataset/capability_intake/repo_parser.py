"""
M21: Parse candidate repo manifest from structured metadata. Offline-first; no live fetch by default.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.capability_intake.source_models import ExternalSourceCandidate
from workflow_dataset.capability_intake.source_intake import intake_candidate


def parse_manifest_file(path: Path | str) -> dict[str, Any]:
    """
    Load a manifest JSON file. Expected keys: name, description, (optional) url, license, etc.
    Returns raw dict; does not validate schema.
    """
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def manifest_to_candidate(raw: dict[str, Any], source_id: str = "") -> ExternalSourceCandidate:
    """
    Convert manifest dict to ExternalSourceCandidate and run intake (classify, risk, fit, recommendation).
    source_id optional; if missing, derived from name or url.
    """
    source_id = source_id or raw.get("source_id") or raw.get("id") or _slug(raw.get("name", "unknown"))
    c = ExternalSourceCandidate(
        source_id=source_id,
        name=raw.get("name", ""),
        source_type=raw.get("source_type", "repo"),
        canonical_url=raw.get("canonical_url") or raw.get("url") or raw.get("repository", ""),
        source_kind=raw.get("source_kind", "github"),
        description=raw.get("description", ""),
        license=raw.get("license", ""),
        primary_language=raw.get("primary_language", ""),
        stars_or_popularity=str(raw.get("stars", raw.get("popularity", ""))),
        last_activity=raw.get("last_activity", ""),
        maintainer_signal=raw.get("maintainer_signal", ""),
        notes=raw.get("notes", ""),
        unresolved_reason=raw.get("unresolved_reason", ""),
        product_layers=raw.get("product_layers", []) if isinstance(raw.get("product_layers"), list) else [],
    )
    return intake_candidate(c.model_dump())


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name.lower()).strip("_") or "unknown"


def parse_local_manifest(path: Path | str) -> ExternalSourceCandidate | None:
    """
    Parse a local manifest file and return an intake-ready candidate, or None if file missing/invalid.
    """
    raw = parse_manifest_file(path)
    if not raw:
        return None
    return manifest_to_candidate(raw)
