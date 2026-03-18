"""
M42D.1: Vertical runtime profiles and routing policies — conservative, balanced, eval-heavy, production-safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Policy ids
ROUTING_POLICY_CONSERVATIVE = "conservative"
ROUTING_POLICY_BALANCED = "balanced"
ROUTING_POLICY_EVAL_HEAVY = "eval_heavy"
ROUTING_POLICY_PRODUCTION_SAFE = "production_safe"


@dataclass
class VerticalRuntimeProfile:
    """M42D.1: Vertical-specific runtime profile — allowed backends, task families, production-safe requirement."""
    vertical_id: str = ""
    label: str = ""
    allowed_backends: list[str] = field(default_factory=list)  # empty = all allowed
    allowed_task_families: list[str] = field(default_factory=list)  # empty = all allowed
    required_production_safe: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertical_id": self.vertical_id,
            "label": self.label,
            "allowed_backends": list(self.allowed_backends),
            "allowed_task_families": list(self.allowed_task_families),
            "required_production_safe": self.required_production_safe,
            "notes": self.notes,
        }


@dataclass
class RoutingPolicy:
    """M42D.1: Routing policy — conservative, balanced, eval-heavy, production-safe."""
    policy_id: str = ""
    label: str = ""
    allow_experimental_models: bool = False
    prefer_production_safe_only: bool = True
    allow_degraded_fallback: bool = True
    eval_task_families_priority: list[str] = field(default_factory=list)  # task families to prioritize for eval
    block_when_no_production_safe: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "label": self.label,
            "allow_experimental_models": self.allow_experimental_models,
            "prefer_production_safe_only": self.prefer_production_safe_only,
            "allow_degraded_fallback": self.allow_degraded_fallback,
            "eval_task_families_priority": list(self.eval_task_families_priority),
            "block_when_no_production_safe": self.block_when_no_production_safe,
            "notes": self.notes,
        }


# Built-in vertical runtime profiles
VERTICAL_RUNTIME_PROFILES: list[VerticalRuntimeProfile] = [
    VerticalRuntimeProfile(
        vertical_id="default",
        label="Default",
        allowed_backends=[],
        allowed_task_families=[],
        required_production_safe=True,
        notes="No vertical-specific constraints.",
    ),
    VerticalRuntimeProfile(
        vertical_id="document_workflow",
        label="Document workflow",
        allowed_backends=["ollama", "repo_local"],
        allowed_task_families=["summarization", "vertical_workflow"],
        required_production_safe=True,
        notes="Document and vision tasks; local-only backends.",
    ),
    VerticalRuntimeProfile(
        vertical_id="codebase",
        label="Codebase",
        allowed_backends=["ollama", "repo_local", "llama_cpp"],
        allowed_task_families=["suggestion", "vertical_workflow", "adaptation_comparison"],
        required_production_safe=True,
        notes="Coding and codebase tasks.",
    ),
    VerticalRuntimeProfile(
        vertical_id="council_eval",
        label="Council / evaluation",
        allowed_backends=["ollama", "repo_local"],
        allowed_task_families=["review", "evaluation", "council"],
        required_production_safe=True,
        notes="Council review and evaluation; production-safe only.",
    ),
]

# Built-in routing policies
ROUTING_POLICIES: list[RoutingPolicy] = [
    RoutingPolicy(
        policy_id=ROUTING_POLICY_CONSERVATIVE,
        label="Conservative",
        allow_experimental_models=False,
        prefer_production_safe_only=True,
        allow_degraded_fallback=False,
        eval_task_families_priority=[],
        block_when_no_production_safe=True,
        notes="Only production-safe models; no degraded fallback; block when no production-safe route.",
    ),
    RoutingPolicy(
        policy_id=ROUTING_POLICY_BALANCED,
        label="Balanced",
        allow_experimental_models=True,
        prefer_production_safe_only=True,
        allow_degraded_fallback=True,
        eval_task_families_priority=["evaluation", "council"],
        block_when_no_production_safe=False,
        notes="Prefer production-safe; allow experimental and degraded fallback when needed.",
    ),
    RoutingPolicy(
        policy_id=ROUTING_POLICY_EVAL_HEAVY,
        label="Eval-heavy",
        allow_experimental_models=True,
        prefer_production_safe_only=False,
        allow_degraded_fallback=True,
        eval_task_families_priority=["evaluation", "council", "adaptation_comparison"],
        block_when_no_production_safe=False,
        notes="Prioritize evaluation/council task families; allow experimental for eval.",
    ),
    RoutingPolicy(
        policy_id=ROUTING_POLICY_PRODUCTION_SAFE,
        label="Production-safe",
        allow_experimental_models=False,
        prefer_production_safe_only=True,
        allow_degraded_fallback=True,
        eval_task_families_priority=[],
        block_when_no_production_safe=True,
        notes="Production-safe only; allow degraded fallback to next production-safe option.",
    ),
]


def list_vertical_profiles() -> list[VerticalRuntimeProfile]:
    return list(VERTICAL_RUNTIME_PROFILES)


def get_vertical_profile(vertical_id: str) -> VerticalRuntimeProfile | None:
    for p in VERTICAL_RUNTIME_PROFILES:
        if p.vertical_id == vertical_id:
            return p
    return None


def list_routing_policies() -> list[RoutingPolicy]:
    return list(ROUTING_POLICIES)


def get_routing_policy(policy_id: str) -> RoutingPolicy | None:
    for p in ROUTING_POLICIES:
        if p.policy_id == policy_id:
            return p
    return None


def build_routing_policy_report(
    vertical_id: str = "",
    policy_id: str = "",
) -> dict[str, Any]:
    """Build a report of how the given vertical profile and routing policy affect routing."""
    vp = get_vertical_profile(vertical_id) if vertical_id else get_vertical_profile("default")
    rp = get_routing_policy(policy_id) if policy_id else get_routing_policy("balanced")
    return {
        "vertical_id": vertical_id or "default",
        "vertical_profile": vp.to_dict() if vp else None,
        "policy_id": policy_id or "balanced",
        "routing_policy": rp.to_dict() if rp else None,
        "effect_summary": _effect_summary(vp, rp),
    }


def _effect_summary(vp: VerticalRuntimeProfile | None, rp: RoutingPolicy | None) -> str:
    if not rp:
        return "No policy selected."
    parts = [f"Policy {rp.policy_id}: prefer_production_safe={rp.prefer_production_safe_only}, allow_degraded={rp.allow_degraded_fallback}, block_when_no_production_safe={rp.block_when_no_production_safe}."]
    if vp and (vp.allowed_backends or vp.allowed_task_families):
        parts.append(f"Vertical {vp.vertical_id}: allowed_backends={vp.allowed_backends or 'all'}, allowed_task_families={vp.allowed_task_families or 'all'}.")
    return " ".join(parts)
