"""
M22: CLIProxyAPI/Plus optional mediated proxy reference. M21 adoption: reference_only.
If ever promoted to optional_wrapper: gated proxy layer only; no arbitrary CLI execution.
"""

from __future__ import annotations

REFERENCE = {
    "source_id": "cliproxyapi_plus",
    "adoption": "reference_only",
    "description": "Optional mediated proxy layer reference for CLI/API bridging.",
    "runtime_mapping": {
        "proxy_layer": "Not in M22 runtime. Would be a gated, allow-listed proxy if adopted.",
    },
    "approved_patterns": [
        "Mediated proxy pattern (allow-list only; no arbitrary third-party execution).",
    ],
    "rejected_or_unsafe": [
        "No arbitrary CLI or script execution from packs or proxy.",
        "No import of CLIProxy code without explicit optional_wrapper approval.",
    ],
}
