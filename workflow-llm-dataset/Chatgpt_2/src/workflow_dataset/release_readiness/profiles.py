"""
M30L.1: Launch profiles — demo, internal pilot, careful first user, broader controlled pilot.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.release_readiness.models import LaunchProfile
from workflow_dataset.release_readiness.gates import (
    GATES,
    GATE_ENV_REQUIRED_OK,
    GATE_ACCEPTANCE_PASS,
    GATE_FIRST_USER_READY,
    GATE_RELEASE_READINESS_NOT_BLOCKED,
    GATE_ROLLOUT_STAGE_READY,
    GATE_TRUST_APPROVAL_READY,
    evaluate_gate,
)

# Profile IDs
PROFILE_DEMO = "demo"
PROFILE_INTERNAL_PILOT = "internal_pilot"
PROFILE_CAREFUL_FIRST_USER = "careful_first_user"
PROFILE_BROADER_CONTROLLED_PILOT = "broader_controlled_pilot"

# Registry: profile_id -> LaunchProfile
PROFILES: dict[str, LaunchProfile] = {
    PROFILE_DEMO: LaunchProfile(
        profile_id=PROFILE_DEMO,
        label="Demo",
        description="Controlled demo: rollout stage ready for trial and latest acceptance pass.",
        required_gate_ids=[GATE_ROLLOUT_STAGE_READY, GATE_ACCEPTANCE_PASS],
    ),
    PROFILE_INTERNAL_PILOT: LaunchProfile(
        profile_id=PROFILE_INTERNAL_PILOT,
        label="Internal pilot",
        description="Internal pilot: demo gates plus env required ok and no release blockers.",
        required_gate_ids=[
            GATE_ROLLOUT_STAGE_READY,
            GATE_ACCEPTANCE_PASS,
            GATE_ENV_REQUIRED_OK,
            GATE_RELEASE_READINESS_NOT_BLOCKED,
        ],
    ),
    PROFILE_CAREFUL_FIRST_USER: LaunchProfile(
        profile_id=PROFILE_CAREFUL_FIRST_USER,
        label="Careful first user",
        description="First real user: internal pilot plus first-user install ready and trust approval.",
        required_gate_ids=[
            GATE_ROLLOUT_STAGE_READY,
            GATE_ACCEPTANCE_PASS,
            GATE_ENV_REQUIRED_OK,
            GATE_RELEASE_READINESS_NOT_BLOCKED,
            GATE_FIRST_USER_READY,
            GATE_TRUST_APPROVAL_READY,
        ],
    ),
    PROFILE_BROADER_CONTROLLED_PILOT: LaunchProfile(
        profile_id=PROFILE_BROADER_CONTROLLED_PILOT,
        label="Broader controlled pilot",
        description="Broader pilot: same as careful first user (all gates).",
        required_gate_ids=[
            GATE_ROLLOUT_STAGE_READY,
            GATE_ACCEPTANCE_PASS,
            GATE_ENV_REQUIRED_OK,
            GATE_RELEASE_READINESS_NOT_BLOCKED,
            GATE_FIRST_USER_READY,
            GATE_TRUST_APPROVAL_READY,
        ],
    ),
}


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def evaluate_all_gates(repo_root: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Evaluate every gate once. Returns {gate_id: {passed, detail}}."""
    root = _repo_root(repo_root)
    return {gid: evaluate_gate(gid, root) for gid in GATES}


def is_profile_allowed(
    profile_id: str,
    gate_results: dict[str, dict[str, Any]] | None = None,
    repo_root: Path | str | None = None,
) -> tuple[bool, list[str], list[str]]:
    """
    Returns (allowed, gates_passed, gates_failed) for the given profile.
    If gate_results is None, evaluates all gates using repo_root.
    """
    profile = PROFILES.get(profile_id)
    if not profile:
        return False, [], [f"unknown profile: {profile_id}"]
    if gate_results is None:
        gate_results = evaluate_all_gates(repo_root)
    passed_ids = []
    failed_ids = []
    for gid in profile.required_gate_ids:
        r = gate_results.get(gid, {})
        if r.get("passed"):
            passed_ids.append(gid)
        else:
            failed_ids.append(gid)
    allowed = len(failed_ids) == 0
    return allowed, passed_ids, failed_ids


def build_launch_profiles_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Per-profile allowed status and gate results.
    """
    root = _repo_root(repo_root)
    gate_results = evaluate_all_gates(root)
    profiles_out: list[dict[str, Any]] = []
    for pid, profile in PROFILES.items():
        allowed, passed_ids, failed_ids = is_profile_allowed(pid, gate_results=gate_results)
        profiles_out.append({
            "profile_id": pid,
            "label": profile.label,
            "description": profile.description,
            "allowed": allowed,
            "required_gate_ids": list(profile.required_gate_ids),
            "gates_passed": passed_ids,
            "gates_failed": failed_ids,
        })
    return {
        "gate_results": gate_results,
        "profiles": profiles_out,
    }


def build_rollout_gate_report(
    repo_root: Path | str | None = None,
    profile_id: str | None = None,
) -> dict[str, Any]:
    """
    Rollout-gate report: all gates evaluated; if profile_id given, include
    only gates relevant to that profile and whether that profile is allowed.
    """
    root = _repo_root(repo_root)
    gate_results = evaluate_all_gates(root)
    out: dict[str, Any] = {
        "gates": {
            gid: {"passed": r["passed"], "detail": r["detail"]}
            for gid, r in gate_results.items()
        },
    }
    if profile_id:
        profile = PROFILES.get(profile_id)
        if profile:
            allowed, passed_ids, failed_ids = is_profile_allowed(profile_id, gate_results=gate_results)
            out["profile"] = {
                "profile_id": profile_id,
                "label": profile.label,
                "allowed": allowed,
                "gates_passed": passed_ids,
                "gates_failed": failed_ids,
                "gate_details": {
                    gid: gate_results.get(gid, {})
                    for gid in profile.required_gate_ids
                },
            }
        else:
            out["profile"] = {"error": f"unknown profile: {profile_id}"}
    else:
        out["profiles_summary"] = [
            {
                "profile_id": pid,
                "label": p.label,
                "allowed": is_profile_allowed(pid, gate_results=gate_results)[0],
            }
            for pid, p in PROFILES.items()
        ]
    return out


def format_launch_profiles_report(report: dict[str, Any]) -> str:
    """Human-readable launch profiles report."""
    lines = ["Launch profiles", "=" * 40]
    for p in report.get("profiles", []):
        status = "allowed" if p.get("allowed") else "not allowed"
        lines.append(f"\n{p.get('profile_id', '')} ({p.get('label', '')}): {status}")
        lines.append(f"  {p.get('description', '')}")
        if p.get("gates_failed"):
            lines.append(f"  Failed gates: {', '.join(p['gates_failed'])}")
    return "\n".join(lines)


def format_rollout_gate_report(report: dict[str, Any]) -> str:
    """Human-readable rollout-gate report."""
    lines = ["Rollout gates", "=" * 40]
    for gid, r in report.get("gates", {}).items():
        status = "pass" if r.get("passed") else "fail"
        lines.append(f"  {gid}: {status} — {r.get('detail', '')}")
    if "profile" in report:
        pr = report["profile"]
        if "error" in pr:
            lines.append(f"\nProfile: {pr['error']}")
        else:
            lines.append(f"\nProfile: {pr.get('profile_id')} ({pr.get('label')}) — allowed={pr.get('allowed')}")
            for gid, d in pr.get("gate_details", {}).items():
                lines.append(f"  {gid}: {'pass' if d.get('passed') else 'fail'} — {d.get('detail', '')}")
    if "profiles_summary" in report:
        lines.append("\nProfiles summary")
        for s in report["profiles_summary"]:
            lines.append(f"  {s.get('profile_id')}: allowed={s.get('allowed')}")
    return "\n".join(lines)


def list_profiles() -> list[dict[str, Any]]:
    """List all launch profiles."""
    return [p.to_dict() for p in PROFILES.values()]


def get_profile(profile_id: str) -> LaunchProfile | None:
    """Return LaunchProfile for profile_id or None."""
    return PROFILES.get(profile_id)
