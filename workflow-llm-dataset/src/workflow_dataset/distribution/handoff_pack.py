"""
M24U.1: Supportable release bundle + handoff pack — install profile, readiness summary,
support bundle pointers, runbooks, first-value launch instructions, known limitations.
Makes product easier to hand off to first real user or internal operator.
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

HANDOFF_DIR = "data/local/distribution/handoff"
KNOWN_LIMITATIONS_STATIC = [
    "Local-only; no cloud deployment or telemetry.",
    "Simulate-first; real mode requires approvals and operator control.",
    "Macros/routines: run in simulate first; real mode requires approval registry.",
    "Corrections and propose-updates: operator review required before apply.",
]


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_handoff_pack(
    pack_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build handoff pack for pack_id: install profile, readiness summary,
    support bundle pointers, runbooks, first-value launch instructions, known limitations.
    """
    root = _repo_root(repo_root)
    try:
        from workflow_dataset.distribution.checklists import CHECKLIST_PACK_ALIASES
        actual_pack = CHECKLIST_PACK_ALIASES.get(pack_id, pack_id)
    except Exception:
        actual_pack = pack_id
    out: dict[str, Any] = {
        "pack_id": pack_id,
        "generated_at": utc_now_iso(),
        "repo_root": str(root),
        "install_profile": {},
        "readiness_summary": {},
        "support_bundle_pointers": [],
        "runbooks": [],
        "first_value_launch_instructions": [],
        "known_limitations": [],
    }

    # Install profile (field deployment profile)
    try:
        from workflow_dataset.distribution.install_profile import build_field_deployment_profile
        profile = build_field_deployment_profile(actual_pack, root)
        out["install_profile"] = {
            "pack_id": profile.pack_id,
            "pack_name": profile.pack_name,
            "runtime_prerequisites": profile.runtime_prerequisites,
            "pack_provisioning_prerequisites": profile.pack_provisioning_prerequisites,
            "trust_readiness_checks": profile.trust_readiness_checks,
            "first_value_run_command": profile.first_value_run_command,
            "first_value_run_notes": profile.first_value_run_notes,
        }
    except Exception:
        pass

    # Readiness summary
    try:
        from workflow_dataset.distribution.readiness import build_deploy_readiness
        out["readiness_summary"] = build_deploy_readiness(root)
    except Exception:
        pass

    # Support bundle pointers: latest support_bundle_* dir or how to generate
    rollout_dir = root / "data/local/rollout"
    if rollout_dir.exists():
        bundles = sorted(
            [p for p in rollout_dir.iterdir() if p.is_dir() and p.name.startswith("support_bundle_")],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if bundles:
            out["support_bundle_pointers"].append(str(bundles[0]))
        else:
            out["support_bundle_pointers"].append("Run: workflow-dataset rollout support-bundle")
    else:
        out["support_bundle_pointers"].append("Run: workflow-dataset rollout support-bundle")

    # Runbooks: ids and paths
    try:
        from workflow_dataset.rollout.runbooks import list_runbooks, get_runbook_path
        for rid in list_runbooks():
            path = get_runbook_path(rid, root)
            out["runbooks"].append({"id": rid, "path": str(path) if path else None})
    except Exception:
        out["runbooks"] = [{"id": "operator_runbooks", "path": None}, {"id": "recovery_escalation", "path": None}]

    # First-value launch instructions (from checklist commands + profile)
    try:
        from workflow_dataset.distribution.checklists import build_field_checklist
        checklist = build_field_checklist(actual_pack, root)
        out["first_value_launch_instructions"] = checklist.get("commands", [])
        if checklist.get("first_value_run_command"):
            out["first_value_launch_instructions"].insert(
                0,
                f"First-value run: {checklist['first_value_run_command']}",
            )
    except Exception:
        out["first_value_launch_instructions"] = [
            "workflow-dataset package install-check",
            "workflow-dataset package first-run",
            "workflow-dataset rollout launch --id founder_demo",
        ]

    # Known limitations: from package_readiness.experimental + static
    out["known_limitations"] = list(KNOWN_LIMITATIONS_STATIC)
    try:
        from workflow_dataset.package_readiness.summary import build_readiness_summary
        ready = build_readiness_summary(root)
        for e in ready.get("experimental") or []:
            if e and e not in out["known_limitations"]:
                out["known_limitations"].append(str(e))
    except Exception:
        pass

    return out


def write_handoff_pack(
    pack_id: str,
    repo_root: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> Path:
    """Write handoff pack to output_dir (default data/local/distribution/handoff/<pack_id>_<timestamp>). Returns path to directory."""
    root = _repo_root(repo_root)
    pack = build_handoff_pack(pack_id, root)
    ts = pack["generated_at"].replace(":", "-").replace(".", "-")[:19]
    default_out = root / HANDOFF_DIR / f"{pack_id}_{ts}"
    out_dir = Path(output_dir).resolve() if output_dir else default_out
    out_dir.mkdir(parents=True, exist_ok=True)

    # handoff_summary.json
    (out_dir / "handoff_summary.json").write_text(
        json.dumps(pack, indent=2),
        encoding="utf-8",
    )

    # HANDOFF_README.md
    readme = format_handoff_readme(pack)
    (out_dir / "HANDOFF_README.md").write_text(readme, encoding="utf-8")

    return out_dir


def format_handoff_readme(pack: dict[str, Any]) -> str:
    """Generate HANDOFF_README.md content from handoff pack dict."""
    lines = [
        "# Handoff pack — " + pack.get("pack_id", ""),
        "",
        "First-draft handoff for first real user or internal operator. Local-only.",
        "",
        "## Install profile",
        "",
    ]
    ip = pack.get("install_profile") or {}
    lines.append(f"- Pack: {ip.get('pack_id')} — {ip.get('pack_name')}")
    lines.append("- Runtime prerequisites: " + ", ".join(ip.get("runtime_prerequisites") or []))
    lines.append("- Pack provisioning: " + ", ".join(ip.get("pack_provisioning_prerequisites") or []))
    lines.append("- Trust/readiness: " + ", ".join(ip.get("trust_readiness_checks") or []))
    lines.append("- First-value run: " + (ip.get("first_value_run_command") or "—"))
    lines.append("")
    lines.append("## Readiness summary")
    rs = pack.get("readiness_summary") or {}
    lines.append(f"- {rs.get('summary', '—')}")
    lines.append("")
    lines.append("## Support bundle")
    for ptr in pack.get("support_bundle_pointers") or []:
        lines.append(f"- {ptr}")
    lines.append("")
    lines.append("## Runbooks")
    for rb in pack.get("runbooks") or []:
        lines.append(f"- {rb.get('id')}: {rb.get('path') or 'see workflow-dataset rollout runbooks show ' + rb.get('id', '')}")
    lines.append("")
    lines.append("## First-value launch instructions")
    for cmd in pack.get("first_value_launch_instructions") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    lines.append("## Known limitations")
    for lim in pack.get("known_limitations") or []:
        lines.append(f"- {lim}")
    lines.append("")
    lines.append("---")
    lines.append("Generated: " + pack.get("generated_at", ""))
    return "\n".join(lines)


def format_release_bundle_summary(pack: dict[str, Any] | None = None, pack_id: str = "", repo_root: Path | str | None = None) -> str:
    """One-page release bundle summary for handoff. If pack is None, builds handoff pack for pack_id."""
    if pack is None and pack_id:
        pack = build_handoff_pack(pack_id, repo_root)
    if not pack:
        pack = build_handoff_pack("founder_ops_starter", repo_root)
    lines = [
        "=== Release bundle summary (handoff) ===",
        "",
        f"Pack: {pack.get('pack_id')}  Generated: {pack.get('generated_at', '')}",
        "",
        "[Readiness] " + (pack.get("readiness_summary") or {}).get("summary", "—"),
        "",
        "[Support bundle] " + "; ".join(pack.get("support_bundle_pointers") or []),
        "",
        "[First-value] " + (pack.get("install_profile") or {}).get("first_value_run_command", "—"),
        "",
        "[Runbooks] " + ", ".join(r.get("id", "") for r in (pack.get("runbooks") or [])),
        "",
        "[Known limitations] " + str(len(pack.get("known_limitations") or [])) + " items (see HANDOFF_README.md).",
        "",
        "Full handoff: workflow-dataset deploy handoff-pack --pack " + pack.get("pack_id", "founder_ops_starter"),
    ]
    return "\n".join(lines)
