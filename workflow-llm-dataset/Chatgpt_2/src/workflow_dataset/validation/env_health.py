"""
M23W: Environment and dependency health — required/optional deps, no installs, operator-visible.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Required for core CLI and mission_control (from pyproject.toml)
REQUIRED_DEPS = ["pydantic", "typer", "rich", "yaml"]
# Optional for full suite (e.g. pandas, sqlalchemy for specific tests)
OPTIONAL_DEPS = ["pandas", "sqlalchemy", "rapidfuzz", "openpyxl", "xlsxwriter"]


def _import_ok(name: str) -> tuple[bool, str]:
    """Return (success, message)."""
    try:
        if name == "yaml":
            __import__("yaml")
        else:
            __import__(name)
        return True, "ok"
    except ImportError as e:
        return False, str(e)


def check_environment_health(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Check required/optional dependencies and Python version. No network; no installs.
    Returns: required_ok, optional_ok, python_version, required_deps[], optional_deps[], incubator_present.
    """
    out: dict[str, Any] = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "required_ok": True,
        "optional_ok": True,
        "required_deps": [],
        "optional_deps": [],
        "incubator_present": False,
    }
    for name in REQUIRED_DEPS:
        ok, msg = _import_ok(name)
        out["required_deps"].append({"name": name, "ok": ok, "message": msg})
        if not ok:
            out["required_ok"] = False
    for name in OPTIONAL_DEPS:
        ok, msg = _import_ok(name)
        out["optional_deps"].append({"name": name, "ok": ok, "message": msg})
        if not ok:
            out["optional_ok"] = False
    try:
        from workflow_dataset.incubator.registry import list_candidates
        _ = list_candidates  # ensure module loadable
        out["incubator_present"] = True
    except Exception:
        out["incubator_present"] = False
    return out


def format_health_report(health: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """Produce a plain-text health report for console or file."""
    if health is None:
        health = check_environment_health(repo_root)
    lines = [
        "=== Environment health (local) ===",
        "",
        f"Python: {health.get('python_version', '?')}",
        f"Required deps: {'ok' if health.get('required_ok') else 'MISSING'}",
    ]
    for d in health.get("required_deps", []):
        status = "ok" if d.get("ok") else "MISSING"
        lines.append(f"  {d.get('name', '?')}: {status}" + (f" — {d.get('message', '')}" if not d.get("ok") else ""))
    lines.append(f"Optional deps: {'all present' if health.get('optional_ok') else 'some missing (optional)'}")
    for d in health.get("optional_deps", []):
        status = "ok" if d.get("ok") else "missing"
        lines.append(f"  {d.get('name', '?')}: {status}")
    lines.append(f"Incubator: {'present' if health.get('incubator_present') else 'absent'}")
    lines.append("")
    lines.append("(No automatic installs. Install with: pip install -e .[dev] or per pyproject.toml)")
    return "\n".join(lines)
