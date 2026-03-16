"""
M22: Pack manifest and recipe validation.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.packs.pack_models import validate_pack_manifest as _validate_manifest
from workflow_dataset.packs.pack_recipes import validate_recipe_steps


def validate_pack_manifest(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate manifest dict (required fields + safety policies). Returns (valid, errors)."""
    return _validate_manifest(data)


def validate_pack_manifest_and_recipes(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate manifest and its recipe_steps. Returns (valid, combined errors)."""
    ok, errs = _validate_manifest(data)
    if not ok:
        return False, errs
    steps = data.get("recipe_steps") or data.get("installer_recipes") or []
    rec_ok, rec_errs = validate_recipe_steps(steps)
    if not rec_ok:
        return False, errs + rec_errs
    return True, []
