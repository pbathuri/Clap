"""
M22: Approved external-source references and optional wrappers. No blind integration.
Encode how external repos map into our runtime; document rejected/unsafe parts.
"""

from __future__ import annotations

from workflow_dataset.external_wrappers.openclaw_runtime_reference import REFERENCE as OPENCLAW_REFERENCE
from workflow_dataset.external_wrappers.worldmonitor_ui_reference import REFERENCE as WORLDMONITOR_REFERENCE
from workflow_dataset.external_wrappers.cliproxy_wrapper import REFERENCE as CLIPROXY_REFERENCE
from workflow_dataset.external_wrappers.mirofish_reference import REFERENCE as MIROFISH_REFERENCE

__all__ = [
    "OPENCLAW_REFERENCE",
    "WORLDMONITOR_REFERENCE",
    "CLIPROXY_REFERENCE",
    "MIROFISH_REFERENCE",
]
