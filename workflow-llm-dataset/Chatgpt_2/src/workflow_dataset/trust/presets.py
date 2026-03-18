"""
M35D.1: Trust presets — cautious, supervised operator, bounded trusted routine, release-safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow_dataset.trust.tiers import AuthorityTierId, get_tier, list_tiers


@dataclass
class TrustPreset:
    """Trust preset: named posture with max authority cap and policy hints."""
    preset_id: str = ""
    name: str = ""
    description: str = ""
    max_authority_tier_id: str = ""   # cap: no contract may exceed this tier unless eligibility matrix allows
    require_approval_for_real: bool = True
    allow_commit_send: bool = False
    allow_bounded_trusted_real: bool = False
    valid_scope_hint: str = ""        # e.g. "global only" or "project/pack scoped"
    order: int = 0                   # lower = more restrictive

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "name": self.name,
            "description": self.description,
            "max_authority_tier_id": self.max_authority_tier_id,
            "require_approval_for_real": self.require_approval_for_real,
            "allow_commit_send": self.allow_commit_send,
            "allow_bounded_trusted_real": self.allow_bounded_trusted_real,
            "valid_scope_hint": self.valid_scope_hint,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TrustPreset":
        return cls(
            preset_id=d.get("preset_id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            max_authority_tier_id=d.get("max_authority_tier_id", ""),
            require_approval_for_real=bool(d.get("require_approval_for_real", True)),
            allow_commit_send=bool(d.get("allow_commit_send", False)),
            allow_bounded_trusted_real=bool(d.get("allow_bounded_trusted_real", False)),
            valid_scope_hint=d.get("valid_scope_hint", ""),
            order=int(d.get("order", 0)),
        )


BUILTIN_PRESETS: list[TrustPreset] = [
    TrustPreset(
        preset_id="cautious",
        name="Cautious",
        description="Observe and suggest only; no execution or writes. Safest posture.",
        max_authority_tier_id=AuthorityTierId.SUGGEST_ONLY.value,
        require_approval_for_real=True,
        allow_commit_send=False,
        allow_bounded_trusted_real=False,
        valid_scope_hint="global only",
        order=0,
    ),
    TrustPreset(
        preset_id="supervised_operator",
        name="Supervised operator",
        description="Human-in-the-loop; queued execution and sandbox/simulate. No direct real run without approval.",
        max_authority_tier_id="queued_execute",
        require_approval_for_real=True,
        allow_commit_send=False,
        allow_bounded_trusted_real=False,
        valid_scope_hint="project/pack scoped",
        order=1,
    ),
    TrustPreset(
        preset_id="bounded_trusted_routine",
        name="Bounded trusted routine",
        description="Selected routines may run at bounded_trusted_real with checkpoints; no commit/send unless explicit.",
        max_authority_tier_id=AuthorityTierId.BOUNDED_TRUSTED_REAL.value,
        require_approval_for_real=True,
        allow_commit_send=False,
        allow_bounded_trusted_real=True,
        valid_scope_hint="project/pack/workflow/recurring_routine",
        order=2,
    ),
    TrustPreset(
        preset_id="release_safe",
        name="Release-safe",
        description="Strict for release: no commit_or_send in production path; audit required for real execution.",
        max_authority_tier_id=AuthorityTierId.BOUNDED_TRUSTED_REAL.value,
        require_approval_for_real=True,
        allow_commit_send=False,
        allow_bounded_trusted_real=True,
        valid_scope_hint="project/pack; no global commit/send",
        order=3,
    ),
]


def get_preset(preset_id: str) -> TrustPreset | None:
    """Return built-in trust preset by id."""
    for p in BUILTIN_PRESETS:
        if p.preset_id == preset_id:
            return p
    return None


def list_presets() -> list[TrustPreset]:
    """Return all built-in presets in order."""
    return list(BUILTIN_PRESETS)


def tier_order(tier_id: str) -> int:
    """Order of tier (0=lowest authority). -1 if unknown."""
    tiers = list_tiers()
    for t in tiers:
        if t.tier_id == tier_id:
            return t.order
    return -1


def preset_allows_tier(preset: TrustPreset, tier_id: str) -> bool:
    """True if preset's max_authority_tier_id allows this tier (tier order <= max order)."""
    max_order = tier_order(preset.max_authority_tier_id)
    t_order = tier_order(tier_id)
    if t_order < 0 or max_order < 0:
        return False
    return t_order <= max_order
