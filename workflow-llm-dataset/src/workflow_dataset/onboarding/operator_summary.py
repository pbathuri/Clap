"""
M23U: Operator-facing summary — recommended domain pack(s), model/tool classes, specialization route,
data usage, simulate-only scope, training/inference path. Local-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.domain_packs.registry import get_domain_pack, recommend_domain_packs
from workflow_dataset.domain_packs.policy import (
    get_allowed_options_for_machine,
    get_safety_posture_from_profile,
    filter_models_by_policy,
)
from workflow_dataset.specialization.recipe_builder import build_recipe_for_domain_pack, explain_recipe


def build_operator_summary(
    user_profile: Any | None = None,
    bootstrap_profile: Any | None = None,
    catalog_entries: list[dict[str, Any]] | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build operator-facing summary: recommended domain pack(s), model/tool classes,
    specialization route, what data would be used, what would remain simulate-only,
    training/inference path for this machine.
    user_profile: UserWorkProfile or dict with field, job_family, risk_safety_posture, preferred_automation_degree.
    bootstrap_profile: BootstrapProfile or dict (optional; for edge_ready, ready_for_real).
    catalog_entries: optional seed catalog (e.g. Ollama models); filtered by policy.
    """
    root = Path(repo_root).resolve() if repo_root else None
    out: dict[str, Any] = {
        "recommended_domain_packs": [],
        "recommended_model_classes": [],
        "recommended_embedding_classes": [],
        "recommended_ocr_vision_classes": [],
        "recommended_specialization_route": "",
        "data_usage": [],
        "simulate_only_scope": [],
        "training_inference_path": "",
        "safety_posture": "simulate_only",
        "catalog_filtered_models": [],
        "machine_tier": "",
    }

    field = ""
    job_family = ""
    daily_task_style = ""
    risk_posture = ""
    auto_degree = ""
    if user_profile:
        if hasattr(user_profile, "field"):
            field = getattr(user_profile, "field", "") or ""
            job_family = getattr(user_profile, "job_family", "") or ""
            daily_task_style = getattr(user_profile, "daily_task_style", "") or ""
            risk_posture = getattr(user_profile, "risk_safety_posture", "") or ""
            auto_degree = getattr(user_profile, "preferred_automation_degree", "") or ""
        elif isinstance(user_profile, dict):
            field = user_profile.get("field", "") or ""
            job_family = user_profile.get("job_family", "") or ""
            daily_task_style = user_profile.get("daily_task_style", "") or ""
            risk_posture = user_profile.get("risk_safety_posture", "") or ""
            auto_degree = user_profile.get("preferred_automation_degree", "") or ""

    out["safety_posture"] = get_safety_posture_from_profile(risk_posture, auto_degree)

    recs = recommend_domain_packs(field=field, job_family=job_family, daily_task_style=daily_task_style)
    if recs:
        out["recommended_domain_packs"] = [
            {"domain_id": p.domain_id, "name": p.name, "score": s} for p, s in recs[:5]
        ]
        primary = recs[0][0]
        out["recommended_model_classes"] = list(primary.suggested_model_classes)
        out["recommended_embedding_classes"] = list(primary.suggested_embedding_classes)
        out["recommended_ocr_vision_classes"] = list(primary.suggested_ocr_vision_classes)
        out["recommended_specialization_route"] = primary.suggested_recipe_id or "retrieval_only"
        out["data_usage"] = ["local user data only (corpus, SFT dirs)"]
        out["simulate_only_scope"] = [
            "All real apply requires explicit approval; recommended: run simulate first.",
        ]
        if primary.trust_notes:
            out["simulate_only_scope"].append(primary.trust_notes)
        out["training_inference_path"] = (
            "Retrieval-only by default. For adapter/SFT: build SFT from local data, run training backend with operator-approved config (no auto-train)."
        )

    tier = ""
    if user_profile and hasattr(user_profile, "preferred_edge_tier"):
        tier = getattr(user_profile, "preferred_edge_tier", "") or ""
    elif user_profile and isinstance(user_profile, dict):
        tier = user_profile.get("preferred_edge_tier", "") or ""

    machine_opts = get_allowed_options_for_machine(repo_root=root, tier=tier, domain_pack=recs[0][0] if recs else None)
    out["machine_tier"] = machine_opts.get("tier", "")
    if machine_opts.get("degraded"):
        out["simulate_only_scope"].extend(machine_opts["degraded"])

    if catalog_entries and out.get("recommended_model_classes"):
        out["catalog_filtered_models"] = filter_models_by_policy(
            catalog_entries,
            out["recommended_model_classes"],
            out["safety_posture"],
        )

    return out


def format_operator_summary_md(summary: dict[str, Any]) -> str:
    """Format operator summary as markdown."""
    lines = [
        "# Operator summary (M23U)",
        "",
        "## Recommended domain pack(s)",
    ]
    for p in summary.get("recommended_domain_packs", []):
        lines.append(f"- **{p.get('domain_id', '')}** — {p.get('name', '')} (score: {p.get('score', 0):.2f})")
    lines.extend([
        "",
        "## Recommended model / tool classes",
        f"- Models: {', '.join(summary.get('recommended_model_classes', []) or ['(none)'])}",
        f"- Embeddings: {', '.join(summary.get('recommended_embedding_classes', []) or ['(none)'])}",
        f"- OCR/Vision: {', '.join(summary.get('recommended_ocr_vision_classes', []) or ['(none)'])}",
        "",
        "## Specialization route",
        summary.get("recommended_specialization_route", "(none)"),
        "",
        "## Data usage",
    ])
    for d in summary.get("data_usage", []):
        lines.append(f"- {d}")
    lines.extend([
        "",
        "## Simulate-only / safety scope",
    ])
    for s in summary.get("simulate_only_scope", []):
        lines.append(f"- {s}")
    lines.extend([
        "",
        "## Training / inference path",
        summary.get("training_inference_path", "(none)"),
        "",
        "## Safety posture",
        summary.get("safety_posture", "simulate_only"),
        "",
        "## Machine tier",
        summary.get("machine_tier", "(unknown)"),
        "",
    ])
    if summary.get("catalog_filtered_models"):
        lines.append("## Catalog-filtered models (from seed catalog)")
        for m in summary["catalog_filtered_models"][:20]:
            name = m.get("name") or m.get("id") or m.get("model") or str(m)
            lines.append(f"- {name}")
        lines.append("")
    return "\n".join(lines)
