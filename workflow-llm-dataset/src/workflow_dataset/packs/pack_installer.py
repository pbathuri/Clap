"""
M22: Local pack install/uninstall. No arbitrary code execution; recipes are declarative only.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from workflow_dataset.packs.pack_models import PackManifest, validate_pack_manifest
from workflow_dataset.packs.pack_state import load_pack_state, save_pack_state, get_packs_dir
from workflow_dataset.packs.pack_recipes import validate_recipe_steps, apply_recipe_steps


def install_pack(
    manifest_path: Path | str,
    packs_dir: Path | str | None = None,
) -> tuple[bool, str]:
    """
    Install a pack from a manifest file. Validates manifest and recipes, copies manifest into
    packs dir, runs declarative recipe steps, updates installed state.
    Returns (success, message).
    """
    path = Path(manifest_path)
    if not path.exists():
        return False, f"Manifest not found: {path}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"Invalid JSON: {e}"
    ok, errs = validate_pack_manifest(data)
    if not ok:
        return False, "Validation failed: " + "; ".join(errs)
    steps = data.get("recipe_steps") or data.get("installer_recipes") or []
    rec_ok, rec_errs = validate_recipe_steps(steps)
    if not rec_ok:
        return False, "Recipe validation failed: " + "; ".join(rec_errs)
    manifest = PackManifest.model_validate(data)
    root = get_packs_dir(packs_dir)
    # Copy manifest into packs dir
    install_subdir = root / manifest.pack_id
    install_subdir.mkdir(parents=True, exist_ok=True)
    manifest_copy = install_subdir / "manifest.json"
    manifest_copy.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    # Apply declarative recipe steps under install_subdir
    apply_recipe_steps(steps, manifest.pack_id, manifest.version, install_subdir)
    state = load_pack_state(packs_dir)
    # Store path relative to root so resolution works from any cwd
    rel_path = f"{manifest.pack_id}/manifest.json"
    state[manifest.pack_id] = {
        "path": rel_path,
        "manifest_path": rel_path,
        "version": manifest.version,
        "installed_utc": time.time(),
    }
    save_pack_state(state, packs_dir)
    return True, f"Installed {manifest.pack_id}@{manifest.version}"


def uninstall_pack(
    pack_id: str,
    packs_dir: Path | str | None = None,
) -> tuple[bool, str]:
    """Remove pack from installed state. Does not delete files under packs dir (safe rollback)."""
    state = load_pack_state(packs_dir)
    if pack_id not in state:
        return False, f"Pack not installed: {pack_id}"
    del state[pack_id]
    save_pack_state(state, packs_dir)
    return True, f"Uninstalled {pack_id}"
