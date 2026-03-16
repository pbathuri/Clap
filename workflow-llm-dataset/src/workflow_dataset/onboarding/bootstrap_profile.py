"""
M23N Phase 1: Local bootstrap profile. Machine identity, adapters, capabilities,
approval summary, trusted real-action subset, simulate-only areas, recommended job packs.
Persisted under data/local/onboarding/; local-only, no remote sync.
"""

from __future__ import annotations

import hashlib
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


DEFAULT_ONBOARDING_DIR = Path("data/local/onboarding")
BOOTSTRAP_PROFILE_FILENAME = "bootstrap_profile.yaml"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root().resolve()
    except Exception:
        return Path.cwd().resolve()


def _machine_id(repo_root: Path) -> str:
    """Stable local machine identity: hash of repo path + node name. No PII, no cloud."""
    raw = f"{repo_root!s}|{platform.node()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class BootstrapProfile:
    """Local bootstrap profile: machine, capabilities, approvals, trusted subset, simulate-only, recommended jobs."""
    machine_id: str = ""
    repo_root: str = ""
    created_at: str = ""
    # Adapters
    adapter_ids: list[str] = field(default_factory=list)
    adapters_available: list[dict[str, Any]] = field(default_factory=list)
    # Capabilities summary
    capabilities_summary: dict[str, Any] = field(default_factory=dict)
    # Approval status
    approval_registry_path: str = ""
    approval_registry_exists: bool = False
    approved_paths_count: int = 0
    approved_apps_count: int = 0
    approved_action_scopes_count: int = 0
    # Trusted real-action subset (from desktop_bench.trusted_actions)
    trusted_real_actions: list[dict[str, Any]] = field(default_factory=list)
    ready_for_real: bool = False
    # Simulate-only (adapters/actions that support only simulate)
    simulate_only_adapters: list[str] = field(default_factory=list)
    simulate_only_actions: list[dict[str, str]] = field(default_factory=list)
    # Recommended first job packs / routines
    recommended_job_packs: list[str] = field(default_factory=list)
    recommended_routines: list[str] = field(default_factory=list)
    # Edge readiness
    edge_ready: bool = False
    edge_checks_passed: int = 0
    edge_checks_total: int = 0
    # Setup (optional)
    setup_session_id: str = ""
    setup_stage: str = ""


def get_bootstrap_profile_path(repo_root: Path | str | None = None) -> Path:
    """Path to bootstrap profile file. Does not create it."""
    root = _repo_root(repo_root)
    return root / DEFAULT_ONBOARDING_DIR / BOOTSTRAP_PROFILE_FILENAME


def build_bootstrap_profile(
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
) -> BootstrapProfile:
    """
    Build bootstrap profile from capability discovery, approval registry,
    trusted actions, job packs report, edge checks. Read-only aggregation.
    """
    root = _repo_root(repo_root)
    try:
        from workflow_dataset.utils.dates import utc_now_iso
    except Exception:
        from datetime import datetime, timezone
        def utc_now_iso() -> str:
            return datetime.now(timezone.utc).isoformat()

    profile = BootstrapProfile(
        machine_id=_machine_id(root),
        repo_root=str(root),
        created_at=utc_now_iso(),
    )

    # Capability discovery
    try:
        from workflow_dataset.capability_discovery import run_scan
        cap = run_scan(repo_root=root)
        profile.adapter_ids = [a.adapter_id for a in cap.adapters_available]
        profile.adapters_available = [
            {
                "adapter_id": a.adapter_id,
                "adapter_type": a.adapter_type,
                "available": a.available,
                "supports_simulate": a.supports_simulate,
                "supports_real_execution": a.supports_real_execution,
                "action_count": a.action_count,
                "executable_action_ids": list(a.executable_action_ids),
            }
            for a in cap.adapters_available
        ]
        profile.capabilities_summary = {
            "adapters_count": len(cap.adapters_available),
            "approved_paths_count": len(cap.approved_paths),
            "approved_apps_count": len(cap.approved_apps),
            "action_scopes_count": len(cap.action_scopes),
        }
        # Simulate-only: adapters with supports_real_execution=False, and actions with executable=False
        profile.simulate_only_adapters = [
            a.adapter_id for a in cap.adapters_available
            if not a.supports_real_execution
        ]
        profile.simulate_only_actions = [
            {"adapter_id": s.adapter_id, "action_id": s.action_id}
            for s in cap.action_scopes
            if not s.executable
        ][:50]
    except Exception as e:
        profile.capabilities_summary["error"] = str(e)

    # Approval registry
    try:
        from workflow_dataset.capability_discovery.approval_registry import (
            get_registry_path,
            load_approval_registry,
        )
        reg_path = get_registry_path(root)
        profile.approval_registry_path = str(reg_path)
        profile.approval_registry_exists = reg_path.exists() and reg_path.is_file()
        if profile.approval_registry_exists:
            reg = load_approval_registry(root)
            profile.approved_paths_count = len(reg.approved_paths)
            profile.approved_apps_count = len(reg.approved_apps)
            profile.approved_action_scopes_count = len(reg.approved_action_scopes)
    except Exception:
        pass

    # Trusted real actions
    try:
        from workflow_dataset.desktop_bench.trusted_actions import get_trusted_real_actions
        trusted = get_trusted_real_actions(root)
        profile.trusted_real_actions = list(trusted.get("trusted_actions", []))
        profile.ready_for_real = trusted.get("ready_for_real", False)
    except Exception:
        pass

    # Job packs report: recommended first (trusted + recent or seed)
    try:
        from workflow_dataset.job_packs import list_job_packs, job_packs_report
        report = job_packs_report(root)
        profile.recommended_job_packs = list(report.get("trusted_for_real_jobs", []))[:10]
        if not profile.recommended_job_packs:
            profile.recommended_job_packs = list(report.get("recent_successful", []))[:5]
        ids = list_job_packs(root)
        if not profile.recommended_job_packs and ids:
            profile.recommended_job_packs = ids[:5]
    except Exception:
        pass

    # Copilot routines
    try:
        from workflow_dataset.copilot.routines import list_routines
        profile.recommended_routines = list_routines(root)[:5]
    except Exception:
        pass

    # Edge readiness
    try:
        from workflow_dataset.edge.checks import run_readiness_checks, checks_summary
        checks = run_readiness_checks(repo_root=root, config_path=config_path)
        summary = checks_summary(checks)
        profile.edge_ready = summary.get("ready", False)
        profile.edge_checks_passed = summary.get("passed", 0)
        profile.edge_checks_total = len(checks)
    except Exception:
        pass

    # Setup (latest session if any)
    try:
        from workflow_dataset.setup.job_store import load_session
        setup_dir = root / "data/local/setup"
        sessions_dir = setup_dir / "sessions"
        if sessions_dir.exists():
            latest = sorted(
                sessions_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if latest:
                sid = latest[0].stem
                session = load_session(setup_dir, sid)
                if session:
                    profile.setup_session_id = sid
                    profile.setup_stage = getattr(session.current_stage, "value", str(session.current_stage))
    except Exception:
        pass

    return profile


def save_bootstrap_profile(profile: BootstrapProfile, repo_root: Path | str | None = None) -> Path:
    """Persist bootstrap profile to data/local/onboarding/bootstrap_profile.yaml."""
    path = get_bootstrap_profile_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "machine_id": profile.machine_id,
        "repo_root": profile.repo_root,
        "created_at": profile.created_at,
        "adapter_ids": profile.adapter_ids,
        "adapters_available": profile.adapters_available,
        "capabilities_summary": profile.capabilities_summary,
        "approval_registry_path": profile.approval_registry_path,
        "approval_registry_exists": profile.approval_registry_exists,
        "approved_paths_count": profile.approved_paths_count,
        "approved_apps_count": profile.approved_apps_count,
        "approved_action_scopes_count": profile.approved_action_scopes_count,
        "trusted_real_actions": profile.trusted_real_actions,
        "ready_for_real": profile.ready_for_real,
        "simulate_only_adapters": profile.simulate_only_adapters,
        "simulate_only_actions": profile.simulate_only_actions[:30],
        "recommended_job_packs": profile.recommended_job_packs,
        "recommended_routines": profile.recommended_routines,
        "edge_ready": profile.edge_ready,
        "edge_checks_passed": profile.edge_checks_passed,
        "edge_checks_total": profile.edge_checks_total,
        "setup_session_id": profile.setup_session_id,
        "setup_stage": profile.setup_stage,
    }
    if yaml:
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    else:
        import json
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_bootstrap_profile(repo_root: Path | str | None = None) -> BootstrapProfile | None:
    """Load bootstrap profile from disk. Returns None if missing or invalid."""
    path = get_bootstrap_profile_path(repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) if yaml else __import__("json").loads(raw)
    except Exception:
        return None
    if not data or not isinstance(data, dict):
        return None
    return BootstrapProfile(
        machine_id=data.get("machine_id", ""),
        repo_root=data.get("repo_root", ""),
        created_at=data.get("created_at", ""),
        adapter_ids=list(data.get("adapter_ids") or []),
        adapters_available=list(data.get("adapters_available") or []),
        capabilities_summary=dict(data.get("capabilities_summary") or {}),
        approval_registry_path=data.get("approval_registry_path", ""),
        approval_registry_exists=bool(data.get("approval_registry_exists")),
        approved_paths_count=int(data.get("approved_paths_count", 0)),
        approved_apps_count=int(data.get("approved_apps_count", 0)),
        approved_action_scopes_count=int(data.get("approved_action_scopes_count", 0)),
        trusted_real_actions=list(data.get("trusted_real_actions") or []),
        ready_for_real=bool(data.get("ready_for_real")),
        simulate_only_adapters=list(data.get("simulate_only_adapters") or []),
        simulate_only_actions=[{k: str(v) for k, v in x.items()} for x in (data.get("simulate_only_actions") or []) if isinstance(x, dict)],
        recommended_job_packs=list(data.get("recommended_job_packs") or []),
        recommended_routines=list(data.get("recommended_routines") or []),
        edge_ready=bool(data.get("edge_ready")),
        edge_checks_passed=int(data.get("edge_checks_passed", 0)),
        edge_checks_total=int(data.get("edge_checks_total", 0)),
        setup_session_id=data.get("setup_session_id", ""),
        setup_stage=data.get("setup_stage", ""),
    )
