"""
M30I–M30L: Operator handoff pack — artifacts list, summary, generated_at; references support bundle and release pack.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.release_readiness.readiness import build_release_readiness
from workflow_dataset.release_readiness.pack import build_user_release_pack
from workflow_dataset.release_readiness.supportability import build_supportability_report


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _now_iso() -> str:
    try:
        from workflow_dataset.utils.dates import utc_now_iso
        return utc_now_iso()
    except Exception:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


HANDOFF_PACK_DIR = "data/local/release_readiness"
HANDOFF_PACK_FILE = "handoff_pack.json"
HANDOFF_SUMMARY_FILE = "handoff_summary.md"


def build_handoff_pack(
    repo_root: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build operator handoff pack: readiness, user release pack summary, supportability summary,
    list of referenced artifacts (support bundle path, runbooks, etc.). Optionally write to output_dir.
    """
    root = _repo_root(repo_root)
    now = _now_iso()
    readiness = build_release_readiness(root)
    pack = build_user_release_pack(root)
    support = build_supportability_report(root)

    artifacts: list[str] = []
    # Support bundle: list latest dir in data/local/rollout if any
    rollout_dir = root / "data/local/rollout"
    if rollout_dir.exists():
        bundles = sorted([d for d in rollout_dir.iterdir() if d.is_dir() and d.name.startswith("support_bundle_")], key=lambda p: p.stat().st_mtime, reverse=True)
        if bundles:
            artifacts.append(str(bundles[0]))
        else:
            artifacts.append("(run workflow-dataset rollout support-bundle to generate)")
    else:
        artifacts.append("(run workflow-dataset rollout support-bundle to generate)")
    artifacts.append("docs/rollout/OPERATOR_RUNBOOKS.md")
    artifacts.append("docs/rollout/RECOVERY_ESCALATION.md")

    summary_lines = [
        "# Operator handoff pack",
        "",
        "Generated: " + now,
        "",
        "## Release readiness",
        "Status: " + readiness.status,
        "Blockers: " + str(len(readiness.blockers)),
        "Warnings: " + str(len(readiness.warnings)),
        "",
        "## Supported workflows",
        ", ".join(readiness.supported_scope.workflow_ids[:10]) or "(see pack)",
        "",
        "## Recommended next action",
        readiness.supportability.recommended_next_support_action,
        "",
        "## Guidance",
        readiness.supportability.guidance,
        "",
        "## Artifacts",
    ]
    for a in artifacts:
        summary_lines.append("- " + a)

    out: dict[str, Any] = {
        "generated_at": now,
        "readiness_status": readiness.status,
        "blocker_count": len(readiness.blockers),
        "warning_count": len(readiness.warnings),
        "supportability_guidance": readiness.supportability.guidance,
        "recommended_next_action": readiness.supportability.recommended_next_support_action,
        "artifacts": artifacts,
        "summary_md": "\n".join(summary_lines),
        "output_path": "",
        "artifact_count": len(artifacts),
    }

    if output_dir is not None:
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        pack_path = out_dir / HANDOFF_PACK_FILE
        pack_data = {k: v for k, v in out.items() if k != "summary_md"}
        pack_data["summary_md_preview"] = out["summary_md"][:500]
        pack_path.write_text(json.dumps(pack_data, indent=2), encoding="utf-8")
        summary_path = out_dir / HANDOFF_SUMMARY_FILE
        summary_path.write_text(out["summary_md"], encoding="utf-8")
        out["output_path"] = str(out_dir)
        out["artifact_count"] = len(artifacts) + 2  # + handoff_pack.json, handoff_summary.md

    return out


def get_handoff_pack_dir(repo_root: Path | str | None = None) -> Path:
    """Default directory for handoff pack output."""
    return _repo_root(repo_root) / HANDOFF_PACK_DIR


def load_latest_handoff_pack(repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load latest handoff pack from data/local/release_readiness if present."""
    root = _repo_root(repo_root)
    pack_dir = root / HANDOFF_PACK_DIR
    if not pack_dir.exists():
        return None
    pack_file = pack_dir / HANDOFF_PACK_FILE
    if not pack_file.exists():
        return None
    try:
        return json.loads(pack_file.read_text(encoding="utf-8"))
    except Exception:
        return None
