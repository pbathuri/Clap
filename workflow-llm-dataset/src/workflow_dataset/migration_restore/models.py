"""
M49E–M49H Phase A: Migration/restore model.
Target environment profile, restore candidate, restore validation report,
reconcile action, conflict class, stale-state note, rebuild-required component,
restore confidence, restore blocker; continuity bundle manifest.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConflictClass(str, Enum):
    """Kind of conflict when reconciling restored state with target."""
    PARTIAL = "partial"       # only some subsystems restored
    STALE = "stale"           # restored state older than target
    CONFLICTING = "conflicting"  # target has newer/different state
    UNSUPPORTED = "unsupported"  # target cannot accept this component
    MISSING_BACKEND = "missing_backend"  # required runtime/backend missing on target


@dataclass
class ContinuityBundleManifest:
    """Minimal manifest for a portable continuity bundle (subsystem paths + version)."""
    bundle_id: str = ""
    created_at_utc: str = ""
    product_version: str = ""
    subsystem_ids: list[str] = field(default_factory=list)
    paths_in_bundle: list[str] = field(default_factory=list)
    source_repo_root: str = ""
    local_only_excluded: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "created_at_utc": self.created_at_utc,
            "product_version": self.product_version,
            "subsystem_ids": list(self.subsystem_ids),
            "paths_in_bundle": list(self.paths_in_bundle),
            "source_repo_root": self.source_repo_root,
            "local_only_excluded": list(self.local_only_excluded),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ContinuityBundleManifest":
        return cls(
            bundle_id=d.get("bundle_id", ""),
            created_at_utc=d.get("created_at_utc", ""),
            product_version=d.get("product_version", ""),
            subsystem_ids=list(d.get("subsystem_ids") or []),
            paths_in_bundle=list(d.get("paths_in_bundle") or []),
            source_repo_root=d.get("source_repo_root", ""),
            local_only_excluded=list(d.get("local_only_excluded") or []),
        )


@dataclass
class TargetEnvironmentProfile:
    """Profile of the target environment (paths, version, runtime) for validation."""
    profile_id: str = ""
    repo_root: str = ""
    product_version: str = ""
    runtime_id: str = ""   # e.g. local, python_venv
    trust_mode: str = ""   # e.g. enforce, audit
    experimental_components: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "repo_root": self.repo_root,
            "product_version": self.product_version,
            "runtime_id": self.runtime_id,
            "trust_mode": self.trust_mode,
            "experimental_components": list(self.experimental_components),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TargetEnvironmentProfile":
        return cls(
            profile_id=d.get("profile_id", ""),
            repo_root=d.get("repo_root", ""),
            product_version=d.get("product_version", ""),
            runtime_id=d.get("runtime_id", ""),
            trust_mode=d.get("trust_mode", ""),
            experimental_components=list(d.get("experimental_components") or []),
        )


@dataclass
class RestoreBlocker:
    """A reason restore cannot proceed or must be limited."""
    blocker_id: str = ""
    code: str = ""   # version_incompatible | runtime_missing | trust_incompatible | local_only_not_restorable | critical_corrupt
    detail: str = ""
    subsystem_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocker_id": self.blocker_id,
            "code": self.code,
            "detail": self.detail,
            "subsystem_id": self.subsystem_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RestoreBlocker":
        return cls(
            blocker_id=d.get("blocker_id", ""),
            code=d.get("code", ""),
            detail=d.get("detail", ""),
            subsystem_id=d.get("subsystem_id", ""),
        )


@dataclass
class RestoreConfidence:
    """Confidence score and label for a restore operation."""
    score: float = 0.0   # 0.0–1.0
    label: str = ""   # high | medium | low | blocked
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "label": self.label,
            "reasons": list(self.reasons),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RestoreConfidence":
        return cls(
            score=float(d.get("score", 0)),
            label=d.get("label", ""),
            reasons=list(d.get("reasons") or []),
        )


@dataclass
class RestoreValidationReport:
    """Result of validating a bundle against a target environment."""
    report_id: str = ""
    bundle_id: str = ""
    target_profile_id: str = ""
    passed: bool = False
    version_compatible: bool = True
    runtime_compatible: bool = True
    trust_compatible: bool = True
    blockers: list[RestoreBlocker] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    local_only_excluded: list[str] = field(default_factory=list)
    experimental_warnings: list[str] = field(default_factory=list)
    restore_confidence: RestoreConfidence | None = None
    generated_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "bundle_id": self.bundle_id,
            "target_profile_id": self.target_profile_id,
            "passed": self.passed,
            "version_compatible": self.version_compatible,
            "runtime_compatible": self.runtime_compatible,
            "trust_compatible": self.trust_compatible,
            "blockers": [b.to_dict() for b in self.blockers],
            "warnings": list(self.warnings),
            "local_only_excluded": list(self.local_only_excluded),
            "experimental_warnings": list(self.experimental_warnings),
            "restore_confidence": self.restore_confidence.to_dict() if self.restore_confidence else None,
            "generated_at_utc": self.generated_at_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RestoreValidationReport":
        rc = d.get("restore_confidence")
        return cls(
            report_id=d.get("report_id", ""),
            bundle_id=d.get("bundle_id", ""),
            target_profile_id=d.get("target_profile_id", ""),
            passed=bool(d.get("passed", False)),
            version_compatible=bool(d.get("version_compatible", True)),
            runtime_compatible=bool(d.get("runtime_compatible", True)),
            trust_compatible=bool(d.get("trust_compatible", True)),
            blockers=[RestoreBlocker.from_dict(x) for x in (d.get("blockers") or [])],
            warnings=list(d.get("warnings") or []),
            local_only_excluded=list(d.get("local_only_excluded") or []),
            experimental_warnings=list(d.get("experimental_warnings") or []),
            restore_confidence=RestoreConfidence.from_dict(rc) if rc else None,
            generated_at_utc=d.get("generated_at_utc", ""),
        )


@dataclass
class RestoreCandidate:
    """A candidate restore: bundle ref + target + validation report."""
    candidate_id: str = ""
    bundle_id: str = ""
    target_profile_id: str = ""
    validation_report: RestoreValidationReport | None = None
    status: str = ""   # pending | validated | dry_run_done | restored | failed
    created_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "bundle_id": self.bundle_id,
            "target_profile_id": self.target_profile_id,
            "validation_report": self.validation_report.to_dict() if self.validation_report else None,
            "status": self.status,
            "created_at_utc": self.created_at_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RestoreCandidate":
        vr = d.get("validation_report")
        return cls(
            candidate_id=d.get("candidate_id", ""),
            bundle_id=d.get("bundle_id", ""),
            target_profile_id=d.get("target_profile_id", ""),
            validation_report=RestoreValidationReport.from_dict(vr) if vr else None,
            status=d.get("status", ""),
            created_at_utc=d.get("created_at_utc", ""),
        )


@dataclass
class StaleStateNote:
    """Note that restored or target state is stale."""
    subsystem_id: str = ""
    path: str = ""
    last_write_utc: str = ""
    stale_threshold_hours: float = 24.0
    recommended_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "path": self.path,
            "last_write_utc": self.last_write_utc,
            "stale_threshold_hours": self.stale_threshold_hours,
            "recommended_action": self.recommended_action,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StaleStateNote":
        return cls(
            subsystem_id=d.get("subsystem_id", ""),
            path=d.get("path", ""),
            last_write_utc=d.get("last_write_utc", ""),
            stale_threshold_hours=float(d.get("stale_threshold_hours", 24)),
            recommended_action=d.get("recommended_action", ""),
        )


@dataclass
class RebuildRequiredComponent:
    """Component that cannot be restored; must be rebuilt on target."""
    subsystem_id: str = ""
    reason: str = ""
    suggested_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "reason": self.reason,
            "suggested_command": self.suggested_command,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RebuildRequiredComponent":
        return cls(
            subsystem_id=d.get("subsystem_id", ""),
            reason=d.get("reason", ""),
            suggested_command=d.get("suggested_command", ""),
        )


@dataclass
class ReconcileAction:
    """One suggested reconciliation action after restore."""
    action_id: str = ""
    kind: str = ""   # overwrite_target | skip_restored | rebuild_component | refresh_stale | resolve_conflict
    subsystem_id: str = ""
    description: str = ""
    safe_to_apply: bool = True
    requires_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "kind": self.kind,
            "subsystem_id": self.subsystem_id,
            "description": self.description,
            "safe_to_apply": self.safe_to_apply,
            "requires_review": self.requires_review,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ReconcileAction":
        return cls(
            action_id=d.get("action_id", ""),
            kind=d.get("kind", ""),
            subsystem_id=d.get("subsystem_id", ""),
            description=d.get("description", ""),
            safe_to_apply=bool(d.get("safe_to_apply", True)),
            requires_review=bool(d.get("requires_review", False)),
        )


# ----- M49H.1: Reconcile policies + restore playbooks -----


@dataclass
class ReconcilePolicy:
    """
    Policy for how to reconcile after restore: overwrite vs skip, rebuild handling, review requirements.
    E.g. conservative_restore, balanced_restore, production_safe_restore.
    """
    policy_id: str = ""
    name: str = ""
    description: str = ""
    overwrite_target_allowed: bool = False
    skip_restored_allowed: bool = True
    rebuild_required_action: str = "suggest_only"   # suggest_only | require_review | block_restore
    require_review_for_overwrite: bool = True
    production_safe: bool = False
    scope_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "overwrite_target_allowed": self.overwrite_target_allowed,
            "skip_restored_allowed": self.skip_restored_allowed,
            "rebuild_required_action": self.rebuild_required_action,
            "require_review_for_overwrite": self.require_review_for_overwrite,
            "production_safe": self.production_safe,
            "scope_note": self.scope_note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ReconcilePolicy":
        return cls(
            policy_id=d.get("policy_id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            overwrite_target_allowed=bool(d.get("overwrite_target_allowed", False)),
            skip_restored_allowed=bool(d.get("skip_restored_allowed", True)),
            rebuild_required_action=str(d.get("rebuild_required_action", "suggest_only")),
            require_review_for_overwrite=bool(d.get("require_review_for_overwrite", True)),
            production_safe=bool(d.get("production_safe", False)),
            scope_note=d.get("scope_note", ""),
        )


@dataclass
class RestorePlaybookStep:
    """One step in a restore playbook."""
    step_order: int = 0
    label: str = ""
    command_or_action: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_order": self.step_order,
            "label": self.label,
            "command_or_action": self.command_or_action,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RestorePlaybookStep":
        return cls(
            step_order=int(d.get("step_order", 0)),
            label=d.get("label", ""),
            command_or_action=d.get("command_or_action", ""),
            description=d.get("description", ""),
        )


@dataclass
class RestorePlaybook:
    """Playbook for a common migration/restore case: when to use, steps, suggested policy."""
    playbook_id: str = ""
    name: str = ""
    description: str = ""
    when_to_use: str = ""
    steps: list[RestorePlaybookStep] = field(default_factory=list)
    applicable_conflict_classes: list[str] = field(default_factory=list)
    suggested_policy_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "playbook_id": self.playbook_id,
            "name": self.name,
            "description": self.description,
            "when_to_use": self.when_to_use,
            "steps": [s.to_dict() for s in self.steps],
            "applicable_conflict_classes": list(self.applicable_conflict_classes),
            "suggested_policy_id": self.suggested_policy_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RestorePlaybook":
        return cls(
            playbook_id=d.get("playbook_id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            when_to_use=d.get("when_to_use", ""),
            steps=[RestorePlaybookStep.from_dict(x) for x in (d.get("steps") or [])],
            applicable_conflict_classes=list(d.get("applicable_conflict_classes") or []),
            suggested_policy_id=d.get("suggested_policy_id", ""),
        )
