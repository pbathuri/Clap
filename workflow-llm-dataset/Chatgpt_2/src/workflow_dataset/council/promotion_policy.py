"""
M41H.1: Promotion policies — rules tied to cohort and production-cut boundaries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.council.models import PromotionPolicy, PromotionPolicyRule


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


# Condition identifiers (align with safe_adaptation boundary)
CONDITION_AFFECTS_SUPPORTED_SURFACE = "affects_supported_surface"
CONDITION_AFFECTS_EXPERIMENTAL_ONLY = "affects_experimental_only"
CONDITION_CHANGES_TRUST_POSTURE = "changes_trust_posture"
CONDITION_HIGH_RISK = "high_risk"

OUTCOME_QUARANTINE = "quarantine"
OUTCOME_REJECT = "reject"
OUTCOME_LIMITED_ROLLOUT = "limited_rollout"
OUTCOME_EXPERIMENTAL_ONLY = "experimental_only"
OUTCOME_NO_OVERRIDE = "no_override"


def _default_policy() -> PromotionPolicy:
    """Default policy: clear rules for supported vs experimental, trust changes, high risk."""
    return PromotionPolicy(
        policy_id="default",
        label="Default promotion policy",
        cohort_id="",
        production_cut_id="",
        description="Boundary-based rules: supported surface and trust changes trigger quarantine or limited rollout.",
        rules=[
            PromotionPolicyRule(
                rule_id="trust_change",
                condition=CONDITION_CHANGES_TRUST_POSTURE,
                outcome=OUTCOME_QUARANTINE,
                reason="Changes trust posture; must be reviewed before promote.",
            ),
            PromotionPolicyRule(
                rule_id="high_risk_supported",
                condition=CONDITION_HIGH_RISK,
                outcome=OUTCOME_QUARANTINE,
                reason="High risk on supported surface; quarantine.",
            ),
            PromotionPolicyRule(
                rule_id="supported_surface",
                condition=CONDITION_AFFECTS_SUPPORTED_SURFACE,
                outcome=OUTCOME_LIMITED_ROLLOUT,
                reason="Affects supported surface; promote only in limited cohort until validated.",
            ),
            PromotionPolicyRule(
                rule_id="experimental_only",
                condition=CONDITION_AFFECTS_EXPERIMENTAL_ONLY,
                outcome=OUTCOME_EXPERIMENTAL_ONLY,
                reason="Affects only experimental surfaces; safe for experimental_only scope.",
            ),
        ],
    )


def get_effective_policy(
    cohort_id: str = "",
    production_cut_id: str = "",
    repo_root: Path | str | None = None,
) -> PromotionPolicy:
    """
    Return effective promotion policy for cohort and/or production cut.
    First-draft: returns default policy; later can load from data/local/council/policies/ by cohort/cut.
    """
    root = _repo_root(repo_root)
    # Optional: load cohort-specific or production_cut-specific policy from disk
    policy_path = root / "data/local/council/policies" / f"cohort_{cohort_id or 'default'}.json"
    if cohort_id and policy_path.exists():
        try:
            import json
            data = json.loads(policy_path.read_text(encoding="utf-8"))
            rules = [
                PromotionPolicyRule(
                    rule_id=r.get("rule_id", ""),
                    condition=r.get("condition", ""),
                    outcome=r.get("outcome", ""),
                    reason=r.get("reason", ""),
                )
                for r in data.get("rules", [])
            ]
            return PromotionPolicy(
                policy_id=data.get("policy_id", "custom"),
                label=data.get("label", "Custom"),
                cohort_id=data.get("cohort_id", cohort_id),
                production_cut_id=data.get("production_cut_id", ""),
                description=data.get("description", ""),
                rules=rules,
            )
        except Exception:
            pass
    return _default_policy()


def apply_policy_outcome(
    policy: PromotionPolicy,
    context: dict[str, Any],
) -> str | None:
    """
    Apply policy rules to context; return override outcome (quarantine, reject, limited_rollout, experimental_only) or None.
    context may include: affects_supported_surface, affects_experimental_only, changes_trust_posture, risk_level.
    """
    for rule in policy.rules:
        cond = rule.condition
        if cond == CONDITION_CHANGES_TRUST_POSTURE and context.get("changes_trust_posture"):
            return rule.outcome
        if cond == CONDITION_HIGH_RISK and context.get("risk_level") == "high" and context.get("affects_supported_surface"):
            return rule.outcome
        if cond == CONDITION_AFFECTS_SUPPORTED_SURFACE and context.get("affects_supported_surface") and not context.get("affects_experimental_only"):
            return rule.outcome
        if cond == CONDITION_AFFECTS_EXPERIMENTAL_ONLY and context.get("affects_experimental_only") and not context.get("affects_supported_surface"):
            return rule.outcome
    return None
