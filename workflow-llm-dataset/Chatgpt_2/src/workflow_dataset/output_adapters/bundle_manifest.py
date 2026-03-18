"""
M13: Persist and load output bundle manifests.

Sandbox-first; local-only.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.output_adapters.adapter_models import OutputBundleManifest


def _bundle_root(store_path: Path | str) -> Path:
    p = Path(store_path)
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    return p


def save_bundle_manifest(manifest: OutputBundleManifest, store_path: Path | str) -> Path:
    """Persist bundle manifest. Returns path to file."""
    root = _bundle_root(store_path)
    base = root / "manifests"
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{manifest.manifest_id}.json"
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_bundle_manifest(manifest_id: str, store_path: Path | str) -> OutputBundleManifest | None:
    """Load bundle manifest by id."""
    root = _bundle_root(store_path)
    path = root / "manifests" / f"{manifest_id}.json"
    if not path.exists():
        return None
    return OutputBundleManifest.model_validate_json(path.read_text(encoding="utf-8"))


def load_manifest_for_bundle(bundle_id: str, store_path: Path | str) -> OutputBundleManifest | None:
    """Load manifest by bundle_id (scan manifests for matching bundle_id)."""
    root = _bundle_root(store_path)
    base = root / "manifests"
    if not base.exists():
        return None
    for p in base.glob("*.json"):
        try:
            m = OutputBundleManifest.model_validate_json(p.read_text(encoding="utf-8"))
            if m.bundle_id == bundle_id:
                return m
        except Exception:
            continue
    return None


def list_bundles(store_path: Path | str, limit: int = 50) -> list[dict]:
    """List known bundles (from manifests). Returns list of {bundle_id, adapter_used, created_utc}."""
    root = _bundle_root(store_path)
    base = root / "manifests"
    if not base.exists():
        return []
    out = []
    for p in sorted(base.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if len(out) >= limit:
            break
        try:
            m = OutputBundleManifest.model_validate_json(p.read_text(encoding="utf-8"))
            out.append({
                "bundle_id": m.bundle_id,
                "manifest_id": m.manifest_id,
                "adapter_used": m.adapter_used,
                "created_utc": m.created_utc,
                "populated_paths": getattr(m, "populated_paths", []) or [],
                "scaffold_only_paths": getattr(m, "scaffold_only_paths", []) or [],
                "fallback_used": getattr(m, "fallback_used", False),
                "xlsx_created": getattr(m, "xlsx_created", False),
            })
        except Exception:
            continue
    return out
