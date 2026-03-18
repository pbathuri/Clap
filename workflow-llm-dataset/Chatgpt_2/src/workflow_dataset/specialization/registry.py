"""
M23U: Built-in specialization recipe definitions by mode.
"""

from __future__ import annotations

from workflow_dataset.specialization.recipe_models import RECIPE_MODES, SpecializationRecipe

BUILTIN_RECIPES: list[SpecializationRecipe] = [
    SpecializationRecipe(
        recipe_id="local_user_data_only",
        name="Local user data only",
        description="Use only local user data for retrieval or training. No external datasets.",
        mode="local_user_data_only",
        data_sources={"local_only": True},
        licensing_compliance_metadata={"source": "local", "attribution": "N/A"},
        auto_download=False,
        auto_train=False,
        steps_summary=["Collect local corpus from data/local/llm/corpus and SFT dirs", "Use for retrieval or SFT build only"],
    ),
    SpecializationRecipe(
        recipe_id="local_user_data_plus_approved_open_datasets",
        name="Local + approved open datasets",
        description="Local user data plus operator-approved open datasets. References only; operator must add and approve.",
        mode="local_user_data_plus_approved_open_datasets",
        data_sources={"local_only": True, "approved_dataset_refs": []},
        licensing_compliance_metadata={"dataset_licenses": [], "attribution": "Operator must set per dataset"},
        auto_download=False,
        auto_train=False,
        steps_summary=["Operator adds approved_dataset_refs with license metadata", "Merge with local corpus for SFT or retrieval"],
    ),
    SpecializationRecipe(
        recipe_id="local_user_data_plus_approved_public_model",
        name="Local + approved public model class",
        description="Local data with an approved base model (e.g. from catalog). No auto-download.",
        mode="local_user_data_plus_approved_public_model",
        data_sources={"local_only": True, "approved_model_refs": []},
        licensing_compliance_metadata={"model_license": "Operator must set per model", "attribution": ""},
        auto_download=False,
        auto_train=False,
        steps_summary=["Operator selects base model from allowed list", "Adapter/SFT from local data only"],
    ),
    SpecializationRecipe(
        recipe_id="retrieval_only",
        name="Retrieval-only mode",
        description="No training; use local corpus and embeddings for retrieval-augmented generation.",
        mode="retrieval_only",
        data_sources={"local_only": True},
        licensing_compliance_metadata={"source": "local"},
        auto_download=False,
        auto_train=False,
        steps_summary=["Build/refresh embedding index from local corpus", "Use retrieval at inference"],
    ),
    SpecializationRecipe(
        recipe_id="adapter_finetune",
        name="Adapter fine-tune mode",
        description="LoRA/adapter fine-tuning on local data. Base model from approved list.",
        mode="adapter_finetune",
        data_sources={"local_only": True, "approved_model_refs": []},
        licensing_compliance_metadata={"model_license": "Set per base model", "train_data": "local only"},
        auto_download=False,
        auto_train=False,
        steps_summary=["Export SFT examples from local corpus", "Run training backend with operator-approved config"],
    ),
    SpecializationRecipe(
        recipe_id="embedding_refresh",
        name="Embedding refresh mode",
        description="Rebuild embedding index from current local corpus.",
        mode="embedding_refresh",
        data_sources={"local_only": True},
        licensing_compliance_metadata={"source": "local"},
        auto_download=False,
        auto_train=False,
        steps_summary=["Read corpus from data/local/llm/corpus", "Run embedding model; write index"],
    ),
    SpecializationRecipe(
        recipe_id="ocr_doc",
        name="OCR / document mode",
        description="OCR and document extraction; optional vision model. Output for review before apply.",
        mode="ocr_doc",
        data_sources={"local_only": True},
        licensing_compliance_metadata={"source": "local", "ocr_output_review": "required"},
        auto_download=False,
        auto_train=False,
        steps_summary=["Run OCR/vision on local documents", "Review output; optional merge into corpus"],
    ),
    SpecializationRecipe(
        recipe_id="coding_agent",
        name="Coding-agent mode",
        description="Code scaffolding and assistance; code-aware model and retrieval.",
        mode="coding_agent",
        data_sources={"local_only": True},
        licensing_compliance_metadata={"source": "local", "code_apply_confirm": "required"},
        auto_download=False,
        auto_train=False,
        steps_summary=["Use code-aware model from allowed list", "Apply only with explicit confirm"],
    ),
]


def list_recipes() -> list[str]:
    """Return list of recipe IDs."""
    return [r.recipe_id for r in BUILTIN_RECIPES]


def get_recipe(recipe_id: str) -> SpecializationRecipe | None:
    """Return recipe by id."""
    for r in BUILTIN_RECIPES:
        if r.recipe_id == recipe_id:
            return r
    return None
