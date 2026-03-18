"""
M24E: Local pack provisioning runner — prepare sample assets, pack config, stage specialization inputs. No auto-download/train.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.value_packs.registry import get_value_pack
from workflow_dataset.value_packs.recommend import _missing_prerequisites
from workflow_dataset.value_packs.first_run_flow import get_sample_asset_path
from workflow_dataset.specialization.recipe_builder import build_recipe_for_domain_pack
from workflow_dataset.specialization.recipe_run_models import RecipeRun
from workflow_dataset.specialization.recipe_runs_storage import save_run, generate_run_id

PROVISIONING_ROOT = "data/local/provisioning"

# Alias recipe-style ids to value pack ids for "recipe run --id founder_ops_recipe"
RECIPE_PACK_ALIASES: dict[str, str] = {
    "founder_ops_recipe": "founder_ops_plus",
    "analyst_research_recipe": "analyst_research_plus",
    "developer_recipe": "developer_plus",
    "document_worker_recipe": "document_worker_plus",
    "operations_logistics_recipe": "operations_logistics_plus",
}


def resolve_pack_id(id_or_alias: str) -> str:
    """Return value pack id; if id_or_alias is an alias (e.g. founder_ops_recipe), return mapped pack id."""
    return RECIPE_PACK_ALIASES.get(id_or_alias, id_or_alias)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd()


def check_prerequisites(
    value_pack_id: str | None = None,
    domain_pack_id: str | None = None,
    repo_root: Path | str | None = None,
) -> tuple[list[str], Any]:
    """
    Check prerequisites for provisioning a value pack (or domain pack).
    Returns (missing_prerequisites, pack_or_none). If value_pack_id given, uses value pack and its domain; else domain_pack_id only (no value pack).
    """
    root = _repo_root(repo_root)
    missing: list[str] = []
    pack = None
    if value_pack_id:
        pack = get_value_pack(value_pack_id)
        if not pack:
            return [f"Value pack not found: {value_pack_id}"], None
        missing = _missing_prerequisites(pack, root)
        return missing, pack
    if domain_pack_id:
        from workflow_dataset.domain_packs.registry import get_domain_pack
        pack = get_domain_pack(domain_pack_id)
        if not pack:
            return [f"Domain pack not found: {domain_pack_id}"], None
        # For domain-only we don't have value pack prereq check; minimal check
        return [], pack
    return ["Neither value_pack_id nor domain_pack_id provided"], None


def run_provisioning(
    value_pack_id: str,
    repo_root: Path | str | None = None,
    dry_run: bool = False,
    strict_prerequisites: bool = True,
) -> dict[str, Any]:
    """
    Run local provisioning for a value pack: prepare sample assets, write pack manifest/config under data/local/provisioning/<pack_id>/.
    If strict_prerequisites and prerequisites missing, returns error and does not write. No auto-download or training.
    Returns: success, run_id, message, steps_done, outputs_produced, error, missing_prerequisites.
    """
    root = _repo_root(repo_root)
    pack = get_value_pack(value_pack_id)
    if not pack:
        return {
            "success": False,
            "run_id": "",
            "message": f"Value pack not found: {value_pack_id}",
            "steps_done": [],
            "outputs_produced": [],
            "error": f"Value pack not found: {value_pack_id}",
            "missing_prerequisites": [value_pack_id],
        }
    missing, _ = check_prerequisites(value_pack_id=value_pack_id, repo_root=root)
    if strict_prerequisites and missing:
        return {
            "success": False,
            "run_id": "",
            "message": "Provisioning blocked: missing prerequisites.",
            "steps_done": [],
            "outputs_produced": [],
            "error": "Missing prerequisites",
            "missing_prerequisites": missing,
        }
    recipe = build_recipe_for_domain_pack(pack.domain_pack_id, repo_root=str(root)) if pack.domain_pack_id else None
    run_id = generate_run_id("provision")
    steps_done: list[str] = []
    outputs_produced: list[str] = []
    prov_dir = root / PROVISIONING_ROOT / value_pack_id
    if not dry_run:
        prov_dir.mkdir(parents=True, exist_ok=True)
        # 1) Ensure sample assets exist (copy or stub)
        samples_dir = root / "data/local/value_packs/samples"
        samples_dir.mkdir(parents=True, exist_ok=True)
        for rel in pack.sample_asset_paths or []:
            existing = get_sample_asset_path(rel, root)
            if not existing and rel:
                stub = samples_dir / rel
                if not stub.exists():
                    stub.parent.mkdir(parents=True, exist_ok=True)
                    stub.write_text(f"# Sample asset placeholder for {value_pack_id}\n", encoding="utf-8")
                outputs_produced.append(str(stub))
            elif existing:
                outputs_produced.append(str(existing))
        steps_done.append("prepare_sample_assets")
        # 2) Write pack provisioning manifest
        manifest = {
            "value_pack_id": value_pack_id,
            "domain_pack_id": pack.domain_pack_id or "",
            "starter_kit_id": pack.starter_kit_id or "",
            "recipe_id": recipe.recipe_id if recipe else "",
            "provisioned_steps": steps_done,
            "sample_assets": list(pack.sample_asset_paths or []),
        }
        import json
        (prov_dir / "provisioning_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        steps_done.append("write_provisioning_manifest")
        outputs_produced.append(str(prov_dir / "provisioning_manifest.json"))
        # 3) Stub corpus/specialization dirs if not present (optional)
        corpus_dir = root / "data/local/llm/corpus"
        if not corpus_dir.exists():
            corpus_dir.mkdir(parents=True, exist_ok=True)
            (corpus_dir / ".gitkeep").write_text("", encoding="utf-8")
            outputs_produced.append(str(corpus_dir))
        steps_done.append("stage_specialization_dirs")
    else:
        steps_done.append("(dry-run) would prepare_sample_assets")
        steps_done.append("(dry-run) would write_provisioning_manifest")
        steps_done.append("(dry-run) would stage_specialization_dirs")

    recipe_run = RecipeRun(
        run_id=run_id,
        source_recipe_id=recipe.recipe_id if recipe else "",
        target_domain_pack_id=pack.domain_pack_id or "",
        target_value_pack_id=value_pack_id,
        target_starter_kit_id=pack.starter_kit_id or "",
        machine_assumptions={"repo_root": str(root)},
        approvals_required=list(pack.approvals_likely_needed or []),
        steps_planned=["prepare_sample_assets", "write_provisioning_manifest", "stage_specialization_dirs"],
        steps_done=steps_done,
        outputs_expected=["Sample assets", "Provisioning manifest", "Corpus dir"],
        outputs_produced=outputs_produced,
        reversible=True,
        status="completed",
        started_at="",
        finished_at="",
        dry_run=dry_run,
    )
    if not dry_run:
        save_run(recipe_run, root)

    return {
        "success": True,
        "run_id": run_id,
        "message": "Provisioning completed (dry-run)" if dry_run else "Provisioning completed.",
        "steps_done": steps_done,
        "outputs_produced": outputs_produced,
        "error": "",
        "missing_prerequisites": missing,
        "recipe_run": recipe_run,
    }
