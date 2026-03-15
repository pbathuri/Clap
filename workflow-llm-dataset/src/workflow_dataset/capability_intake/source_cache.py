"""
M22: Source snapshot/cache layer for approved capability intake sources.
Stores approved source metadata; optional repo snapshot for analysis; links to intake decisions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CACHE_DIR = Path("data/local/capability_intake/source_cache")


def get_cache_dir(cache_dir: Path | str | None = None) -> Path:
    root = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def record_source_metadata(
    source_id: str,
    repo_url: str,
    commit: str = "",
    version: str = "",
    license_info: str = "",
    adoption_decision: str = "",
    cache_dir: Path | str | None = None,
) -> Path:
    """Record approved source metadata under cache dir. Returns path to metadata file."""
    root = get_cache_dir(cache_dir)
    meta = {
        "source_id": source_id,
        "repo_url": repo_url,
        "commit": commit,
        "version": version,
        "license": license_info,
        "adoption_decision": adoption_decision,
    }
    path = root / f"{source_id}_metadata.json"
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return path


def load_source_metadata(source_id: str, cache_dir: Path | str | None = None) -> dict[str, Any] | None:
    """Load recorded metadata for source_id. Returns None if not found."""
    root = get_cache_dir(cache_dir)
    path = root / f"{source_id}_metadata.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_cached_sources(cache_dir: Path | str | None = None) -> list[dict[str, Any]]:
    """List all cached source metadata."""
    root = get_cache_dir(cache_dir)
    out: list[dict[str, Any]] = []
    for p in root.glob("*_metadata.json"):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


def link_snapshot_to_source(
    source_id: str,
    snapshot_path: str,
    cache_dir: Path | str | None = None,
) -> None:
    """Record path to a local snapshot for source_id (e.g. cloned repo)."""
    root = get_cache_dir(cache_dir)
    path = root / f"{source_id}_metadata.json"
    meta: dict[str, Any] = {}
    if path.exists():
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    meta["snapshot_path"] = snapshot_path
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
