"""
M21T/B3: Handoff profiles for publishable package (internal_team, stakeholder, operator_archive).
Used by package_builder to filter artifacts and build profile-specific summary/readme. Local-only.
"""

from __future__ import annotations

from typing import Any

VALID_PROFILES = frozenset({"internal_team", "stakeholder", "operator_archive"})

# Artifact names allowed in stakeholder-facing package (external handoff). Others are internal-only.
STAKEHOLDER_SAFE_ARTIFACTS = frozenset({
    "weekly_status.md",
    "stakeholder_update.md",
    "status_brief.md",
    "meeting_brief.md",
    "decision_requests.md",
})

_PROFILES: dict[str, dict[str, Any]] = {
    "internal_team": {
        "name": "internal_team",
        "label": "Internal team",
        "description": "All approved artifacts; full set for internal use.",
    },
    "stakeholder": {
        "name": "stakeholder",
        "label": "Stakeholder",
        "description": "Stakeholder-facing artifacts only (weekly_status, stakeholder_update, status_brief, etc.).",
    },
    "operator_archive": {
        "name": "operator_archive",
        "label": "Operator archive",
        "description": "Full approved set for audit/archive.",
    },
}


def get_profile(profile: str) -> dict[str, Any]:
    """Return profile dict by name. Raises ValueError for unknown profile."""
    p = profile.strip().lower() if profile else ""
    if p not in VALID_PROFILES:
        raise ValueError(f"Unknown handoff profile: {p!r}. Valid: {sorted(VALID_PROFILES)}")
    return dict(_PROFILES[p])


def filter_artifacts_for_profile(approved: list[str], profile: str) -> list[str]:
    """
    Return approved artifacts included for this profile.
    internal_team / operator_archive: all approved.
    stakeholder: only artifacts in STAKEHOLDER_SAFE_ARTIFACTS.
    """
    p = profile.strip().lower() if profile else ""
    if p not in VALID_PROFILES:
        raise ValueError(f"Unknown handoff profile: {p!r}. Valid: {sorted(VALID_PROFILES)}")
    if p == "stakeholder":
        return [a for a in approved if a in STAKEHOLDER_SAFE_ARTIFACTS]
    return list(approved)


def build_approved_summary_lines(
    profile_dict: dict[str, Any],
    run_id: str,
    workflow: str,
    grounding: str,
    copied: list[str],
    created_utc: str,
) -> list[str]:
    """Build lines for approved_summary.md for a given profile."""
    name = profile_dict.get("name") or "default"
    label = profile_dict.get("label") or name
    if name == "internal_team":
        title = "Approved summary (internal team)"
    elif name == "stakeholder":
        title = "Approved summary (stakeholder)"
    elif name == "operator_archive":
        title = "Approved summary (operator archive)"
    else:
        title = f"Approved summary ({label})"
    return [
        f"# {title}",
        "",
        f"Package built from workspace: `{run_id}`",
        f"Workflow: {workflow}",
        f"Grounding: {grounding}",
        "",
        "## Artifacts included",
        "",
        *[f"- {a}" for a in copied],
        "",
        f"Generated: {created_utc}",
    ]


def build_handoff_readme_lines(
    profile_dict: dict[str, Any],
    workflow: str,
    grounding: str,
    source_workspace: str,
    copied: list[str],
) -> list[str]:
    """Build lines for handoff_readme.md for a given profile."""
    return [
        "# Handoff readme",
        "",
        "This directory is a **publishable reporting package** built from the operator review queue.",
        "It contains only artifacts selected for this handoff profile.",
        "",
        "## Contents",
        "",
        f"- **Workflow:** {workflow}",
        f"- **Grounding:** {grounding}",
        f"- **Source workspace:** `{source_workspace}`",
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


def list_profiles() -> list[dict[str, Any]]:
    """Return list of profile dicts (name, label, description) for CLI list-profiles."""
    return [
        {"name": p["name"], "label": p["label"], "description": p["description"]}
        for p in _PROFILES.values()
    ]
