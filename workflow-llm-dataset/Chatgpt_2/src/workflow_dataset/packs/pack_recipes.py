"""
M22: Safe declarative recipe steps. No arbitrary script execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ALLOWED_RECIPE_STEP_TYPES = (
    "create_config",
    "register_templates",
    "register_prompts",
    "declare_model_recommendation",
    "add_local_reference",
    "enable_optional_wrapper_metadata",
)


def validate_recipe_steps(steps: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    """
    Validate recipe steps. Only declarative step types are allowed.
    Reject run_shell, execute_script, or any unknown type.
    """
    errors: list[str] = []
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"step {i}: must be a dict")
            continue
        step_type = step.get("type") or step.get("step_type")
        if not step_type:
            errors.append(f"step {i}: missing type")
            continue
        if step_type not in ALLOWED_RECIPE_STEP_TYPES:
            errors.append(f"step {i}: disallowed type '{step_type}'; allowed: {ALLOWED_RECIPE_STEP_TYPES}")
    return len(errors) == 0, errors


def apply_recipe_steps(
    steps: list[dict[str, Any]],
    pack_id: str,
    pack_version: str,
    target_dir: Path | str,
) -> list[str]:
    """
    Apply declarative recipe steps. Creates config files, registers metadata under target_dir.
    Returns list of created/updated paths. Does NOT execute scripts.
    """
    applied: list[str] = []
    valid, errs = validate_recipe_steps(steps)
    if not valid:
        return applied
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    for step in steps:
        step_type = step.get("type") or step.get("step_type")
        if step_type == "create_config":
            name = step.get("name") or "config"
            content = step.get("content") or step.get("config", "{}")
            path = target_dir / f"{name}.json"
            if isinstance(content, dict):
                path.write_text(json.dumps(content, indent=2), encoding="utf-8")
            else:
                path.write_text(str(content), encoding="utf-8")
            applied.append(str(path))
        elif step_type == "register_templates":
            # Write a stub so we know templates were registered
            path = target_dir / "templates_registered.txt"
            path.write_text(f"pack_id={pack_id}\nversion={pack_version}\n", encoding="utf-8")
            if str(path) not in applied:
                applied.append(str(path))
        elif step_type == "register_prompts":
            path = target_dir / "prompts_registered.txt"
            path.write_text(f"pack_id={pack_id}\nversion={pack_version}\n", encoding="utf-8")
            if str(path) not in applied:
                applied.append(str(path))
    return applied
