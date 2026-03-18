"""
M25I–M25L: Extended pack validation for authoring — manifest shape, behavior fields,
role/task compatibility, required assets, runtime requirements, conflict risk, missing docs/tests, safety.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.packs.pack_models import PackManifest, validate_pack_manifest
from workflow_dataset.packs.pack_validator import validate_pack_manifest_and_recipes


def _packs_dir(repo_root: Path | str | None, packs_dir: Path | str | None) -> Path:
    if packs_dir:
        return Path(packs_dir).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        root = Path(get_repo_root()).resolve()
    except Exception:
        root = Path.cwd().resolve()
    return root / "data/local/packs"


def _manifest_path_for_pack(pack_id: str, packs_dir: Path) -> Path:
    return packs_dir / pack_id / "manifest.json"


def validate_pack_structure(
    pack_id: str | None = None,
    manifest_path: Path | str | None = None,
    packs_dir: Path | str | None = None,
    repo_root: Path | str | None = None,
    strict: bool = False,
) -> tuple[bool, list[str], list[str]]:
    """
    Validate pack: manifest schema + recipes, then structure (required assets, docs/tests presence).
    If strict=True, missing docs/README or tests/ placeholders become errors.
    Returns (valid, errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []
    root = _packs_dir(repo_root, packs_dir)
    path: Path | None = None
    if manifest_path:
        path = Path(manifest_path).resolve()
    elif pack_id:
        path = _manifest_path_for_pack(pack_id, root)
    if not path or not path.exists():
        errors.append("Manifest not found")
        return False, errors, warnings
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"Invalid JSON: {e}")
        return False, errors, warnings
    ok, errs = validate_pack_manifest_and_recipes(data)
    if not ok:
        return False, errs, warnings
    pack_dir = path.parent
    # Required assets / placeholders
    if not (pack_dir / "prompts").exists():
        warnings.append("prompts/ directory missing")
    if not (pack_dir / "docs").exists():
        if strict:
            errors.append("docs/ directory missing (strict)")
        else:
            warnings.append("docs/ directory missing")
    if not (pack_dir / "docs" / "README.md").exists() and (pack_dir / "docs").exists():
        if strict:
            errors.append("docs/README.md missing (strict)")
        else:
            warnings.append("docs/README.md missing")
    has_any_test = (pack_dir / "tests").exists() and any(
        (pack_dir / "tests").iterdir()
    )
    if not has_any_test:
        if strict:
            errors.append("tests/ empty or missing (strict)")
        else:
            warnings.append("tests/ empty or missing")
    # Behavior fields: role_tags or workflow_tags recommended
    if not data.get("role_tags") and not data.get("workflow_tags"):
        warnings.append("role_tags or workflow_tags recommended for resolution")
    # Safety / trust metadata presence
    sp = data.get("safety_policies") or {}
    if not sp:
        warnings.append("safety_policies should be explicit")
    if not data.get("safety_constraints") and not sp:
        warnings.append("safety_constraints or safety_policies recommended for trust/readiness")
    # Behavior shape: optional check
    behavior = data.get("behavior") or {}
    if isinstance(behavior, dict) and (behavior.get("prompt_assets") or behavior.get("task_defaults")):
        if not isinstance(behavior.get("prompt_assets"), list):
            warnings.append("behavior.prompt_assets should be a list when present")
        if not isinstance(behavior.get("task_defaults"), list):
            warnings.append("behavior.task_defaults should be a list when present")
    return len(errors) == 0, errors, warnings


def conflict_risk_indicators(
    pack_id: str,
    packs_dir: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> list[str]:
    """Return list of conflict risk indicators (e.g. optional_wrappers, many templates). Does not load other packs."""
    root = _packs_dir(repo_root, packs_dir)
    path = _manifest_path_for_pack(pack_id, root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    risks = []
    if data.get("optional_wrappers"):
        risks.append("optional_wrappers may conflict with strict local-only packs")
    if len(data.get("templates") or []) + len(data.get("workflow_templates") or []) > 10:
        risks.append("many templates may overlap with other packs")
    return risks


def validate_pack_full(
    pack_id: str | None = None,
    manifest_path: Path | str | None = None,
    packs_dir: Path | str | None = None,
    repo_root: Path | str | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    """Full validation result: valid, errors, warnings, conflict_risks."""
    ok, errs, warns = validate_pack_structure(
        pack_id=pack_id, manifest_path=manifest_path, packs_dir=packs_dir, repo_root=repo_root, strict=strict
    )
    pid = pack_id
    if not pid and manifest_path:
        pid = Path(manifest_path).parent.name
    risks = conflict_risk_indicators(pid or "", packs_dir=packs_dir, repo_root=repo_root) if pid else []
    return {
        "valid": ok,
        "errors": errs,
        "warnings": warns,
        "conflict_risk_indicators": risks,
        "pack_id": pid,
    }
