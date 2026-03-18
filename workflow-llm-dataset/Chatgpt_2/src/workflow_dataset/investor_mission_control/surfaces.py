"""
M52F–M52G: Investor-facing copy for commands and vertical packs (no benchmark hero).
"""

from __future__ import annotations

_VERTICAL_FRIENDLY = {
    "founder_operator_core": "Founder & operations",
    "founder_operator": "Founder & operations",
}


def vertical_pack_display_name(pack_id: str) -> str:
    return _VERTICAL_FRIENDLY.get(pack_id, pack_id.replace("_", " ").title() if pack_id else "—")


def humanize_first_value_command(cmd: str) -> tuple[str, str, str]:
    """
    Map internal CLI to investor headline, why, what_next.
    """
    c = (cmd or "").strip()
    low = c.lower()
    if "workspace home" in low:
        return (
            "Open your workspace home",
            "Your calm command center for the day — priorities and surfaces in one place.",
            "You’ll see day context and suggested next steps without leaving this shell.",
        )
    if "progress board" in low:
        return (
            "Open your follow-up board",
            "See projects and recurring check-ins in one structured view.",
            "Skim what needs attention next; nothing runs without your go-ahead.",
        )
    if "day" in low and "preset" in low:
        return (
            "Align your day layout",
            "Match the shell to how you work today.",
            "Surfaces update to fit the selected day profile.",
        )
    return (
        "Take the recommended next step",
        "This command opens the highest-value surface for your current role.",
        "Explore; all sensitive actions stay approval-gated in demo mode.",
    )


def memory_headline(ready: bool, files: int, units: int) -> str:
    if ready and files > 0:
        return f"Sample workspace understood ({files} files → {units} memory notes)"
    if files > 0:
        return f"Partial scan: {files} sample files ingested"
    return "Memory bootstrap not complete yet"


def bounded_memory_note() -> str:
    return (
        "Bounded demo ingest: capped file count and size. Nothing leaves this machine. "
        "Heuristics only — not a full knowledge migration."
    )


def trust_investor_copy(simulate_first: bool, posture_label: str) -> tuple[str, str]:
    h = "You stay in control"
    if simulate_first:
        body = (
            f"{posture_label}: actions default to preview/simulation until you explicitly approve. "
            "No silent execution on this demo path."
        )
    else:
        body = f"{posture_label}. Approvals still apply for sensitive scopes."
    return h, body


def readiness_headline(capability: str) -> tuple[str, bool]:
    if capability == "full":
        return "This device is ready for the full investor demo path.", True
    if capability == "degraded":
        return "Demo-ready in lightweight mode (no heavy local model required).", True
    if capability == "blocked":
        return "Environment needs a quick fix before the full demo (see demo readiness).", False
    return "Run demo readiness to confirm this laptop.", False
