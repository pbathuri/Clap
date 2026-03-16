"""
M21T/B3: Build publishable package from approved artifacts in a reporting workspace.
Supports handoff profiles (internal_team, stakeholder, operator_archive).
Writes to data/local/packages/<ts_id>/. Does not apply outside sandbox.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.path_utils import get_repo_root
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

from workflow_dataset.release.reporting_workspaces import get_workspace_inventory
from workflow_dataset.release.review_state import get_approved_artifacts, load_review_state, save_review_state

PACKAGES_ROOT = "data/local/packages"


def build_package(
    workspace_path: str | Path,
    repo_root: Path | None = None,
    profile: str | None = None,
) -> Path:
    """
    Build a publishable package from approved artifacts in the workspace.
    If profile is set (internal_team | stakeholder | operator_archive), only profile-selected
    artifacts are included and summary/readme are profile-specific. Otherwise all approved
    artifacts are included with default summary/readme.
    Copies selected artifacts; adds package_manifest.json, approved_summary.md, handoff_readme.md.
    Updates review state with last_package_path. Returns package directory path.
    """
    ws = Path(workspace_path).resolve()
    if not ws.exists() or not ws.is_dir():
        raise FileNotFoundError(f"Workspace not found: {ws}")
    root = repo_root or get_repo_root()
    packages_root = root / PACKAGES_ROOT
    packages_root.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    pid = stable_id("pkg", str(ws), ts, prefix="")[:10]
    package_dir = packages_root / f"{ts}_{pid}"
    package_dir.mkdir(parents=True, exist_ok=True)

    approved = get_approved_artifacts(ws, repo_root=root)
    if not approved:
        raise ValueError("No approved artifacts; approve at least one artifact before building package")

    if profile:
        from workflow_dataset.release.handoff_profiles import (
            filter_artifacts_for_profile,
            get_profile,
            build_approved_summary_lines,
            build_handoff_readme_lines,
        )
        included = filter_artifacts_for_profile(approved, profile)
        if not included:
            raise ValueError(
                f"Profile '{profile}' excludes all approved artifacts. "
                "Approve at least one artifact that is included for this profile."
            )
        profile_dict = get_profile(profile)
    else:
        included = list(approved)
        profile_dict = None

    inv = get_workspace_inventory(ws)
    workflow = inv.get("workflow", "unknown") if inv else "unknown"
    grounding = (inv.get("grounding") or "unknown") if inv else "unknown"
    timestamp_src = (inv.get("timestamp") or utc_now_iso()) if inv else utc_now_iso()
    created_utc = utc_now_iso()

    copied: list[str] = []
    for name in included:
        src = ws / name
        if src.exists() and src.is_file():
            shutil.copy2(src, package_dir / name)
            copied.append(name)

    review = load_review_state(ws, repo_root=root)
    workspace_lane = review.get("lane") if review.get("lane") in ("operator", "reviewer", "stakeholder-prep", "approver") else None

    package_manifest: dict[str, Any] = {
        "package_type": "ops_reporting",
        "source_workspace": str(ws),
        "workflow": workflow,
        "grounding": grounding,
        "source_timestamp": timestamp_src,
        "created_utc": created_utc,
        "approved_artifacts": approved,
        "artifact_count": len(copied),
    }
    if inv and inv.get("manifest"):
        if inv["manifest"].get("template_id") is not None:
            package_manifest["template_id"] = inv["manifest"]["template_id"]
        if inv["manifest"].get("template_version") is not None:
            package_manifest["template_version"] = inv["manifest"]["template_version"]
    if workspace_lane:
        package_manifest["lane"] = workspace_lane
    if profile and profile_dict:
        package_manifest["handoff_profile"] = profile
        package_manifest["profile_included_artifacts"] = copied
    (package_dir / "package_manifest.json").write_text(
        json.dumps(package_manifest, indent=2), encoding="utf-8"
    )

    if profile and profile_dict:
        approved_summary_lines = build_approved_summary_lines(
            profile_dict, ws.name, workflow, grounding, copied, created_utc
        )
        handoff_lines = build_handoff_readme_lines(
            profile_dict, workflow, grounding, str(ws), copied
        )
    else:
        approved_summary_lines = [
            "# Approved summary",
            "",
            f"Package built from workspace: `{ws.name}`",
            f"Workflow: {workflow}",
            f"Grounding: {grounding}",
            "",
            "## Approved artifacts",
            "",
            *[f"- {a}" for a in copied],
            "",
            f"Generated: {created_utc}",
        ]
        handoff_lines = [
            "# Handoff readme",
            "",
            "This directory is a **publishable reporting package** built from the operator review queue.",
            "It contains only artifacts marked **approved** in the source workspace.",
            "",
            "## Contents",
            "",
            f"- **Workflow:** {workflow}",
            f"- **Grounding:** {grounding}",
            f"- **Source workspace:** `{ws}`",
            "",
            "## Artifacts included",
            "",
            *[f"- `{a}`" for a in copied],
            "",
            "## Apply to project",
            "",
            "To copy this package to a target directory (no automatic apply):",
            "",
            "  workflow-dataset assist apply-plan <this_package_dir> <target_path>",
            "  workflow-dataset assist apply <this_package_dir> <target_path> --confirm",
            "",
            "Apply requires explicit `--confirm`. No writes occur outside sandbox until you run apply.",
        ]
    (package_dir / "approved_summary.md").write_text("\n".join(approved_summary_lines), encoding="utf-8")
    (package_dir / "handoff_readme.md").write_text("\n".join(handoff_lines), encoding="utf-8")

    save_review_state(
        ws,
        review.get("artifacts") or {},
        last_package_path=str(package_dir),
        updated_at=utc_now_iso(),
        lane=workspace_lane,
        repo_root=root,
    )
    return package_dir
