"""
M25L.1: Pack demo gallery + certified pack showcase — purpose, roles, first-value flow,
readiness/certification status, demo assets, recommended install path. Operator-facing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.packs.certification import run_certification, CERT_STATUS_CERTIFIABLE
from workflow_dataset.packs.scorecard import build_pack_scorecard


def _packs_dir(repo_root: Path | str | None, packs_dir: Path | str | None) -> Path:
    if packs_dir:
        return Path(packs_dir).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        root = Path(get_repo_root()).resolve()
    except Exception:
        root = Path.cwd().resolve()
    return root / "data/local/packs"


def build_gallery_entry(
    pack_id: str,
    packs_dir: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build a single gallery/showcase entry: purpose, roles_supported, first_value_flow,
    certification_status, demo_assets (paths if any), recommended_install_path.
    """
    root = _packs_dir(repo_root, packs_dir)
    pack_dir = root / pack_id
    manifest_path = pack_dir / "manifest.json"
    entry: dict[str, Any] = {
        "pack_id": pack_id,
        "name": "",
        "version": "",
        "purpose": "",
        "roles_supported": [],
        "first_value_flow": "",
        "certification_status": "unknown",
        "readiness": "unknown",
        "demo_assets": [],
        "recommended_install_path": f"workflow-dataset packs install {(pack_dir / 'manifest.json').resolve()}",
    }
    if not manifest_path.exists():
        entry["purpose"] = "(pack not found)"
        return entry
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        entry["purpose"] = "(invalid manifest)"
        return entry
    entry["name"] = (data.get("name") or pack_id).strip()
    entry["version"] = (data.get("version") or "").strip()
    entry["purpose"] = (data.get("description") or data.get("name") or pack_id).strip() or "(no description)"
    entry["roles_supported"] = data.get("role_tags") or []
    templates = list(set((data.get("templates") or []) + (data.get("workflow_templates") or [])))
    entry["first_value_flow"] = " → ".join(templates[:8]) if templates else "Add templates or workflow_templates"
    cert = run_certification(pack_id, packs_dir=root, repo_root=repo_root)
    entry["certification_status"] = cert.get("status", "unknown")
    sc = build_pack_scorecard(pack_id, packs_dir=root, repo_root=repo_root)
    entry["readiness"] = sc.get("acceptance_readiness", "unknown")
    # Demo assets: any files under demos/ or docs/ (screenshots, placeholders)
    for sub in ("demos", "docs"):
        d = pack_dir / sub
        if d.exists():
            for f in d.iterdir():
                if f.is_file() and f.suffix.lower() in (".md", ".png", ".jpg", ".jpeg", ".webp", ".txt"):
                    entry["demo_assets"].append(str(f.relative_to(pack_dir)))
    entry["recommended_install_path"] = f"workflow-dataset packs install {(pack_dir / 'manifest.json').resolve()}"
    return entry


def build_gallery(
    packs_dir: Path | str | None = None,
    repo_root: Path | str | None = None,
    certified_only: bool = False,
) -> list[dict[str, Any]]:
    """
    Build gallery of all packs that have a manifest (in packs_dir). If certified_only, include only certifiable.
    """
    root = _packs_dir(repo_root, packs_dir)
    entries: list[dict[str, Any]] = []
    if not root.exists():
        return entries
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        if not (d / "manifest.json").exists():
            continue
        pack_id = d.name
        if pack_id in ("registry",) or pack_id.startswith("."):
            continue
        entry = build_gallery_entry(pack_id, packs_dir=root, repo_root=repo_root)
        if certified_only and entry.get("certification_status") != CERT_STATUS_CERTIFIABLE:
            continue
        entries.append(entry)
    return entries


def format_showcase(
    pack_id: str,
    packs_dir: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> str:
    """Single certified pack showcase output: name, version, purpose, roles, first-value flow, status, demo assets, install path."""
    entry = build_gallery_entry(pack_id, packs_dir=packs_dir, repo_root=repo_root)
    name_ver = entry.get("name", "") or entry["pack_id"]
    if entry.get("version"):
        name_ver = name_ver + " " + entry["version"]
    lines = [
        "=== Certified pack showcase: " + entry["pack_id"] + " ===",
        "",
        "[Name] " + name_ver,
        "[Purpose] " + entry.get("purpose", "—"),
        "[Roles supported] " + ", ".join(entry.get("roles_supported") or []),
        "[First-value flow] " + entry.get("first_value_flow", "—"),
        "[Certification status] " + entry.get("certification_status", "—") + "  [Readiness] " + entry.get("readiness", "—"),
        "",
        "[Demo assets / screenshots] " + (", ".join(entry.get("demo_assets") or []) or "(none — add under demos/ or docs/)"),
        "",
        "[Recommended install]",
        "  " + entry.get("recommended_install_path", "—"),
    ]
    return "\n".join(lines)


def format_gallery_report(
    packs_dir: Path | str | None = None,
    repo_root: Path | str | None = None,
    certified_only: bool = False,
) -> str:
    """Gallery report: one block per pack (name, version, purpose, roles, first-value, status, demo assets, install path)."""
    entries = build_gallery(packs_dir=packs_dir, repo_root=repo_root, certified_only=certified_only)
    lines = ["=== Pack demo gallery" + (" (certified only)" if certified_only else "") + " ===", ""]
    for e in entries:
        name_ver = (e.get("name") or e.get("pack_id", "")) + ((" " + e.get("version", "")) if e.get("version") else "")
        lines.append("--- " + e.get("pack_id", "") + " ---  " + name_ver)
        lines.append("  Purpose: " + (e.get("purpose") or "—"))
        lines.append("  Roles: " + ", ".join(e.get("roles_supported") or []))
        lines.append("  First-value: " + (e.get("first_value_flow") or "—"))
        lines.append("  Certification: " + e.get("certification_status", "—") + "  Readiness: " + e.get("readiness", "—"))
        if e.get("demo_assets"):
            lines.append("  Demo assets: " + ", ".join(e["demo_assets"][:8]))
        lines.append("  Install: workflow-dataset packs install <path-to-manifest>")
        lines.append("")
    if not entries:
        lines.append("(no packs in gallery)")
    return "\n".join(lines)
