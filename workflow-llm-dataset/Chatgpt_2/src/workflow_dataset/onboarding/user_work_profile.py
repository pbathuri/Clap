"""
M23U: User work profile — field, job family, task style, tools, risk posture, automation preference.
Explicit and editable; persisted under data/local/onboarding/. Local-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.onboarding.bootstrap_profile import DEFAULT_ONBOARDING_DIR


USER_WORK_PROFILE_FILENAME = "user_work_profile.yaml"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root().resolve()
    except Exception:
        return Path.cwd().resolve()


@dataclass
class UserWorkProfile:
    """Explicit user work profile for domain adaptation. All fields editable."""
    # Identity / vertical
    field: str = ""                    # e.g. operations, founder_ops, research
    vertical: str = ""                 # industry vertical if different from field
    job_family: str = ""               # e.g. office_admin, analyst, developer
    # Task style
    daily_task_style: str = ""         # e.g. document_heavy, meeting_driven, code_first
    important_apps_tools: list[str] = dataclass_field(default_factory=lambda: [])
    document_types: list[str] = dataclass_field(default_factory=lambda: [])
    communication_reporting_style: str = ""
    # Safety / automation
    risk_safety_posture: str = "conservative"  # conservative | moderate | high_automation
    preferred_automation_degree: str = "simulate_first"  # simulate_first | approval_gated | trusted_scope
    # Runtime
    hardware_runtime_constraints: list[str] = dataclass_field(default_factory=lambda: [])  # e.g. cpu_only, low_memory
    preferred_edge_tier: str = ""      # dev_full | local_standard | constrained_edge | minimal_eval
    # Metadata
    created_at: str = ""
    updated_at: str = ""
    notes: str = ""


def get_user_work_profile_path(repo_root: Path | str | None = None) -> Path:
    """Path to user work profile file. Does not create it."""
    root = _repo_root(repo_root)
    return root / DEFAULT_ONBOARDING_DIR / USER_WORK_PROFILE_FILENAME


def _to_dict(p: UserWorkProfile) -> dict[str, Any]:
    return {
        "field": p.field,
        "vertical": p.vertical,
        "job_family": p.job_family,
        "daily_task_style": p.daily_task_style,
        "important_apps_tools": p.important_apps_tools,
        "document_types": p.document_types,
        "communication_reporting_style": p.communication_reporting_style,
        "risk_safety_posture": p.risk_safety_posture,
        "preferred_automation_degree": p.preferred_automation_degree,
        "hardware_runtime_constraints": p.hardware_runtime_constraints,
        "preferred_edge_tier": p.preferred_edge_tier,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "notes": p.notes,
    }


def _from_dict(d: dict[str, Any]) -> UserWorkProfile:
    return UserWorkProfile(
        field=str(d.get("field", "")),
        vertical=str(d.get("vertical", "")),
        job_family=str(d.get("job_family", "")),
        daily_task_style=str(d.get("daily_task_style", "")),
        important_apps_tools=list(d.get("important_apps_tools") or []),
        document_types=list(d.get("document_types") or []),
        communication_reporting_style=str(d.get("communication_reporting_style", "")),
        risk_safety_posture=str(d.get("risk_safety_posture", "conservative")),
        preferred_automation_degree=str(d.get("preferred_automation_degree", "simulate_first")),
        hardware_runtime_constraints=list(d.get("hardware_runtime_constraints") or []),
        preferred_edge_tier=str(d.get("preferred_edge_tier", "")),
        created_at=str(d.get("created_at", "")),
        updated_at=str(d.get("updated_at", "")),
        notes=str(d.get("notes", "")),
    )


def build_default_user_work_profile(repo_root: Path | str | None = None) -> UserWorkProfile:
    """Build a default empty profile. Use load_user_work_profile to get existing or this for new."""
    root = _repo_root(repo_root)
    return UserWorkProfile(
        created_at=utc_now_iso(),
        updated_at=utc_now_iso(),
    )


def load_user_work_profile(repo_root: Path | str | None = None) -> UserWorkProfile | None:
    """Load user work profile from disk. Returns None if missing or invalid."""
    path = get_user_work_profile_path(repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) if yaml else __import__("json").loads(raw)
    except Exception:
        return None
    if not data or not isinstance(data, dict):
        return None
    return _from_dict(data)


def save_user_work_profile(profile: UserWorkProfile, repo_root: Path | str | None = None) -> Path:
    """Persist user work profile to data/local/onboarding/user_work_profile.yaml."""
    path = get_user_work_profile_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile.updated_at = utc_now_iso()
    if not profile.created_at:
        profile.created_at = profile.updated_at
    data = _to_dict(profile)
    if yaml:
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    else:
        import json
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def bootstrap_user_work_profile(
    repo_root: Path | str | None = None,
    field: str = "",
    job_family: str = "",
    **overrides: Any,
) -> UserWorkProfile:
    """
    Create or update user work profile: load existing or create default, apply overrides, save.
    Overrides can include any UserWorkProfile field (e.g. field=..., job_family=..., risk_safety_posture=...).
    """
    root = _repo_root(repo_root)
    existing = load_user_work_profile(root)
    if existing:
        profile = existing
    else:
        profile = build_default_user_work_profile(root)
    if field:
        profile.field = field
    if job_family:
        profile.job_family = job_family
    for k, v in overrides.items():
        if hasattr(profile, k):
            setattr(profile, k, v)
    save_user_work_profile(profile, root)
    return profile
