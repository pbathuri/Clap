"""
M23Q: Trust cockpit data model. Read-only, advisory; no automatic trust state mutation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BenchmarkTrust:
    """Benchmark trust summary from desktop bench board."""
    latest_run_id: str | None = None
    latest_outcome: str | None = None
    latest_trust_status: str | None = None
    simulate_only_coverage: float = 0.0
    trusted_real_coverage: float = 0.0
    missing_approval_blockers: list[str] = field(default_factory=list)
    regressions: list[str] = field(default_factory=list)
    recommended_next_action: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> BenchmarkTrust:
        if not d:
            return cls()
        return cls(
            latest_run_id=d.get("latest_run_id"),
            latest_outcome=d.get("latest_outcome"),
            latest_trust_status=d.get("latest_trust_status"),
            simulate_only_coverage=float(d.get("simulate_only_coverage") or 0),
            trusted_real_coverage=float(d.get("trusted_real_coverage") or 0),
            missing_approval_blockers=list(d.get("missing_approval_blockers") or []),
            regressions=list(d.get("regressions") or []),
            recommended_next_action=str(d.get("recommended_next_action") or ""),
        )


@dataclass
class ApprovalReadiness:
    """Approval registry readiness."""
    registry_exists: bool = False
    registry_path: str = ""
    approved_paths_count: int = 0
    approved_action_scopes_count: int = 0

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> ApprovalReadiness:
        if not d:
            return cls()
        return cls(
            registry_exists=bool(d.get("registry_exists")),
            registry_path=str(d.get("registry_path") or ""),
            approved_paths_count=int(d.get("approved_paths_count") or 0),
            approved_action_scopes_count=int(d.get("approved_action_scopes_count") or 0),
        )


@dataclass
class JobMacroTrustState:
    """Job and macro (routine) trust state summary."""
    total_jobs: int = 0
    simulate_only_count: int = 0
    trusted_for_real_count: int = 0
    approval_blocked_count: int = 0
    recent_successful_count: int = 0
    routines_count: int = 0

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> JobMacroTrustState:
        if not d:
            return cls()
        return cls(
            total_jobs=int(d.get("total_jobs") or 0),
            simulate_only_count=int(d.get("simulate_only_count") or 0),
            trusted_for_real_count=int(d.get("trusted_for_real_count") or 0),
            approval_blocked_count=int(d.get("approval_blocked_count") or 0),
            recent_successful_count=int(d.get("recent_successful_count") or 0),
            routines_count=int(d.get("routines_count") or 0),
        )


@dataclass
class UnresolvedCorrections:
    """Unresolved corrections and review recommendations."""
    proposed_updates_count: int = 0
    review_recommended_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> UnresolvedCorrections:
        if not d:
            return cls()
        return cls(
            proposed_updates_count=int(d.get("proposed_updates_count") or 0),
            review_recommended_ids=list(d.get("review_recommended_ids") or []),
        )


@dataclass
class ReleaseGateStatus:
    """Release gate status (unreviewed, pending, staged, report)."""
    unreviewed_count: int = 0
    package_pending_count: int = 0
    staged_count: int = 0
    release_readiness_report_exists: bool = False

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> ReleaseGateStatus:
        if not d:
            return cls()
        return cls(
            unreviewed_count=int(d.get("unreviewed_count") or 0),
            package_pending_count=int(d.get("package_pending_count") or 0),
            staged_count=int(d.get("staged_count") or 0),
            release_readiness_report_exists=bool(d.get("release_readiness_report_exists")),
        )


@dataclass
class GateCheck:
    """Single release gate check result (advisory)."""
    gate_id: str
    name: str
    passed: bool
    message: str = ""


@dataclass
class TrustCockpit:
    """Full trust cockpit data model. Read-only snapshot."""
    benchmark_trust: BenchmarkTrust = field(default_factory=BenchmarkTrust)
    approval_readiness: ApprovalReadiness = field(default_factory=ApprovalReadiness)
    job_macro_trust_state: JobMacroTrustState = field(default_factory=JobMacroTrustState)
    unresolved_corrections: UnresolvedCorrections = field(default_factory=UnresolvedCorrections)
    release_gate_status: ReleaseGateStatus = field(default_factory=ReleaseGateStatus)
    errors: list[str] = field(default_factory=list)
    release_gate_checks: list[GateCheck] = field(default_factory=list)
    safe_to_expand: bool = False
    safe_to_expand_reasons: list[str] = field(default_factory=list)

    @classmethod
    def from_cockpit_dict(cls, d: dict[str, Any]) -> TrustCockpit:
        """Build schema from build_trust_cockpit() output."""
        out = cls(
            benchmark_trust=BenchmarkTrust.from_dict(d.get("benchmark_trust")),
            approval_readiness=ApprovalReadiness.from_dict(d.get("approval_readiness")),
            job_macro_trust_state=JobMacroTrustState.from_dict(d.get("job_macro_trust_state")),
            unresolved_corrections=UnresolvedCorrections.from_dict(d.get("unresolved_corrections")),
            release_gate_status=ReleaseGateStatus.from_dict(d.get("release_gate_status")),
            errors=list(d.get("errors") or []),
        )
        for gc in d.get("release_gate_checks") or []:
            if isinstance(gc, dict):
                out.release_gate_checks.append(GateCheck(
                    gate_id=gc.get("gate_id", ""),
                    name=gc.get("name", ""),
                    passed=bool(gc.get("passed")),
                    message=str(gc.get("message", "")),
                ))
        out.safe_to_expand = bool(d.get("safe_to_expand"))
        out.safe_to_expand_reasons = list(d.get("safe_to_expand_reasons") or [])
        return out
