"""
M23X: Operator quick reference — dashboard, profile, onboard, jobs, copilot, inbox, trust, runtime, mission-control.
Concise one-line purpose + key commands per surface. Local-only.
"""

from __future__ import annotations

from typing import Any

QUICK_REFERENCE_SECTIONS = [
    {
        "surface": "dashboard",
        "purpose": "Command center: workspaces, packages, cohort, apply-plan, next action.",
        "commands": ["workflow-dataset dashboard", "dashboard workspace", "dashboard package", "dashboard action"],
    },
    {
        "surface": "profile",
        "purpose": "User work profile and bootstrap: field, job family, operator summary.",
        "commands": ["workflow-dataset profile bootstrap", "profile show", "profile operator-summary"],
    },
    {
        "surface": "onboard",
        "purpose": "First-run onboarding: status, bootstrap profile, approval bootstrap (no auto-grant).",
        "commands": ["workflow-dataset onboard", "onboard status", "onboard bootstrap", "onboard approve"],
    },
    {
        "surface": "jobs",
        "purpose": "Job packs and specialization: list, run (simulate/real), report, diagnostics.",
        "commands": ["workflow-dataset jobs list", "jobs show --id <id>", "jobs run --id <id> --mode simulate", "jobs report"],
    },
    {
        "surface": "copilot",
        "purpose": "Recommendations, plan, run routine, reminders, explain-recommendation.",
        "commands": ["workflow-dataset copilot recommend", "copilot plan --job <id>", "copilot run --routine <id>", "copilot reminders"],
    },
    {
        "surface": "inbox",
        "purpose": "Daily digest: what changed, relevant jobs/routines, blocked, reminders, top next action.",
        "commands": ["workflow-dataset inbox", "inbox explain", "inbox snapshot", "inbox macros list", "inbox macros preview --id <id>"],
    },
    {
        "surface": "trust",
        "purpose": "Trust cockpit and release gates: benchmark trust, approvals, staged count.",
        "commands": ["workflow-dataset trust cockpit", "trust release-gates", "trust readiness-report"],
    },
    {
        "surface": "runtime",
        "purpose": "Runtime mesh: backends, catalog, integrations, recommend, profile, compatibility.",
        "commands": ["workflow-dataset runtime backends", "runtime catalog", "runtime recommend", "runtime profile", "runtime status"],
    },
    {
        "surface": "mission-control",
        "purpose": "Unified dashboard: product, eval, dev, inbox, trust, runtime; recommended next action.",
        "commands": ["workflow-dataset mission-control", "mission-control --output path"],
    },
]


def build_quick_reference() -> dict[str, Any]:
    """Build quick reference structure (list of sections with surface, purpose, commands)."""
    return {
        "sections": list(QUICK_REFERENCE_SECTIONS),
        "intro": "Operator quick reference (M23X). All commands under workflow-dataset. Local-only; no auto-run.",
    }


def format_quick_reference_text(ref: dict[str, Any] | None = None) -> str:
    """Format quick reference as plain text."""
    if ref is None:
        ref = build_quick_reference()
    lines = [ref.get("intro", "Operator quick reference"), ""]
    for s in ref.get("sections", []):
        lines.append(f"  {s['surface']}: {s['purpose']}")
        for c in s.get("commands", []):
            lines.append(f"    · {c}")
        lines.append("")
    return "\n".join(lines)


def format_quick_reference_md(ref: dict[str, Any] | None = None) -> str:
    """Format quick reference as markdown."""
    if ref is None:
        ref = build_quick_reference()
    lines = ["# Operator quick reference (M23X)", "", ref.get("intro", ""), ""]
    for s in ref.get("sections", []):
        lines.append(f"## {s['surface']}")
        lines.append("")
        lines.append(s["purpose"])
        lines.append("")
        for c in s.get("commands", []):
            lines.append(f"- `{c}`")
        lines.append("")
    return "\n".join(lines)
