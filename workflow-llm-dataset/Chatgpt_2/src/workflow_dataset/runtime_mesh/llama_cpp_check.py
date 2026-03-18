"""
M23S: Optional llama.cpp compatibility check. Not mandatory; local-only; no hidden downloads.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd()


def llama_cpp_check(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Optional check: is llama.cpp available on this machine? No download; no mandatory use.
    Returns: available (bool), status (available|not_found|optional), path (if found), config_profile_path (optional).
    """
    root = _repo_root(repo_root)
    result: dict[str, Any] = {
        "available": False,
        "status": "not_found",
        "path": None,
        "config_profile_path": None,
        "message": "llama.cpp is optional; not required for this product.",
    }

    # 1. Env override (operator can set path to llama-cli or server)
    env_path = os.environ.get("LAMMACPP_PATH") or os.environ.get("LLAMA_CPP_PATH")
    if env_path and Path(env_path).exists():
        result["available"] = True
        result["status"] = "available"
        result["path"] = env_path
        result["message"] = f"Found via env: {env_path}"
        return result

    # 2. Common CLI names in PATH (no execution; just which)
    for name in ("llama-cli", "llama-cpp-cli", "main", "llama-server"):
        path = shutil.which(name)
        if path:
            result["available"] = True
            result["status"] = "available"
            result["path"] = path
            result["message"] = f"Found in PATH: {name} -> {path}"
            break
    if result["available"]:
        return result

    # 3. Optional config profile path (data/local/runtime/llama_cpp_profile.json) — existence only
    profile_path = root / "data/local/runtime/llama_cpp_profile.json"
    if profile_path.exists():
        result["config_profile_path"] = str(profile_path)
        result["message"] = "Config profile exists; llama.cpp binary not found in PATH or LAMMACPP_PATH."
    else:
        result["config_profile_path"] = str(profile_path)
        result["message"] = "llama.cpp is optional. Set LAMMACPP_PATH or install llama-cli in PATH; add llama_cpp_profile.json for config."

    result["status"] = "optional"
    return result


def format_llama_cpp_check_report(result: dict[str, Any]) -> str:
    """Human-readable llama.cpp check report."""
    lines = [
        "=== llama.cpp compatibility check (optional) ===",
        "",
        result.get("message", ""),
        "",
        f"Available: {result.get('available')}  Status: {result.get('status')}",
    ]
    if result.get("path"):
        lines.append(f"Path: {result['path']}")
    if result.get("config_profile_path"):
        lines.append(f"Config profile: {result['config_profile_path']}")
    lines.append("")
    lines.append("(Optional local runtime. Not mandatory; no download.)")
    return "\n".join(lines)
