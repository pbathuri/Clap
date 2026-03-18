"""
M23U: Specialization recipe builder — explicit recipes (retrieval-only, adapter fine-tune, etc.).
Recipe generation only; no auto-download or auto-training.
M24E: Recipe run model and storage for provisioning runs.
"""

from workflow_dataset.specialization.recipe_models import SpecializationRecipe
from workflow_dataset.specialization.registry import list_recipes, get_recipe
from workflow_dataset.specialization.recipe_builder import build_recipe_for_domain_pack, explain_recipe
from workflow_dataset.specialization.recipe_run_models import RecipeRun, RECIPE_RUN_STATUSES
from workflow_dataset.specialization.recipe_runs_storage import list_runs as list_recipe_runs, get_run as get_recipe_run, save_run, generate_run_id

__all__ = [
    "SpecializationRecipe",
    "list_recipes",
    "get_recipe",
    "build_recipe_for_domain_pack",
    "explain_recipe",
    "RecipeRun",
    "RECIPE_RUN_STATUSES",
    "list_recipe_runs",
    "get_recipe_run",
    "save_run",
    "generate_run_id",
]
