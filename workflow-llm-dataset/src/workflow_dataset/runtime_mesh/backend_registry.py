"""
M23T: Backend/runtime profile registry. Local vs optional remote; capability flags; status (available/configured/missing/unsupported).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Default path under repo (local-first)
DEFAULT_REGISTRY_DIR = "data/local/runtime"
BACKEND_PROFILES_FILENAME = "backend_profiles.json"


@dataclass
class BackendProfile:
    """Single backend/runtime profile."""

    backend_id: str
    backend_family: str  # e.g. ollama, repo_local, llama_cpp
    local: bool = True
    optional_remote: bool = False
    tool_calling: bool = False
    thinking_reasoning: bool = False
    vision: bool = False
    embedding: bool = False
    ocr: bool = False
    coding_agent_suitable: bool = False
    desktop_assistant_suitable: bool = False
    hardware_profile_requirements: list[str] = field(default_factory=list)  # e.g. ["gpu", "8gb_ram"]
    install_prerequisites: list[str] = field(default_factory=list)
    notes: str = ""
    risk_trust_notes: str = ""
    # Filled at runtime
    status: str = "unknown"  # available | configured | missing | unsupported


def _default_backend_profiles() -> list[dict[str, Any]]:
    """Built-in seed profiles: repo local path, Ollama, optional llama.cpp."""
    return [
        {
            "backend_id": "repo_local",
            "backend_family": "repo_local",
            "local": True,
            "optional_remote": False,
            "tool_calling": False,
            "thinking_reasoning": True,
            "vision": False,
            "embedding": False,
            "ocr": False,
            "coding_agent_suitable": True,
            "desktop_assistant_suitable": True,
            "hardware_profile_requirements": [],
            "install_prerequisites": ["configs/settings.yaml", "data/local/llm"],
            "notes": "Current repo local backend path (MLX/adapter runs).",
            "risk_trust_notes": "Local-only; no network.",
        },
        {
            "backend_id": "ollama",
            "backend_family": "ollama",
            "local": True,
            "optional_remote": False,
            "tool_calling": True,
            "thinking_reasoning": True,
            "vision": True,
            "embedding": True,
            "ocr": False,
            "coding_agent_suitable": True,
            "desktop_assistant_suitable": True,
            "hardware_profile_requirements": [],
            "install_prerequisites": ["Ollama installed and running (e.g. http://127.0.0.1:11434)"],
            "notes": "Ollama-backed local model execution. Optional; not mandatory.",
            "risk_trust_notes": "Local by default; no data sent unless user configures remote.",
        },
        {
            "backend_id": "llama_cpp",
            "backend_family": "llama_cpp",
            "local": True,
            "optional_remote": False,
            "tool_calling": False,
            "thinking_reasoning": True,
            "vision": False,
            "embedding": False,
            "ocr": False,
            "coding_agent_suitable": True,
            "desktop_assistant_suitable": True,
            "hardware_profile_requirements": [],
            "install_prerequisites": ["llama.cpp build; GGUF model path"],
            "notes": "Optional compatibility; not a rewrite anchor.",
            "risk_trust_notes": "Local-only when used.",
        },
    ]


def _detect_backend_status(profile: BackendProfile, repo_root: Path) -> str:
    """Set status: available, configured, missing, or unsupported."""
    if profile.backend_id == "repo_local":
        # Repo local: configured if key paths exist
        llm_runs = repo_root / "data/local/llm/runs"
        config = repo_root / "configs/settings.yaml"
        if config.exists() and llm_runs.parent.exists():
            return "configured"
        return "missing"
    if profile.backend_id == "ollama":
        # Ollama: optional; check if we could talk to it (we don't require it)
        try:
            import urllib.request
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as _:
                return "available"
        except Exception:
            return "missing"
    if profile.backend_id == "llama_cpp":
        # llama.cpp: unsupported until explicitly wired
        return "unsupported"
    return "missing"


def load_backend_registry(repo_root: Path | str | None = None) -> list[BackendProfile]:
    """Load backend profiles from data/local/runtime/backend_profiles.json or built-in seed."""
    root = _repo_root(repo_root)
    registry_dir = root / DEFAULT_REGISTRY_DIR
    path = registry_dir / BACKEND_PROFILES_FILENAME
    if path.exists() and path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            profiles_data = data.get("profiles", data) if isinstance(data, dict) else data
            if not isinstance(profiles_data, list):
                profiles_data = _default_backend_profiles()
        except Exception:
            profiles_data = _default_backend_profiles()
    else:
        profiles_data = _default_backend_profiles()

    out: list[BackendProfile] = []
    for p in profiles_data:
        if isinstance(p, dict):
            prof = BackendProfile(
                backend_id=str(p.get("backend_id", "")),
                backend_family=str(p.get("backend_family", p.get("backend_id", ""))),
                local=bool(p.get("local", True)),
                optional_remote=bool(p.get("optional_remote", False)),
                tool_calling=bool(p.get("tool_calling", False)),
                thinking_reasoning=bool(p.get("thinking_reasoning", False)),
                vision=bool(p.get("vision", False)),
                embedding=bool(p.get("embedding", False)),
                ocr=bool(p.get("ocr", False)),
                coding_agent_suitable=bool(p.get("coding_agent_suitable", False)),
                desktop_assistant_suitable=bool(p.get("desktop_assistant_suitable", False)),
                hardware_profile_requirements=list(p.get("hardware_profile_requirements", [])),
                install_prerequisites=list(p.get("install_prerequisites", [])),
                notes=str(p.get("notes", "")),
                risk_trust_notes=str(p.get("risk_trust_notes", "")),
            )
            prof.status = _detect_backend_status(prof, root)
            out.append(prof)
    return out


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return get_repo_root()
    except Exception:
        return Path.cwd()


def list_backend_profiles(repo_root: Path | str | None = None) -> list[BackendProfile]:
    """List all backend profiles with current status."""
    return load_backend_registry(repo_root)


def get_backend_profile(backend_id: str, repo_root: Path | str | None = None) -> BackendProfile | None:
    """Get a single backend profile by id."""
    for p in load_backend_registry(repo_root):
        if p.backend_id == backend_id:
            return p
    return None


def get_backend_status(backend_id: str, repo_root: Path | str | None = None) -> str:
    """Return status for backend: available, configured, missing, unsupported."""
    prof = get_backend_profile(backend_id, repo_root)
    return prof.status if prof else "unsupported"
