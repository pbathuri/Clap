"""
M24G.1: Capability profiles and domain/pack compatibility — matrix between capabilities,
domain packs, value packs, starter kits, machine tiers. Worth-enabling vs not-worth-enabling logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.external_capability.schema import ExternalCapabilitySource, SOURCE_CATEGORIES
from workflow_dataset.external_capability.registry import load_external_sources
from workflow_dataset.external_capability.planner import plan_activations
from workflow_dataset.domain_packs.registry import get_domain_pack, list_domain_packs
from workflow_dataset.value_packs.registry import get_value_pack, list_value_packs
from workflow_dataset.starter_kits.registry import get_kit, list_kits

# Task class -> capability categories that are useful for that task (for compatibility)
TASK_CLASS_TO_CAPABILITY_CATEGORIES: dict[str, list[str]] = {
    "desktop_copilot": ["ollama_model", "openclaw", "optional_model_dataset", "automation"],
    "inbox": ["ollama_model", "optional_model_dataset", "automation"],
    "codebase_task": ["coding_agent", "ollama_model", "ide_editor", "optional_model_dataset"],
    "coding_agent": ["coding_agent", "ollama_model", "ide_editor", "optional_model_dataset"],
    "local_retrieval": ["embeddings", "ollama_model", "optional_model_dataset"],
    "document_workflow": ["ollama_model", "embeddings", "vision_ocr", "optional_model_dataset"],
    "vision": ["vision_ocr", "ollama_model", "optional_model_dataset"],
    "plan_run_review": ["ollama_model", "optional_model_dataset", "automation"],
    "lightweight_edge": ["ollama_model", "optional_model_dataset"],
}

# Domain pack -> capability categories that are typically useful for that vertical
DOMAIN_PACK_TO_CAPABILITY_CATEGORIES: dict[str, list[str]] = {
    "founder_ops": ["ollama_model", "optional_model_dataset", "automation", "openclaw"],
    "office_admin": ["ollama_model", "optional_model_dataset", "automation"],
    "logistics_ops": ["ollama_model", "optional_model_dataset", "automation"],
    "research_analyst": ["ollama_model", "embeddings", "optional_model_dataset", "openclaw"],
    "coding_development": ["coding_agent", "ollama_model", "ide_editor", "optional_model_dataset"],
    "document_knowledge_worker": ["ollama_model", "embeddings", "optional_model_dataset", "vision_ocr"],
    "multilingual": ["ollama_model", "optional_model_dataset", "embeddings"],
    "document_ocr_heavy": ["vision_ocr", "ollama_model", "optional_model_dataset"],
}

# Machine tiers we consider (local-first)
SUPPORTED_TIERS = ("dev_full", "local_standard", "constrained_edge", "minimal_eval")

# Value pack -> capability categories (for worth-enabling; derived from domain + task class)
VALUE_PACK_TO_CAPABILITY_CATEGORIES: dict[str, list[str]] = {
    "founder_ops_plus": ["ollama_model", "optional_model_dataset", "automation", "openclaw"],
    "analyst_research_plus": ["ollama_model", "embeddings", "optional_model_dataset", "openclaw"],
    "developer_plus": ["coding_agent", "ollama_model", "ide_editor", "optional_model_dataset"],
    "document_worker_plus": ["ollama_model", "embeddings", "vision_ocr", "optional_model_dataset"],
    "operations_logistics_plus": ["ollama_model", "optional_model_dataset", "automation"],
}

# Blocked reason codes for routing and reporting
BLOCKED_REASON_POLICY = "rejected_by_policy"
BLOCKED_REASON_LOW_VALUE = "low_value_for_this_pack"
BLOCKED_REASON_INCOMPATIBLE_TIER = "incompatible_tier"
BLOCKED_REASON_INCOMPATIBLE_DOMAIN = "incompatible_domain"
BLOCKED_REASON_NOT_WORTH_FOR_PACK = "not_worth_for_pack"


@dataclass
class CompatibilityRow:
    """One row of the compatibility matrix: a capability source and what it is compatible with."""
    source_id: str
    category: str
    compatible_domain_pack_ids: list[str] = field(default_factory=list)
    compatible_value_pack_ids: list[str] = field(default_factory=list)
    compatible_starter_kit_ids: list[str] = field(default_factory=list)
    compatible_tiers: list[str] = field(default_factory=list)
    enabled: bool = False
    activation_status: str = ""


@dataclass
class CapabilityRecommendationEntry:
    """Single entry in recommendation: source + reason + code + whether compatible with current pack."""
    source_id: str
    reason: str
    code: str = ""
    category: str = ""
    compatible_with_pack: bool = False
    estimated_resource: str = ""


@dataclass
class CapabilityRecommendationResult:
    """Result of recommend_capabilities_for_pack: worth enabling, not worth, blocked, and pack context."""
    worth_enabling: list[CapabilityRecommendationEntry] = field(default_factory=list)
    not_worth_enabling: list[CapabilityRecommendationEntry] = field(default_factory=list)
    blocked: list[CapabilityRecommendationEntry] = field(default_factory=list)
    pack_context: dict[str, Any] = field(default_factory=dict)
    compatibility_summary: list[CompatibilityRow] = field(default_factory=list)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd()


def _value_pack_to_starter_kit_ids(value_pack_id: str) -> list[str]:
    p = get_value_pack(value_pack_id)
    if not p or not p.starter_kit_id:
        return []
    return [p.starter_kit_id]


def _domain_pack_to_value_pack_ids(domain_pack_id: str) -> list[str]:
    return [vp for vp in list_value_packs() if get_value_pack(vp) and get_value_pack(vp).domain_pack_id == domain_pack_id]


def _domain_pack_to_starter_kit_ids(domain_pack_id: str) -> list[str]:
    return [k.kit_id for k in [get_kit(kid) for kid in list_kits()] if k and k.domain_pack_id == domain_pack_id]


def _source_compatible_with_domain(source: ExternalCapabilitySource, domain_pack_id: str) -> bool:
    if source.supported_domain_pack_ids and domain_pack_id not in source.supported_domain_pack_ids:
        return False
    allowed_cats = DOMAIN_PACK_TO_CAPABILITY_CATEGORIES.get(domain_pack_id, [])
    if allowed_cats and source.category not in allowed_cats:
        return False
    return True


def _source_compatible_with_task_class(source: ExternalCapabilitySource, task_class: str) -> bool:
    if source.supported_task_classes and task_class not in source.supported_task_classes:
        return False
    allowed_cats = TASK_CLASS_TO_CAPABILITY_CATEGORIES.get(task_class, [])
    if allowed_cats and source.category not in allowed_cats:
        return False
    return True


def build_compatibility_matrix(repo_root: Path | str | None = None) -> list[CompatibilityRow]:
    """
    Build compatibility matrix: for each external capability source, list compatible
    domain packs, value packs, starter kits, and tiers. Uses TASK_CLASS and DOMAIN_PACK
    mappings plus source's own supported_* when set.
    """
    root = _repo_root(repo_root)
    sources = load_external_sources(root)
    value_packs = list_value_packs()
    domain_packs = list_domain_packs()
    starter_kits = list_kits()
    rows: list[CompatibilityRow] = []

    for src in sources:
        compat_domains = [
            did for did in domain_packs
            if (not src.supported_domain_pack_ids or did in src.supported_domain_pack_ids)
            and (
                did not in DOMAIN_PACK_TO_CAPABILITY_CATEGORIES
                or src.category in DOMAIN_PACK_TO_CAPABILITY_CATEGORIES.get(did, [])
            )
        ]
        compat_value = [
            vpid for vpid in value_packs
            for vp in [get_value_pack(vpid)] if vp
            if (vp.domain_pack_id in compat_domains)
            or (
                (not src.supported_task_classes or (vp.recommended_runtime_task_class or "") in src.supported_task_classes)
                and (src.category in TASK_CLASS_TO_CAPABILITY_CATEGORIES.get(vp.recommended_runtime_task_class or "", []) or not TASK_CLASS_TO_CAPABILITY_CATEGORIES.get(vp.recommended_runtime_task_class or ""))
            )
        ]
        compat_value = list(dict.fromkeys(compat_value))
        compat_kits = [
            kid for kid in starter_kits
            for kit in [get_kit(kid)] if kit and kit.domain_pack_id
            if kit.domain_pack_id in compat_domains
        ]
        tiers = list(src.supported_tiers) if src.supported_tiers else list(SUPPORTED_TIERS)
        rows.append(CompatibilityRow(
            source_id=src.source_id,
            category=src.category,
            compatible_domain_pack_ids=compat_domains,
            compatible_value_pack_ids=compat_value,
            compatible_starter_kit_ids=compat_kits,
            compatible_tiers=tiers,
            enabled=src.enabled,
            activation_status=src.activation_status or "unknown",
        ))
    return rows


def recommend_capabilities_for_pack(
    value_pack_id: str | None = None,
    domain_pack_id: str | None = None,
    field: str | None = None,
    tier: str | None = None,
    repo_root: Path | str | None = None,
) -> CapabilityRecommendationResult:
    """
    Recommend capabilities for a pack/domain/field: worth_enabling, not_worth_enabling, blocked.
    Uses plan_activations then enriches with compatibility and tier: if source is not compatible
    with this pack -> not_worth_enabling; if rejected by policy or incompatible tier -> blocked with code.
    """
    root = _repo_root(repo_root)
    task_class: str = ""
    resolved_domain_pack_id: str = ""
    resolved_value_pack_id: str = ""
    effective_tier = (tier or "").strip() or "local_standard"

    if value_pack_id:
        vp = get_value_pack(value_pack_id)
        if vp:
            task_class = vp.recommended_runtime_task_class or ""
            resolved_domain_pack_id = vp.domain_pack_id or ""
            resolved_value_pack_id = value_pack_id
    if domain_pack_id and not resolved_domain_pack_id:
        resolved_domain_pack_id = domain_pack_id
        # Infer task class from first value pack for this domain
        for vpid in _domain_pack_to_value_pack_ids(domain_pack_id):
            vp = get_value_pack(vpid)
            if vp:
                task_class = vp.recommended_runtime_task_class or ""
                resolved_value_pack_id = vpid
                break
    if field and not resolved_domain_pack_id:
        from workflow_dataset.domain_packs.registry import recommend_domain_packs
        recs = recommend_domain_packs(field=field)
        if recs:
            resolved_domain_pack_id = recs[0][0].domain_id
            task_class = get_value_pack(resolved_value_pack_id).recommended_runtime_task_class if resolved_value_pack_id and get_value_pack(resolved_value_pack_id) else ""
            if not resolved_value_pack_id and recs:
                vpids = _domain_pack_to_value_pack_ids(resolved_domain_pack_id)
                if vpids:
                    resolved_value_pack_id = vpids[0]

    plan = plan_activations(
        repo_root=root,
        domain_pack_id=resolved_domain_pack_id or None,
        task_class=task_class or None,
    )
    sources = load_external_sources(root)
    source_by_id = {s.source_id: s for s in sources}
    matrix = build_compatibility_matrix(root)
    source_to_row = {r.source_id: r for r in matrix}

    worth: list[CapabilityRecommendationEntry] = []
    not_worth: list[CapabilityRecommendationEntry] = []
    blocked: list[CapabilityRecommendationEntry] = []

    def compatible_with_pack(sid: str) -> bool:
        row = source_to_row.get(sid)
        if not row:
            return False
        if resolved_value_pack_id and resolved_value_pack_id in row.compatible_value_pack_ids:
            return True
        if resolved_domain_pack_id and resolved_domain_pack_id in row.compatible_domain_pack_ids:
            return True
        return False

    def compatible_with_tier(sid: str) -> bool:
        src = source_by_id.get(sid)
        if not src or not src.supported_tiers:
            return True
        return effective_tier in src.supported_tiers

    for r in plan.recommended:
        row = source_to_row.get(r.source_id)
        src = source_by_id.get(r.source_id)
        if not compatible_with_tier(r.source_id):
            blocked.append(CapabilityRecommendationEntry(
                source_id=r.source_id,
                reason=f"Tier {effective_tier} not in source supported_tiers",
                code=BLOCKED_REASON_INCOMPATIBLE_TIER,
                category=row.category if row else "",
                compatible_with_pack=compatible_with_pack(r.source_id),
                estimated_resource=r.estimated_resource or "medium",
            ))
            continue
        compat = compatible_with_pack(r.source_id)
        entry = CapabilityRecommendationEntry(
            source_id=r.source_id,
            reason=r.reason,
            code="recommended",
            category=row.category if row else "",
            compatible_with_pack=compat,
            estimated_resource=r.estimated_resource or "medium",
        )
        if compat or not (resolved_value_pack_id or resolved_domain_pack_id):
            worth.append(entry)
        else:
            entry.reason = "low_value_for_this_pack"
            entry.code = BLOCKED_REASON_NOT_WORTH_FOR_PACK
            not_worth.append(entry)

    for b in plan.not_worth_it:
        rb = source_to_row.get(b.source_id)
        not_worth.append(CapabilityRecommendationEntry(
            source_id=b.source_id,
            reason=b.reason,
            code=b.code or BLOCKED_REASON_NOT_WORTH_FOR_PACK,
            category=rb.category if rb else "",
            compatible_with_pack=compatible_with_pack(b.source_id),
            estimated_resource="",
        ))

    for b in plan.rejected_by_policy:
        rbb = source_to_row.get(b.source_id)
        blocked.append(CapabilityRecommendationEntry(
            source_id=b.source_id,
            reason=b.reason,
            code=b.code or BLOCKED_REASON_POLICY,
            category=rbb.category if rbb else "",
            compatible_with_pack=False,
            estimated_resource="",
        ))

    return CapabilityRecommendationResult(
        worth_enabling=worth,
        not_worth_enabling=not_worth,
        blocked=blocked,
        pack_context={
            "value_pack_id": resolved_value_pack_id,
            "domain_pack_id": resolved_domain_pack_id,
            "task_class": task_class,
            "field": field,
            "tier": effective_tier,
        },
        compatibility_summary=matrix,
    )
