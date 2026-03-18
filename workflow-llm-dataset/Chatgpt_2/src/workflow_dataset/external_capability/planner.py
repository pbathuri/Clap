"""
M24A: Activation planner — given machine profile, user/domain, trust posture,
output recommended activations, blocked, not worth it, rejected by policy, prerequisites, resource estimate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.external_capability.registry import load_external_sources
from workflow_dataset.external_capability.policy import apply_rejection_policy
from workflow_dataset.external_capability.schema import ExternalCapabilitySource


@dataclass
class ActivationRecommendation:
    source_id: str
    reason: str
    estimated_resource: str = ""


@dataclass
class BlockedEntry:
    source_id: str
    reason: str
    code: str = ""


@dataclass
class PlannerResult:
    recommended: list[ActivationRecommendation] = field(default_factory=list)
    blocked: list[BlockedEntry] = field(default_factory=list)
    not_worth_it: list[BlockedEntry] = field(default_factory=list)
    rejected_by_policy: list[BlockedEntry] = field(default_factory=list)
    prerequisite_steps: list[str] = field(default_factory=list)
    resource_estimate: dict[str, Any] = field(default_factory=dict)


class ActivationPlanner:
    """
    Plans what external capabilities to recommend, block, or reject
    given machine profile, user/domain, and trust posture.
    """

    def __init__(
        self,
        repo_root: Path | str | None = None,
    ):
        self.repo_root = Path(repo_root).resolve() if repo_root else Path.cwd()
        self._sources: list[ExternalCapabilitySource] = []

    def _ensure_sources(self) -> list[ExternalCapabilitySource]:
        if not self._sources:
            self._sources = load_external_sources(self.repo_root)
        return self._sources

    def plan(
        self,
        machine_profile: dict[str, Any] | None = None,
        domain_pack_id: str | None = None,
        task_class: str | None = None,
        trust_posture: dict[str, Any] | None = None,
    ) -> PlannerResult:
        """
        Generate recommended activations, blocked, not_worth_it, rejected_by_policy,
        prerequisite_steps, and resource_estimate.
        """
        sources = self._ensure_sources()
        machine_profile = machine_profile or {}
        trust_posture = trust_posture or {}
        tier = machine_profile.get("tier") or (machine_profile.get("edge_profile") or {}).get("tier") or "local_standard"

        result = PlannerResult()
        resource_low = resource_medium = resource_high = 0

        for src in sources:
            allowed, reject_reason = apply_rejection_policy(
                src, machine_profile, trust_posture, domain_pack_id, task_class
            )
            if not allowed:
                result.rejected_by_policy.append(BlockedEntry(src.source_id, reject_reason or "policy", reject_reason))
                continue

            # Already enabled / available: recommend as "already active" or skip from "recommended"
            if src.enabled or src.activation_status in ("available", "configured"):
                result.recommended.append(ActivationRecommendation(
                    src.source_id, "already_available", src.estimated_resource or "medium"
                ))
            elif src.activation_status in ("missing", "not_installed"):
                # Recommend for activation if useful for domain/task
                if task_class and src.supported_task_classes and task_class not in src.supported_task_classes:
                    result.not_worth_it.append(BlockedEntry(
                        src.source_id, "not_useful_for_task", "not_useful_for_profile"
                    ))
                else:
                    result.recommended.append(ActivationRecommendation(
                        src.source_id, "recommended_activation", src.estimated_resource or "medium"
                    ))
                    result.prerequisite_steps.extend(src.install_prerequisites or [])
            else:
                result.recommended.append(ActivationRecommendation(
                    src.source_id, src.activation_status or "optional", src.estimated_resource or "medium"
                ))

            # Resource tally
            r = (src.estimated_resource or "").lower()
            if r == "low":
                resource_low += 1
            elif r == "high":
                resource_high += 1
            else:
                resource_medium += 1

        result.resource_estimate = {
            "low_count": resource_low,
            "medium_count": resource_medium,
            "high_count": resource_high,
            "tier": tier,
        }
        result.prerequisite_steps = list(dict.fromkeys(result.prerequisite_steps))

        return result


def plan_activations(
    repo_root: Path | str | None = None,
    machine_profile: dict[str, Any] | None = None,
    domain_pack_id: str | None = None,
    task_class: str | None = None,
    trust_posture: dict[str, Any] | None = None,
) -> PlannerResult:
    """
    Convenience: build planner and run plan with optional machine/domain/trust.
    If machine_profile/trust_posture not provided, builds from local_deployment and trust cockpit.
    """
    root = repo_root
    if root is None:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = get_repo_root()
        except Exception:
            root = Path.cwd()

    if machine_profile is None:
        try:
            from workflow_dataset.local_deployment.profile import build_local_deployment_profile
            dep = build_local_deployment_profile(repo_root=root)
            machine_profile = {
                "tier": dep.get("tier"),
                "edge_profile": dep.get("edge_profile", {}),
            }
        except Exception:
            machine_profile = {}

    if trust_posture is None:
        try:
            from workflow_dataset.trust.cockpit import build_trust_cockpit
            cockpit = build_trust_cockpit(root)
            trust_posture = {
                "safe_to_expand": cockpit.get("safe_to_expand", False),
                "approval_registry_exists": (cockpit.get("approval_readiness") or {}).get("registry_exists", False),
            }
        except Exception:
            trust_posture = {}

    planner = ActivationPlanner(repo_root=root)
    return planner.plan(
        machine_profile=machine_profile,
        domain_pack_id=domain_pack_id,
        task_class=task_class,
        trust_posture=trust_posture,
    )
