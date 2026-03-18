"""
M51H.1: Operator-facing guidance to stage a consistent first-run investor demonstration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.demo_onboarding.user_presets import DEMO_USER_PRESETS, DEFAULT_DEMO_USER_PRESET_ID
from workflow_dataset.demo_onboarding.workspace_packs import SAMPLE_WORKSPACE_PACKS


def build_operator_staging_guide(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Structured staging guide: pre-demo checklist, preset matrix, pack inventory, script outline.
    """
    try:
        if repo_root is not None:
            root = str(Path(repo_root).resolve())
        else:
            from workflow_dataset.path_utils import get_repo_root
            root = str(Path(get_repo_root()).resolve())
    except Exception:
        root = ""

    preset_rows = []
    for uid, up in DEMO_USER_PRESETS.items():
        preset_rows.append({
            "user_preset_id": uid,
            "label": up.label,
            "role_preset": up.role_preset_id,
            "workspace_pack": up.workspace_pack_id,
            "primary": uid == DEFAULT_DEMO_USER_PRESET_ID,
        })

    pack_rows = []
    for pid, pk in SAMPLE_WORKSPACE_PACKS.items():
        pack_rows.append({
            "pack_id": pid,
            "label": pk.label,
            "path_relative": pk.path_relative,
            "roles": pk.suggested_role_preset_ids,
        })

    return {
        "title": "Investor demo — first-run staging (M51H.1)",
        "repo_root_hint": root,
        "before_live_demo": [
            "Confirm USB image runs package first-run or equivalent install path.",
            "Pick one demo user preset (default: investor_demo_primary).",
            "Verify sample workspace pack exists on disk: demo onboarding workspace-pack path --id <pack_id>.",
            "Reset prior demo session so the story is clean: demo onboarding start --reset.",
            "Rehearse: user-preset → bootstrap-memory → ready-state in under 2 minutes.",
        ],
        "during_demo": [
            "Narrate: bounded sample only — no whole-laptop indexing.",
            "After ready-state, run the printed first-value command (e.g. workspace home).",
            "If asked about trust: simulate-first; onboard approve for real execution.",
        ],
        "after_demo": [
            "Optional: demo onboarding start --reset before next audience.",
        ],
        "demo_user_presets": preset_rows,
        "workspace_packs": pack_rows,
        "quick_script": [
            "workflow-dataset demo onboarding start --reset",
            "workflow-dataset demo onboarding user-preset --id investor_demo_primary",
            "workflow-dataset demo onboarding bootstrap-memory",
            "workflow-dataset demo onboarding ready-state",
        ],
    }


def format_staging_guide_text(guide: dict[str, Any] | None = None) -> str:
    if guide is None:
        guide = build_operator_staging_guide()
    lines = [guide["title"], "=" * len(guide["title"]), ""]
    lines.append("Before live demo")
    for x in guide.get("before_live_demo", []):
        lines.append(f"  • {x}")
    lines.append("")
    lines.append("During demo")
    for x in guide.get("during_demo", []):
        lines.append(f"  • {x}")
    lines.append("")
    lines.append("Demo user presets (role + workspace pack)")
    for r in guide.get("demo_user_presets", []):
        star = " *" if r.get("primary") else ""
        lines.append(f"  {r['user_preset_id']}{star}: {r['label']}")
        lines.append(f"      role={r['role_preset']}  pack={r['workspace_pack']}")
    lines.append("")
    lines.append("Workspace packs")
    for p in guide.get("workspace_packs", []):
        lines.append(f"  {p['pack_id']}: {p['label']}  → {p['path_relative']}")
    lines.append("")
    lines.append("Quick script")
    for c in guide.get("quick_script", []):
        lines.append(f"  {c}")
    return "\n".join(lines)
