"""
M21W-F2: License and risk triage for devlab intake.
Surfaces: license visibility, dependency heaviness, use_as (inspiration vs direct_reuse), risky assumptions.
"""

from __future__ import annotations

import re
from typing import Any


def triage_license_risk(parsed: dict[str, Any]) -> dict[str, Any]:
    """
    Triage license and operational risk from parsed repo (readme_preview, license_note, deps).
    Returns: license_visible (bool), dependency_heaviness (light|medium|heavy),
    use_as (inspiration|direct_reuse|unclear), optional legal_operational_risk (low|medium|high).
    """
    readme = (parsed.get("readme_preview") or "").lower()
    license_note = (parsed.get("license_note") or parsed.get("license") or "").strip()
    deps = parsed.get("deps") or {}
    if isinstance(deps, dict):
        dep_files = list(deps.keys())
        dep_content = " ".join(str(v).lower() for v in deps.values() if v)
    else:
        dep_files = []
        dep_content = ""

    license_visible = bool(license_note and len(license_note) > 2)
    if not license_visible and ("license" in readme or "mit " in readme or "apache" in readme):
        license_visible = True

    # Dependency heaviness by file count and content size
    dep_count = len(dep_files) + (len(dep_content) // 100)
    if dep_count <= 5 and len(dep_content) < 500:
        dependency_heaviness = "light"
    elif dep_count <= 20 and len(dep_content) < 3000:
        dependency_heaviness = "medium"
    else:
        dependency_heaviness = "heavy"

    # use_as: inspiration_only vs reuse candidate
    use_as = "unclear"
    if license_visible:
        ln = license_note.lower()
        if "mit" in ln or "apache" in ln or "bsd" in ln:
            use_as = "direct_reuse"
        elif "gpl" in ln or "agpl" in ln:
            use_as = "inspiration"
    if "reference only" in readme or "inspiration" in readme or "do not use" in readme:
        use_as = "inspiration"
    if use_as == "unclear" and not license_visible:
        use_as = "inspiration"

    # Legal/operational risk
    legal_operational_risk = "unknown"
    if license_visible:
        ln = license_note.lower()
        if "mit" in ln or "apache" in ln or "bsd" in ln:
            legal_operational_risk = "low"
        elif "gpl" in ln or "agpl" in ln:
            legal_operational_risk = "medium"
        else:
            legal_operational_risk = "medium"

    return {
        "license_visible": license_visible,
        "dependency_heaviness": dependency_heaviness,
        "use_as": use_as,
        "legal_operational_risk": legal_operational_risk,
    }
