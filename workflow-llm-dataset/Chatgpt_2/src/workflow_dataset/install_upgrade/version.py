"""
M30: Current installed version — read/write from data/local/install; read from pyproject/bundle.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.install_upgrade.models import ProductVersion, product_version_to_dict, product_version_from_dict

INSTALL_DIR = "data/local/install"
CURRENT_VERSION_FILE = "current_version.json"


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_install_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / INSTALL_DIR


def get_current_version_path(repo_root: Path | str | None = None) -> Path:
    return get_install_dir(repo_root) / CURRENT_VERSION_FILE


def read_current_version(repo_root: Path | str | None = None) -> ProductVersion | None:
    """Read current installed version from data/local/install/current_version.json. Returns None if not found."""
    path = get_current_version_path(repo_root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return product_version_from_dict(data)
    except Exception:
        return None


def write_current_version(
    pv: ProductVersion,
    repo_root: Path | str | None = None,
) -> Path:
    """Write current version to data/local/install/current_version.json."""
    root = _repo_root(repo_root)
    path = get_current_version_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(product_version_to_dict(pv), indent=2), encoding="utf-8")
    return path


def get_package_version_from_pyproject(repo_root: Path | str | None = None) -> str:
    """Read version from pyproject.toml in repo root. Returns 0.0.0 if not found."""
    root = _repo_root(repo_root)
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return "0.0.0"
    try:
        text = pyproject.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("version") and "=" in line:
                val = line.split("=", 1)[1].strip().strip('"\'')
                return val
    except Exception:
        pass
    return "0.0.0"


def get_current_version_display(repo_root: Path | str | None = None) -> tuple[str, str]:
    """Return (version_string, source). Prefer installed version file; fallback to pyproject."""
    pv = read_current_version(repo_root)
    if pv and pv.version:
        return pv.version, pv.source or "install"
    ver = get_package_version_from_pyproject(repo_root)
    return ver, "pyproject"
