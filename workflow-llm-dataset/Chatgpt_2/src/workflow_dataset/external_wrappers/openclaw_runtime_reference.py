"""
M22: OpenClaw runtime layer reference. M21 adoption: reference_only.
Maps OpenClaw concepts to our runtime layers; no import of external OpenClaw code.
"""

from __future__ import annotations

REFERENCE = {
    "source_id": "openclaw",
    "adoption": "reference_only",
    "description": "Local agent orchestration and layer model reference.",
    "runtime_mapping": {
        "channel_layer": "CLI / console entrypoints; no cloud channel binding by default.",
        "planner_layer": "Orchestration and routing; role-capability selection aligns with our planner.",
        "memory_layer": "Personal graph and retrieval; we keep local-first priors and corpora.",
        "tools_layer": "Parsers, generators, adapters; we use our own parse/output adapters.",
        "policy_layer": "Sandbox and apply gates; we preserve require_apply_confirm and sandbox_only.",
        "pack_layer": "Capability packs as installable units; we implement installer/resolver locally.",
    },
    "approved_patterns": [
        "Layered runtime (channel, planner, memory, tools, policy, pack).",
        "Local-first orchestration; no private data to cloud.",
        "Role/domain capability selection before execution.",
    ],
    "rejected_or_unsafe": [
        "No direct import of OpenClaw codebase without explicit optional_wrapper approval.",
        "No automatic sync or cloud orchestration from this reference.",
    ],
}
