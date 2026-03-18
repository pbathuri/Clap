"""
M22: World Monitor UI/dashboard reference. M21 adoption: reference_only.
Data organization and dashboard patterns; no import of external World Monitor code.
"""

from __future__ import annotations

REFERENCE = {
    "source_id": "worldmonitor",
    "adoption": "reference_only",
    "description": "Dashboard and data organization reference for operator console.",
    "runtime_mapping": {
        "ui_surfaces": "Console home/release/pilot views; we keep our existing TUI.",
        "data_organization": "Scope, readiness, evidence, recommendation structure (e.g. pilot report).",
    },
    "approved_patterns": [
        "Structured readiness reports (scope, ready/safe/degraded, evidence, recommendation).",
        "Clear separation of dashboard data from private runtime data.",
    ],
    "rejected_or_unsafe": [
        "No import of World Monitor code without explicit optional_wrapper approval.",
        "No cloud dashboard or external data push.",
    ],
}
