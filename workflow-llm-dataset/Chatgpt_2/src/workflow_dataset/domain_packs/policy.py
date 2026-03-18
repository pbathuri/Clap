"""
M23U: Policy layer — map user field to domain pack; filter model/dataset/integration by machine and safety.
Uses external catalog as seed input; does not fetch catalogs. simulate_only | benchmark_first | trusted_real.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.domain_packs.models import DomainPack
from workflow_dataset.domain_packs.registry import get_domain_pack, recommend_domain_packs


def resolve_domain_pack_for_field(
    field: str = "",
    job_family: str = "",
    daily_task_style: str = "",
) -> DomainPack | None:
    """Resolve primary domain pack for user field/job family. Returns first recommended or None."""
    recs = recommend_domain_packs(field=field, job_family=job_family, daily_task_style=daily_task_style)
    if not recs or recs[0][1] <= 0.1:
        return None
    return recs[0][0]


def get_allowed_options_for_machine(
    repo_root: Path | str | None = None,
    tier: str = "",
    domain_pack: DomainPack | None = None,
) -> dict[str, Any]:
    """
    Return allowed model/dataset/integration options for this machine (edge tier).
    Does not fetch catalog; returns class ID lists from domain pack filtered by tier.
    Keys: allowed_model_classes, allowed_embedding_classes, allowed_ocr_vision_classes,
    allowed_integration_classes, tier, degraded (list of reasons if constrained).
    """
    root = Path(repo_root).resolve() if repo_root else None
    degraded: list[str] = []
    allowed_models: list[str] = []
    allowed_embeddings: list[str] = []
    allowed_ocr: list[str] = []
    allowed_integrations: list[str] = []

    if domain_pack:
        allowed_models = list(domain_pack.suggested_model_classes)
        allowed_embeddings = list(domain_pack.suggested_embedding_classes)
        allowed_ocr = list(domain_pack.suggested_ocr_vision_classes)
        allowed_integrations = list(domain_pack.suggested_integration_classes)

    tier_lower = (tier or "").strip().lower()
    if tier_lower == "constrained_edge":
        # Optional LLM; suggest smaller/faster models only if we had a catalog
        degraded.append("LLM optional; prefer smaller model classes")
    elif tier_lower == "minimal_eval":
        allowed_models = []
        allowed_embeddings = []
        allowed_ocr = []
        allowed_integrations = []
        degraded.append("Eval-only tier; no reporting workflows or model classes")

    return {
        "allowed_model_classes": allowed_models,
        "allowed_embedding_classes": allowed_embeddings,
        "allowed_ocr_vision_classes": allowed_ocr,
        "allowed_integration_classes": allowed_integrations,
        "tier": tier or "unknown",
        "degraded": degraded,
    }


def filter_models_by_policy(
    catalog_entries: list[dict[str, Any]],
    allowed_model_classes: list[str],
    safety_posture: str = "simulate_only",
) -> list[dict[str, Any]]:
    """
    Filter external catalog (list of dicts with e.g. name, id, size) to only allowed model classes.
    catalog_entries: seed input from caller (e.g. Ollama model list). Each entry should have
    a name or id that can be matched to allowed_model_classes (substring or exact).
    safety_posture: simulate_only | benchmark_first | trusted_real. For now only affects
    which entries are included (all allowed); future can restrict by size/risk.
    """
    if not allowed_model_classes:
        return []
    allowed_set = {c.lower() for c in allowed_model_classes}
    out: list[dict[str, Any]] = []
    for entry in catalog_entries:
        name = (entry.get("name") or entry.get("id") or entry.get("model") or "").lower()
        if not name:
            continue
        for a in allowed_set:
            if a in name or name in a:
                out.append(dict(entry))
                break
    return out


def get_safety_posture_from_profile(
    risk_safety_posture: str = "",
    preferred_automation_degree: str = "",
) -> str:
    """
    Map user profile to policy safety posture: simulate_only | benchmark_first | trusted_real.
    """
    risk = (risk_safety_posture or "").strip().lower()
    auto = (preferred_automation_degree or "").strip().lower()
    if "high_automation" in auto or "trusted" in auto:
        return "trusted_real"
    if "approval_gated" in auto or "moderate" in risk:
        return "benchmark_first"
    return "simulate_only"
