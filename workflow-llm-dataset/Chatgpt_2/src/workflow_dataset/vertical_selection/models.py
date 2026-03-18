"""
M39A–M39D: Vertical candidate and scope model — evidence-based vertical selection, core/advanced/non-core surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Surface classification for scope lock (per vertical)
SURFACE_CLASS_CORE = "core"
SURFACE_CLASS_ADVANCED_AVAILABLE = "advanced_available"
SURFACE_CLASS_NON_CORE = "non_core"

# M39D.1: Surface policy levels — recommended / allowed / discouraged / blocked
SURFACE_POLICY_RECOMMENDED = "recommended"
SURFACE_POLICY_ALLOWED = "allowed"
SURFACE_POLICY_DISCOURAGED = "discouraged"
SURFACE_POLICY_BLOCKED = "blocked"

# Advanced surface reveal rules
REVEAL_ALWAYS = "always"
REVEAL_AFTER_FIRST_MILESTONE = "after_first_milestone"
REVEAL_ON_DEMAND = "on_demand"
REVEAL_NEVER = "never"


@dataclass
class SurfacePolicyEntry:
    """M39D.1: Per-vertical surface policy: level, experimental flag, reveal rule."""
    surface_id: str = ""
    policy_level: str = SURFACE_POLICY_ALLOWED
    is_experimental: bool = False
    reveal_rule: str = REVEAL_ALWAYS
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "policy_level": self.policy_level,
            "is_experimental": self.is_experimental,
            "reveal_rule": self.reveal_rule,
            "label": self.label,
        }


@dataclass
class VerticalCandidate:
    """Evidence-based vertical candidate: scores, core workflows, required/optional/excluded surfaces."""
    vertical_id: str = ""
    label: str = ""
    description: str = ""
    # Evidence and readiness (0–1 or 0–100; higher = better for evidence/readiness, lower = better for burden/risk)
    evidence_score: float = 0.0
    readiness_score: float = 0.0
    support_burden_score: float = 0.0  # higher = more burden (open issues, etc.)
    trust_risk_score: float = 0.0
    # Workflows and surfaces
    core_workflow_ids: list[str] = field(default_factory=list)
    required_surface_ids: list[str] = field(default_factory=list)
    optional_surface_ids: list[str] = field(default_factory=list)
    excluded_surface_ids: list[str] = field(default_factory=list)
    # Optional: link to curated pack
    curated_pack_id: str = ""
    # Explanation
    strength_reason: str = ""
    weakness_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertical_id": self.vertical_id,
            "label": self.label,
            "description": self.description,
            "evidence_score": self.evidence_score,
            "readiness_score": self.readiness_score,
            "support_burden_score": self.support_burden_score,
            "trust_risk_score": self.trust_risk_score,
            "core_workflow_ids": list(self.core_workflow_ids),
            "required_surface_ids": list(self.required_surface_ids),
            "optional_surface_ids": list(self.optional_surface_ids),
            "excluded_surface_ids": list(self.excluded_surface_ids),
            "curated_pack_id": self.curated_pack_id,
            "strength_reason": self.strength_reason,
            "weakness_reason": self.weakness_reason,
        }
