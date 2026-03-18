"""
M25B: Pack verification — checksum, manifest integrity, version compatibility. Reject or warn on invalid/tampered.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from workflow_dataset.packs.pack_models import PackManifest, validate_pack_manifest
from workflow_dataset.packs.pack_registry import get_installed_manifest, get_installed_pack
from workflow_dataset.packs.pack_state import get_packs_dir


def _manifest_path_for_pack(pack_id: str, packs_dir: Path | str | None) -> Path | None:
    """Resolve path to installed pack manifest."""
    root = Path(packs_dir).resolve() if packs_dir else get_packs_dir(None)
    rec = get_installed_pack(pack_id, packs_dir)
    if not rec:
        return None
    rel = rec.get("path") or rec.get("manifest_path")
    if not rel:
        return None
    p = root / rel
    return p if p.exists() else None


def _compute_checksum(path: Path) -> str:
    """SHA256 hex digest of file contents."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def verify_pack(
    pack_id: str,
    packs_dir: Path | str | None = None,
    strict_signature: bool = False,
) -> tuple[bool, list[str], list[str]]:
    """
    Verify installed pack: manifest integrity, schema validation, optional checksum.
    Returns (valid, warnings, errors). valid=True only when errors is empty.
    """
    errors: list[str] = []
    warnings: list[str] = []

    path = _manifest_path_for_pack(pack_id, packs_dir)
    if not path:
        errors.append(f"Pack not installed or manifest missing: {pack_id}")
        return False, warnings, errors

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return False, warnings, errors
    except Exception as e:
        errors.append(str(e))
        return False, warnings, errors

    ok, val_errs = validate_pack_manifest(data)
    if not ok:
        errors.extend(val_errs)
        return False, warnings, errors

    manifest = PackManifest.model_validate(data)
    if manifest.pack_id != pack_id:
        errors.append(f"Manifest pack_id {manifest.pack_id} does not match {pack_id}")

    # Checksum if present in manifest
    sig = getattr(manifest, "signature_metadata", None) or {}
    if isinstance(sig, dict) and sig.get("checksum"):
        expected = sig.get("checksum", "").strip()
        if expected:
            actual = _compute_checksum(path)
            if actual != expected:
                errors.append("Checksum mismatch: manifest may be tampered or corrupted")
            if strict_signature and not sig.get("verified"):
                warnings.append("Signature metadata present but not verified (strict mode)")

    if strict_signature and sig and not sig.get("verified"):
        errors.append("Signature verification required but not verified")

    return len(errors) == 0, warnings, errors
