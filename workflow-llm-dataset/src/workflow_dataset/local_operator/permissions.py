"""
Minimal capability checks for macOS local operator.
"""

from __future__ import annotations

from typing import Any
import shutil


def check_capabilities() -> list[dict[str, Any]]:
    """Return basic capability readiness checks (best-effort)."""
    checks: list[dict[str, Any]] = []
    checks.append({
        "capability_id": "automation",
        "ready": bool(shutil.which("osascript")),
        "notes": ["osascript present"] if shutil.which("osascript") else ["osascript missing"],
    })
    checks.append({
        "capability_id": "files_folders",
        "ready": True,
        "notes": ["approved folders gate file access"],
    })
    checks.append({
        "capability_id": "finder_open",
        "ready": bool(shutil.which("osascript")),
        "notes": ["Finder open requires macOS Automation permission when not using dry-run"],
    })
    checks.append({
        "capability_id": "accessibility",
        "ready": False,
        "notes": ["not yet verified in Phase 1"],
    })
    checks.append({
        "capability_id": "full_disk_access",
        "ready": False,
        "notes": ["not required for Phase 1"],
    })
    return checks
