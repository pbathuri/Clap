"""
Finder adapter: open approved folder in Finder (macOS).
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FinderOpenResult:
    success: bool
    path: str
    error: str = ""


def run_open_folder(path: str) -> FinderOpenResult:
    path_obj = Path(path).expanduser()
    if not path_obj.exists() or not path_obj.is_dir():
        return FinderOpenResult(success=False, path=str(path_obj), error="path_not_found")

    if os.environ.get("WORKFLOW_DATASET_FINDER_DRY_RUN"):
        return FinderOpenResult(success=True, path=str(path_obj))

    cmd = [
        "/usr/bin/osascript",
        "-e",
        f'tell application "Finder" to open POSIX file "{path_obj}"',
        "-e",
        'tell application "Finder" to activate',
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return FinderOpenResult(success=True, path=str(path_obj))
    except Exception as e:
        return FinderOpenResult(success=False, path=str(path_obj), error=str(e))
