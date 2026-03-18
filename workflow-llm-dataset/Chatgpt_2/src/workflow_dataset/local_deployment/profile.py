"""
M23R: Local deployment profile — reproducible snapshot of product state for local deploy. No cloud.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


DEPLOYMENT_DIR = "data/local/deployment"
PROFILE_FILENAME = "local_deployment_profile.json"
REPORT_FILENAME = "local_deployment_report.md"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_deployment_dir(repo_root: Path | str | None = None) -> Path:
    """Return path to deployment dir (data/local/deployment). Does not create it."""
    return _repo_root(repo_root) / DEPLOYMENT_DIR


def build_local_deployment_profile(
    repo_root: Path | str | None = None,
    config_path: str = "configs/settings.yaml",
    tier: str | None = None,
) -> dict[str, Any]:
    """
    Build a reproducible local deployment profile: edge profile, readiness summary,
    trust summary, product surfaces (jobs, routines, macros). Local-only; read-only snapshot.
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "version": "1",
        "generated_at": utc_now_iso(),
        "repo_root": str(root),
        "config_path": config_path,
        "tier": tier,
        "edge_profile": {},
        "readiness": {},
        "trust_summary": {},
        "product_surfaces": {},
        "errors": [],
    }

    # Edge profile (runtime, storage, sandbox paths)
    try:
        from workflow_dataset.edge.profile import build_edge_profile
        out["edge_profile"] = build_edge_profile(repo_root=root, config_path=config_path, tier=tier)
    except Exception as e:
        out["errors"].append(f"edge_profile: {e}")

    # Package readiness summary
    try:
        from workflow_dataset.package_readiness.summary import build_readiness_summary
        out["readiness"] = build_readiness_summary(repo_root=root)
    except Exception as e:
        out["errors"].append(f"readiness: {e}")

    # Trust cockpit summary (safe_to_expand, failed_gates count)
    try:
        from workflow_dataset.trust.cockpit import build_trust_cockpit
        cockpit = build_trust_cockpit(root)
        out["trust_summary"] = {
            "safe_to_expand": cockpit.get("safe_to_expand", False),
            "failed_gates_count": len(cockpit.get("failed_gates") or []),
            "benchmark_trust_status": (cockpit.get("benchmark_trust") or {}).get("latest_trust_status"),
            "approval_registry_exists": (cockpit.get("approval_readiness") or {}).get("registry_exists"),
        }
    except Exception as e:
        out["errors"].append(f"trust: {e}")
        out["trust_summary"] = {}

    # Product surfaces available on this machine
    try:
        from workflow_dataset.job_packs import list_job_packs
        from workflow_dataset.copilot.routines import list_routines
        from workflow_dataset.macros.runner import list_macros
        job_ids = list_job_packs(root)
        routine_ids = list_routines(root)
        macros_list = list_macros(root)
        out["product_surfaces"] = {
            "job_packs_count": len(job_ids),
            "job_pack_ids": job_ids[:50],
            "routines_count": len(routine_ids),
            "routine_ids": routine_ids[:30],
            "macros_count": len(macros_list),
            "macro_ids": [m.macro_id for m in macros_list][:30],
        }
    except Exception as e:
        out["errors"].append(f"product_surfaces: {e}")
        out["product_surfaces"] = {}

    return out


def write_deployment_profile(
    repo_root: Path | str | None = None,
    profile: dict[str, Any] | None = None,
    write_report_md: bool = True,
) -> Path:
    """
    Write deployment profile to data/local/deployment/local_deployment_profile.json.
    Optionally write local_deployment_report.md. Returns path to profile file.
    """
    root = _repo_root(repo_root)
    if profile is None:
        profile = build_local_deployment_profile(repo_root=root)
    deploy_dir = get_deployment_dir(root)
    deploy_dir.mkdir(parents=True, exist_ok=True)
    profile_path = deploy_dir / PROFILE_FILENAME
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    if write_report_md:
        report_path = deploy_dir / REPORT_FILENAME
        report_path.write_text(format_deployment_report(profile), encoding="utf-8")
    return profile_path


def format_deployment_report(profile: dict[str, Any]) -> str:
    """Human-readable deployment report (markdown)."""
    lines = [
        "# Local deployment profile",
        "",
        f"Generated: {profile.get('generated_at', '')}",
        f"Repo root: {profile.get('repo_root', '')}",
        "",
        "## Runtime",
        "",
    ]
    ep = profile.get("edge_profile") or {}
    rt = ep.get("runtime_requirements") or {}
    lines.append(f"- Python: {rt.get('python_version_current')} (min {rt.get('python_version_min')})")
    lines.append(f"- Config exists: {ep.get('config_exists')}")
    lines.append("")
    lines.append("## Readiness")
    r = profile.get("readiness") or {}
    mr = r.get("current_machine_readiness") or {}
    lines.append(f"- Machine ready: {mr.get('ready')}  passed: {mr.get('passed')}/{mr.get('total', 0)}")
    lines.append(f"- Ready for first real-user install: {r.get('ready_for_first_real_user_install')}")
    lines.append("")
    lines.append("## Trust summary")
    ts = profile.get("trust_summary") or {}
    lines.append(f"- Safe to expand: {ts.get('safe_to_expand')}  failed_gates: {ts.get('failed_gates_count', 0)}")
    lines.append(f"- Approval registry: {ts.get('approval_registry_exists')}")
    lines.append("")
    lines.append("## Product surfaces")
    ps = profile.get("product_surfaces") or {}
    lines.append(f"- Job packs: {ps.get('job_packs_count', 0)}  routines: {ps.get('routines_count', 0)}  macros: {ps.get('macros_count', 0)}")
    if profile.get("errors"):
        lines.append("")
        lines.append("## Errors")
        for e in profile["errors"][:10]:
            lines.append(f"- {e}")
    return "\n".join(lines)
