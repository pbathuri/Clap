"""
M23U: Specialization recipe builder — explicit recipes (retrieval-only, adapter fine-tune, etc.).
Recipe generation only; no auto-download or auto-training.
"""

from workflow_dataset.specialization.recipe_models import SpecializationRecipe
from workflow_dataset.specialization.registry import list_recipes, get_recipe
from workflow_dataset.specialization.recipe_builder import build_recipe_for_domain_pack, explain_recipe

__all__ = [
    "SpecializationRecipe",
    "list_recipes",
    "get_recipe",
    "build_recipe_for_domain_pack",
    "explain_recipe",
]
