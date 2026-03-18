"""
Persist generation requests, style packs, prompt packs, asset plans, variant plans, manifests.

All under data/local/generation/ and data/local/generation_manifests/. Local-only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.generate.generate_models import (
    GenerationRequest,
    StylePack,
    PromptPack,
    AssetPlan,
    VariantPlan,
    GenerationManifest,
)


def _ensure_dir(path: Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _generation_root(workspace_root: str | Path) -> Path:
    p = Path(workspace_root)
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    return p


def save_generation_request(request: GenerationRequest, store_path: Path | str) -> Path:
    """Persist a generation request. Returns path to file."""
    root = _generation_root(store_path)
    base = root / "requests"
    _ensure_dir(base)
    path = base / f"{request.generation_id}.json"
    data = request.model_dump()
    if "status" in data and hasattr(data["status"], "value"):
        data["status"] = data["status"].value
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def save_style_pack(pack: StylePack, store_path: Path | str) -> Path:
    """Persist a style pack."""
    root = _generation_root(store_path)
    base = root / "style_packs"
    _ensure_dir(base)
    path = base / f"{pack.style_pack_id}.json"
    path.write_text(pack.model_dump_json(indent=2), encoding="utf-8")
    return path


def save_prompt_pack(pack: PromptPack, store_path: Path | str) -> Path:
    """Persist a prompt pack."""
    root = _generation_root(store_path)
    base = root / "prompt_packs"
    _ensure_dir(base)
    path = base / f"{pack.prompt_pack_id}.json"
    path.write_text(pack.model_dump_json(indent=2), encoding="utf-8")
    return path


def save_asset_plan(plan: AssetPlan, store_path: Path | str) -> Path:
    """Persist an asset plan."""
    root = _generation_root(store_path)
    base = root / "asset_plans"
    _ensure_dir(base)
    path = base / f"{plan.asset_plan_id}.json"
    path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    return path


def save_variant_plan(plan: VariantPlan, store_path: Path | str) -> Path:
    """Persist a variant plan."""
    root = _generation_root(store_path)
    base = root / "variant_plans"
    _ensure_dir(base)
    path = base / f"{plan.variant_plan_id}.json"
    path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    return path


def save_generation_manifest(manifest: GenerationManifest, store_path: Path | str) -> Path:
    """Persist a generation manifest (refs only; prompt_packs/asset_plans/style_packs not embedded)."""
    root = _generation_root(store_path)
    base = root / "manifests"
    _ensure_dir(base)
    path = base / f"{manifest.manifest_id}.json"
    data = manifest.model_dump()
    if "status" in data and hasattr(data["status"], "value"):
        data["status"] = data["status"].value
    # Exclude large embedded lists for persistence; they are refs only on disk
    for key in ("prompt_packs", "asset_plans", "style_packs"):
        if key in data and data[key]:
            data[key] = []
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_generation_manifest(manifest_id: str, store_path: Path | str) -> GenerationManifest | None:
    """Load a generation manifest by id. Packs are refs only; use load_*_for_manifest to hydrate."""
    root = _generation_root(store_path)
    path = root / "manifests" / f"{manifest_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return GenerationManifest.model_validate(data)


def load_prompt_pack(pack_id: str, store_path: Path | str) -> PromptPack | None:
    """Load a prompt pack by id."""
    root = _generation_root(store_path)
    path = root / "prompt_packs" / f"{pack_id}.json"
    if not path.exists():
        return None
    return PromptPack.model_validate_json(path.read_text(encoding="utf-8"))


def load_asset_plan(plan_id: str, store_path: Path | str) -> AssetPlan | None:
    """Load an asset plan by id."""
    root = _generation_root(store_path)
    path = root / "asset_plans" / f"{plan_id}.json"
    if not path.exists():
        return None
    return AssetPlan.model_validate_json(path.read_text(encoding="utf-8"))


def load_style_pack(pack_id: str, store_path: Path | str) -> StylePack | None:
    """Load a style pack by id."""
    root = _generation_root(store_path)
    path = root / "style_packs" / f"{pack_id}.json"
    if not path.exists():
        return None
    return StylePack.model_validate_json(path.read_text(encoding="utf-8"))


def load_packs_for_manifest(manifest: GenerationManifest, store_path: Path | str) -> None:
    """Hydrate manifest.prompt_packs, asset_plans, style_packs from store by refs. Mutates manifest."""
    root = _generation_root(store_path)
    manifest.prompt_packs = []
    for ref in manifest.prompt_pack_refs:
        p = load_prompt_pack(ref, root)
        if p:
            manifest.prompt_packs.append(p)
    manifest.asset_plans = []
    for ref in manifest.asset_plan_refs:
        a = load_asset_plan(ref, root)
        if a:
            manifest.asset_plans.append(a)
    manifest.style_packs = []
    for ref in manifest.style_pack_refs:
        s = load_style_pack(ref, root)
        if s:
            manifest.style_packs.append(s)


def list_generation_requests(
    store_path: Path | str,
    session_id: str = "",
    project_id: str = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List generation requests (id, session_id, project_id, generation_type, created_utc)."""
    root = _generation_root(store_path)
    base = root / "requests"
    if not base.exists():
        return []
    out = []
    for p in sorted(base.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if len(out) >= limit:
            break
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if session_id and data.get("session_id") != session_id:
                continue
            if project_id and data.get("project_id") != project_id:
                continue
            out.append({
                "generation_id": data.get("generation_id", p.stem),
                "session_id": data.get("session_id", ""),
                "project_id": data.get("project_id", ""),
                "generation_type": data.get("generation_type", ""),
                "created_utc": data.get("created_utc", ""),
            })
        except Exception:
            continue
    return out
