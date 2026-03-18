"""
M23U: Build and explain specialization recipes for a domain pack. Generation only; no auto-download or training.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.domain_packs.registry import get_domain_pack
from workflow_dataset.specialization.registry import get_recipe
from workflow_dataset.specialization.recipe_models import SpecializationRecipe


def build_recipe_for_domain_pack(
    domain_pack_id: str,
    repo_root: str | None = None,
) -> SpecializationRecipe | None:
    """
    Build specialization recipe for a domain pack. Returns the recipe suggested by the pack
    (same as get_recipe(pack.suggested_recipe_id)) or None if pack/recipe missing.
    No side effects; no download or training.
    """
    pack = get_domain_pack(domain_pack_id)
    if not pack or not pack.suggested_recipe_id:
        return None
    return get_recipe(pack.suggested_recipe_id)


def explain_recipe(recipe_id: str) -> dict[str, Any]:
    """
    Return human-readable explanation of a recipe: id, name, mode, data sources, licensing, steps, no auto_download/train.
    """
    recipe = get_recipe(recipe_id)
    if not recipe:
        return {
            "recipe_id": recipe_id,
            "found": False,
            "message": "Recipe not found.",
        }
    return {
        "recipe_id": recipe.recipe_id,
        "found": True,
        "name": recipe.name,
        "description": recipe.description,
        "mode": recipe.mode,
        "data_sources": recipe.data_sources,
        "licensing_compliance_metadata": recipe.licensing_compliance_metadata,
        "auto_download": recipe.auto_download,
        "auto_train": recipe.auto_train,
        "steps_summary": recipe.steps_summary,
    }
