"""
M23A-F5: Example chain library — list and install bundled example chain definitions.
Examples live under chain_lab/examples/*.json; install copies to data/local/chain_lab/chains/.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

# Package-relative path to examples dir
_EXAMPLES_DIR = Path(__file__).resolve().parent / "examples"


def _examples_dir() -> Path:
    """Return path to bundled examples directory."""
    if _EXAMPLES_DIR.exists() and _EXAMPLES_DIR.is_dir():
        return _EXAMPLES_DIR
    return Path(__file__).resolve().parent / "examples"


def list_example_chains() -> list[dict[str, Any]]:
    """
    List bundled example chains (id, description, step_count).
    Returns list of {"id", "description", "step_count", "path"}.
    """
    examples_dir = _examples_dir()
    if not examples_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(examples_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            steps = data.get("steps") or []
            out.append({
                "id": data.get("id", p.stem),
                "description": (data.get("description") or "")[:200],
                "step_count": len(steps),
                "path": str(p),
            })
        except Exception:
            continue
    return out


def get_example_path(example_id: str) -> Path | None:
    """Return path to example JSON file for given id, or None if not found."""
    examples_dir = _examples_dir()
    if not examples_dir.exists():
        return None
    p = examples_dir / f"{example_id.strip()}.json"
    if p.exists() and p.is_file():
        return p
    for p in examples_dir.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if (data.get("id") or p.stem) == example_id.strip():
                return p
        except Exception:
            continue
    return None


def install_example(example_id: str, repo_root: Path | str | None = None) -> Path:
    """
    Copy an example chain into the chains directory. Overwrites if already present.
    Returns path to installed chain file.
    """
    from workflow_dataset.chain_lab.config import get_chains_dir
    src = get_example_path(example_id)
    if not src or not src.exists():
        raise FileNotFoundError(f"Example chain not found: {example_id}")
    chains_dir = get_chains_dir(repo_root)
    chains_dir.mkdir(parents=True, exist_ok=True)
    dest = chains_dir / src.name
    shutil.copy2(src, dest)
    return dest
